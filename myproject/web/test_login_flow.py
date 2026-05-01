import sys
import json
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')

from app import app

with app.test_client() as client:
    print("=" * 60)
    print("SIMULATING FRESH ADMIN LOGIN AND DASHBOARD LOAD")
    print("=" * 60)
    
    # Step 1: Login
    print("\n[STEP 1] Admin Login")
    login_response = client.post('/api/auth/login', 
                                json={'email': 'admin@example.com', 'password': 'admin123'},
                                headers={'Content-Type': 'application/json'})
    
    login_data = login_response.get_json()
    token = login_data.get('token') or login_data.get('access_token')
    
    print(f"  Status: {login_response.status_code}")
    print(f"  Token: {token[:50] if token else 'NOT FOUND'}...")
    print(f"  User role: {login_data.get('user', {}).get('role')}")
    
    if login_response.status_code != 200:
        print(f"  ERROR: Login failed with status {login_response.status_code}")
        print(f"  Response: {login_data}")
        sys.exit(1)
    
    # Step 2: Call stats API with token
    print("\n[STEP 2] Fetch Dashboard Stats")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    stats_response = client.get('/api/admin/dashboard/stats', headers=headers)
    print(f"  Status: {stats_response.status_code}")
    
    if stats_response.status_code != 200:
        print(f"  ERROR: API call failed with status {stats_response.status_code}")
        error_data = stats_response.get_json()
        print(f"  Error response: {error_data}")
        sys.exit(1)
    
    stats_data = stats_response.get_json()
    
    print("\n  [API RESPONSE DATA]:")
    print(f"    total_users: {stats_data.get('total_users')}")
    print(f"    total_cases: {stats_data.get('total_cases')}")
    print(f"    pending_cases: {stats_data.get('pending_cases')}")
    print(f"    approved_cases: {stats_data.get('approved_cases')}")
    print(f"    total_donations: {stats_data.get('total_donations')}")
    print(f"    recent_cases: {len(stats_data.get('recent_cases', []))} cases")
    
    # Step 3: Verify values are not zero
    print("\n[STEP 3] Validation")
    issues = []
    if stats_data.get('total_cases') == 0:
        issues.append("  ERROR: total_cases is 0 in API response")
    if stats_data.get('pending_cases') == 0:
        issues.append("  ERROR: pending_cases is 0 in API response")
    if stats_data.get('total_donations') == 0:
        issues.append("  ERROR: total_donations is 0 in API response")
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("  SUCCESS: All stats have non-zero values")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
