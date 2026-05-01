# backend/init_db.py
from app import app
from extensions import db
from models.user import User

def init_database():
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            print("✅ Database tables created")
            
            # Create default users
            users = [
                {
                    'email': 'admin@example.com',
                    'password': 'admin123',
                    'full_name': 'System Administrator',
                    'role': 'admin'
                },
                {
                    'email': 'donor@example.com',
                    'password': 'donor123',
                    'full_name': 'Test Donor',
                    'role': 'donor'
                },
                {
                    'email': 'beneficiary@example.com',
                    'password': 'benef123',
                    'full_name': 'Test Beneficiary',
                    'role': 'beneficiary'
                }
            ]
            
            for user_data in users:
                if not User.query.filter_by(email=user_data['email']).first():
                    user = User(
                        email=user_data['email'],
                        full_name=user_data['full_name'],
                        role=user_data['role'],
                        is_active=True
                    )
                    user.set_password(user_data['password'])
                    db.session.add(user)
                    print(f"✅ Created user: {user_data['email']}")
            
            db.session.commit()
            print("\n✅ Database initialized successfully!")
            print("\nTest Accounts:")
            print("   Admin: admin@example.com / admin123")
            print("   Donor: donor@example.com / donor123")
            print("   Beneficiary: beneficiary@example.com / benef123")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    init_database()