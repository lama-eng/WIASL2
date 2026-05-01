import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.user import User

ADMIN_EMAIL = "admin@wisal.com"
ADMIN_PASSWORD = "Admin@2026"
ADMIN_NAME = "Wisal Admin"

with app.app_context():
    db.create_all()

    existing = User.query.filter_by(email=ADMIN_EMAIL).first()
    if existing:
        existing.set_password(ADMIN_PASSWORD)
        existing.full_name = ADMIN_NAME
        existing.is_active = True
        db.session.commit()
        print(f"[OK] Admin account updated.")
    else:
        admin = User(
            email=ADMIN_EMAIL,
            full_name=ADMIN_NAME,
            role='admin',
            is_active=True,
            phone=''
        )
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"[OK] Admin account created.")

    print()
    print("=== Admin Credentials ===")
    print(f"  Email   : {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print("=========================")
