import sys
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')
from app import app
from flask_jwt_extended import create_access_token
from datetime import timedelta

with app.app_context():
    # Create a test admin token
    token = create_access_token(
        identity="1",
        additional_claims={'role': 'admin'},
        expires_delta=timedelta(days=1)
    )
    print("[TOKEN GENERATED]")
    print(token[:50] + "...")
    print("\nUse this in Authorization header: Bearer %s" % token)
