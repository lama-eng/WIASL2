import sys
import os
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')
os.chdir(r'c:\Users\Admin\Desktop\project10\backend')

from app import app
from extensions import db
from models.user import User

with app.app_context():
    try:
        # Find admin
        admin = User.query.filter_by(email='admin@example.com').first()
        
        if admin:
            print("✅ Found admin account")
            print(f"   Email: {admin.email}")
            print(f"   Role: {admin.role}")
            
            # Update password
            admin.set_password('admin123')
            db.session.commit()
            print("✅ Password updated to 'admin123'")
            
            # Verify password
            if admin.check_password('admin123'):
                print("✅ Password verified successfully!")
            else:
                print("❌ Password verification failed")
        else:
            print("❌ Admin account not found")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
