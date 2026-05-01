/**
 * api.js
 * API client for the Face Verification Auth backend.
 * Handles token storage, authenticated requests, and user session.
 */

// Base URL – empty string means same origin (served by FastAPI)
const API_BASE = '';

// ── Token & user storage ─────────────────────────────────────────────────────
const Token = {
    save   : (t) => localStorage.setItem('faceauth_token', t),
    get    : ()  => localStorage.getItem('faceauth_token'),
    clear  : ()  => localStorage.removeItem('faceauth_token'),
    exists : ()  => Boolean(localStorage.getItem('faceauth_token')),
};

const UserCache = {
    save  : (u) => localStorage.setItem('faceauth_user', JSON.stringify(u)),
    get   : ()  => { try { return JSON.parse(localStorage.getItem('faceauth_user')); } catch { return null; } },
    clear : ()  => localStorage.removeItem('faceauth_user'),
};

// ── Core fetch wrapper ───────────────────────────────────────────────────────
/**
 * Make an authenticated fetch request.
 * Automatically attaches Bearer token if present.
 * Throws an Error with the server's detail message on non-2xx responses.
 */
async function apiFetch(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token   = Token.get();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(API_BASE + path, { ...options, headers });
    const data     = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || `Request failed (${response.status})`);
    }
    return data;
}

// ── Auth API calls ───────────────────────────────────────────────────────────

/**
 * Register a new user.
 * @param {string} username
 * @param {string} email
 * @param {string} password
 * @param {Blob}   faceBlob  JPEG image blob from the webcam
 */
async function registerUser(username, email, password, faceBlob) {
    const form = new FormData();
    form.append('username',   username);
    form.append('email',      email);
    form.append('password',   password);
    form.append('face_image', faceBlob, 'face.jpg');

    return apiFetch('/api/register', { method: 'POST', body: form });
}

/**
 * Login with username + password + face photo.
 * Saves the returned JWT token and user profile to localStorage.
 * @param {string} username
 * @param {string} password
 * @param {Blob}   faceBlob
 * @returns {Promise<object>}  Full login response including token + user info
 */
async function loginUser(username, password, faceBlob) {
    const form = new FormData();
    form.append('username',   username);
    form.append('password',   password);
    form.append('face_image', faceBlob, 'face.jpg');

    const data = await apiFetch('/api/login', { method: 'POST', body: form });
    Token.save(data.token);
    UserCache.save(data.user);
    return data;
}

/**
 * Fetch the current user's profile from the server.
 * Requires a valid token to be stored.
 */
async function getMe() {
    return apiFetch('/api/me');
}

/**
 * Log out the current user.
 * Calls the server logout endpoint, then clears local storage and redirects.
 */
async function logoutUser() {
    try {
        await apiFetch('/api/logout', { method: 'POST' });
    } catch (_) {
        // Ignore – we're logging out regardless
    }
    Token.clear();
    UserCache.clear();
    window.location.href = '/';
}

/**
 * Guard function: redirect to login if no token is stored.
 * Call this at the top of every protected page.
 */
function requireAuth() {
    if (!Token.exists()) {
        window.location.href = '/';
    }
}
