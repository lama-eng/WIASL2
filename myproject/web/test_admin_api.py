import json
import sys
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')

from app import app

with app.test_client() as client:
    # Test login
    login_data = {
        'email': 'admin@example.com',
        'password': 'admin123'
    }
    
    print("=== Testing Admin Login ===")
    response = client.post('/api/auth/login', 
                          json=login_data,
                          headers={'Content-Type': 'application/json'})
    
    print(f"Status: {response.status_code}")
    data = response.get_json()
    print(f"Response: {data}")
    
    if response.status_code == 200:
        # Handle both 'token' and 'access_token' keys
        token = data.get('token') or data.get('access_token')
        if token:
            print(f"[OK] Token obtained: {token[:50]}...")
            
            # Test the dashboard stats endpoint
            print("\n=== Testing Admin Dashboard Stats ===")
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = client.get('/api/admin/dashboard/stats', headers=headers)
            print(f"Status: {response.status_code}")
            stats = response.get_json()
            print(f"Stats: {json.dumps(stats, indent=2)}")
        else:
            print("[ERROR] No token in response")
    else:
        print(f"[FAILED] Login failed: {data}")
