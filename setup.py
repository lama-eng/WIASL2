# backend/setup.py
import subprocess
import sys
import os

def setup_environment():
    """Setup complete environment for AI features"""
    
    print("🚀 Setting up Smart Donation Platform AI Environment...")
    print("=" * 50)
    
    # Get the backend directory path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Create __init__.py files if they don't exist
    init_dirs = ['routes', 'services', 'models', 'scripts']
    for dir_name in init_dirs:
        dir_path = os.path.join(backend_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        init_file = os.path.join(dir_path, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Auto-generated __init__.py\n')
            print(f"✅ Created {dir_name}/__init__.py")
    
    # Install dependencies
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
    except Exception as e:
        print(f"⚠️  Error installing dependencies: {e}")
    
    # Download spaCy model
    print("\n🔤 Downloading spaCy language model...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("✅ spaCy model downloaded")
    except:
        print("⚠️  Could not download spaCy model, will use fallback")
    
    # Download NLTK data
    print("\n📚 Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('stopwords', quiet=True)
        print("✅ NLTK data downloaded")
    except:
        print("⚠️  Could not download NLTK data")
    
    # Initialize database
    print("\n💾 Initializing database...")
    try:
        # Add the backend directory to Python path
        sys.path.insert(0, backend_dir)
        
        # Import app and models
        # Import create_app instead of app
        from app import create_app
        from extensions import db
        import models
        from models import User

        # Create flask app instance
        app = create_app()

      
        
        # Create database tables within app context
        with app.app_context():
            # Drop all tables and recreate (for clean setup)
            db.drop_all()
            db.create_all()
            print("✅ Database tables created")
            
            # Create default admin user
            admin = User.query.filter_by(email='admin@example.com').first()
            if not admin:
                admin = User(
                    email='admin@example.com',
                    full_name='System Administrator',
                    role='admin',
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # Create a test donor
                donor = User(
                    email='donor@example.com',
                    full_name='Test Donor',
                    role='donor',
                    is_active=True
                )
                donor.set_password('donor123')
                db.session.add(donor)
                
                # Create a test beneficiary
                benef = User(
                    email='beneficiary@example.com',
                    full_name='Test Beneficiary',
                    role='beneficiary',
                    is_active=True
                )
                benef.set_password('benef123')
                db.session.add(benef)
                
                db.session.commit()
                print("✅ Default users created:")
                print("   Admin: admin@example.com / admin123")
                print("   Donor: donor@example.com / donor123")
                print("   Beneficiary: beneficiary@example.com / benef123")
            else:
                print("✅ Default users already exist")
                
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete! 🎉")
    print("\nNext steps:")
    print("1. cd backend")
    print("2. python app.py")
    print("3. Open frontend/index.html in your browser")
    print("\nTest Accounts:")
    print("   Admin: admin@example.com / admin123")
    print("   Donor: donor@example.com / donor123")
    print("   Beneficiary: beneficiary@example.com / benef123")
    print("=" * 50)

if __name__ == "__main__":
    setup_environment()