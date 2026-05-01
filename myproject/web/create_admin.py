import sys
import os
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')
os.chdir(r'c:\Users\Admin\Desktop\project10\backend')

from app import app
from extensions import db
from models.user import User

print(f"Current directory: {os.getcwd()}")
print(f"Database path: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

with app.app_context():
    try:
        # Create all tables
        db.create_all()
        print("✅ Database tables created/verified")
        
        # List all existing users
        users = User.query.all()
        print(f"Currently {len(users)} users in database")
        for u in users:
            print(f"  - {u.email} ({u.role})")
        
        # Check if admin exists
        existing_admin = User.query.filter_by(email='admin@example.com').first()
        if existing_admin:
            # Try verifying the password
            if existing_admin.check_password('admin123'):
                print("✅ Admin account exists with correct password!")
            else:
                print("⚠️ Admin account exists but password doesn't match - updating...")
                existing_admin.set_password('admin123')
                db.session.commit()
                print("✅ Password updated!")
        else:
            # Create admin
            admin = User(
                email='admin@example.com',
                full_name='System Administrator',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin account created successfully!")
        
        print("\n✅ Credentials ready:")
        print("Email: admin@example.com")
        print("Password: admin123")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
