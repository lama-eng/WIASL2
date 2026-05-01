import sys
import os
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')
os.chdir(r'c:\Users\Admin\Desktop\project10\backend')

from app import app
from extensions import db
from models.user import User, Donor, Beneficiary

with app.app_context():
    try:
        # Create tables
        db.create_all()
        print("✅ Database tables verified")
        
        # Create Donor Account
        donor_email = 'john.donor@example.com'
        if not User.query.filter_by(email=donor_email).first():
            donor_user = User(
                email=donor_email,
                full_name='John Donor',
                phone='+1-555-0101',
                role='donor',
                is_active=True,
                language='en'
            )
            donor_user.set_password('donor@123')
            db.session.add(donor_user)
            db.session.flush()
            
            # Create donor profile
            donor_profile = Donor(user_id=donor_user.id, total_donations=0)
            db.session.add(donor_profile)
            
            print("✅ Donor account created!")
            print(f"   Email: {donor_email}")
            print(f"   Password: donor@123")
        else:
            print("⚠️ Donor account already exists")
        
        # Create Beneficiary Account
        beneficiary_email = 'sarah.beneficiary@example.com'
        if not User.query.filter_by(email=beneficiary_email).first():
            beneficiary_user = User(
                email=beneficiary_email,
                full_name='Sarah Beneficiary',
                phone='+1-555-0102',
                role='beneficiary',
                is_active=True,
                language='en'
            )
            beneficiary_user.set_password('beneficiary@123')
            db.session.add(beneficiary_user)
            db.session.flush()
            
            # Create beneficiary profile
            beneficiary_profile = Beneficiary(
                user_id=beneficiary_user.id,
                income=8000.00,
                family_size=4,
                children_count=2,
                address='123 Main St, Springfield'
            )
            db.session.add(beneficiary_profile)
            
            print("✅ Beneficiary account created!")
            print(f"   Email: {beneficiary_email}")
            print(f"   Password: beneficiary@123")
        else:
            print("⚠️ Beneficiary account already exists")
        
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ Dummy Data Created Successfully!")
        print("="*50)
        print("\n📋 Account Credentials:")
        print("\n1️⃣  DONOR ACCOUNT:")
        print(f"   Email: {donor_email}")
        print(f"   Password: donor@123")
        print("\n2️⃣  BENEFICIARY ACCOUNT:")
        print(f"   Email: {beneficiary_email}")
        print(f"   Password: beneficiary@123")
        print("\n3️⃣  ADMIN ACCOUNT (from before):")
        print(f"   Email: admin@example.com")
        print(f"   Password: admin123")
        print("\n" + "="*50)
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
