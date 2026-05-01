import os
import io
import re
import json
import pickle
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from keras_facenet import FaceNet

from face_embedding import extract_face_embedding

# ── Config ─────────────────────────────────────────────────────────────────
# Set JWT_SECRET via environment variable in production!
JWT_SECRET    = os.environ.get("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_H  = 8

USER_DB_DIR = "userDatabase"
USERS_FILE  = os.path.join(USER_DB_DIR, "users.json")

# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(title="Face Verification Auth API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
_static_dir  = os.path.join(FRONTEND_DIR, "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Load FaceNet once at startup (expensive operation)
print("Loading FaceNet model...")
embedder = FaceNet()
security = HTTPBearer()
print("Model ready. API starting...")

# ── Storage helpers ─────────────────────────────────────────────────────────
def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, encoding="utf-8") as f:
        return json.load(f)

def _save_users(users: dict) -> None:
    os.makedirs(USER_DB_DIR, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def _img_from_bytes(data: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))

def _emb_path(username: str) -> str:
    return os.path.join(USER_DB_DIR, username, "embedding.pkl")

# ── JWT helpers ──────────────────────────────────────────────────────────────
def _create_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRE_H),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    payload = _decode_token(credentials.credentials)
    return payload["sub"]

# ── Page routes (serve HTML files) ──────────────────────────────────────────
@app.get("/", include_in_schema=False)
def index():
    p = os.path.join(FRONTEND_DIR, "login.html")
    return FileResponse(p) if os.path.exists(p) else {"running": True}

@app.get("/register", include_in_schema=False)
def register_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "register.html"))

@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

# ── API routes ───────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Utility"])
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/api/register", tags=["Auth"])
async def api_register(
    username:   str        = Form(...),
    email:      str        = Form(...),
    password:   str        = Form(...),
    face_image: UploadFile = File(...),
):
    """Register a new user: username + email + password + face photo."""
    # Input validation – username may be derived from an email address
    # (allowed chars: letters, numbers, underscores; length 3-60)
    if len(username) < 3 or len(username) > 60:
        raise HTTPException(400, "Username must be 3-60 characters.")
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise HTTPException(400, "Username can only contain letters, numbers, and underscores.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Invalid email address.")
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")

    users = _load_users()
    if username in users:
        raise HTTPException(400, "Username already taken.")
    if any(u.get("email") == email for u in users.values()):
        raise HTTPException(400, "Email already registered.")

    # Extract face embedding
    contents = await face_image.read()
    try:
        embedding = extract_face_embedding(_img_from_bytes(contents))
    except ValueError as exc:
        raise HTTPException(422, f"Face error: {exc}")

    # Hash password with bcrypt
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Persist embedding
    user_dir = os.path.join(USER_DB_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    with open(_emb_path(username), "wb") as f:
        pickle.dump(embedding, f)

    # Persist user record
    users[username] = {
        "email":      email,
        "password":   hashed_pw,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_users(users)

    return {"success": True, "message": "Account created successfully!"}


@app.post("/api/login", tags=["Auth"])
async def api_login(
    username:   str        = Form(...),
    password:   str        = Form(...),
    face_image: UploadFile = File(...),
):
    """
    Two-factor authentication:
      Factor 1 – Password (bcrypt)
      Factor 2 – Face biometrics (FaceNet cosine similarity)
    Returns a signed JWT on success.
    """
    users = _load_users()

    # Factor 1: password (use same error message to prevent username enumeration)
    if username not in users:
        raise HTTPException(401, "Invalid credentials.")
    if not bcrypt.checkpw(password.encode(), users[username]["password"].encode()):
        raise HTTPException(401, "Invalid credentials.")

    # Factor 2: face
    if not os.path.exists(_emb_path(username)):
        raise HTTPException(500, "Face data missing. Please contact support.")

    with open(_emb_path(username), "rb") as f:
        stored_emb = pickle.load(f)

    contents = await face_image.read()
    try:
        input_emb = extract_face_embedding(_img_from_bytes(contents))
    except ValueError as exc:
        raise HTTPException(422, f"Face error: {exc}")

    distance = embedder.compute_distance(stored_emb, input_emb)
    if distance >= 0.5:
        raise HTTPException(401, "Face verification failed. Please try again.")

    # Issue JWT
    token = _create_token(username)
    return {
        "success":    True,
        "token":      token,
        "token_type": "Bearer",
        "expires_in": JWT_EXPIRE_H * 3600,
        "user": {
            "username":   username,
            "email":      users[username]["email"],
            "created_at": users[username]["created_at"],
        },
    }


@app.get("/api/me", tags=["Auth"])
def api_me(current_user: str = Depends(get_current_user)):
    """Return the authenticated user's profile (requires Bearer token)."""
    users = _load_users()
    u = users.get(current_user)
    if not u:
        raise HTTPException(404, "User not found.")
    return {
        "username":   current_user,
        "email":      u["email"],
        "created_at": u["created_at"],
    }


@app.post("/api/logout", tags=["Auth"])
def api_logout(_: str = Depends(get_current_user)):
    """
    Stateless logout – client discards the token.
    For true revocation, add a server-side token denylist (Redis recommended).
    """
    return {"success": True, "message": "Logged out successfully."}


# ── Entry-point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
