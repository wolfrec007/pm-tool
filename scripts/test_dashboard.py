"""Test dashboard rendering."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback

try:
    from app.main import app
    from starlette.testclient import TestClient
    
    client = TestClient(app, raise_server_exceptions=False)
    
    # Login first
    resp = client.get('/auth/login')
    print(f'GET /auth/login: {resp.status_code}')
    
    # Get CSRF token
    import re
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.text)
    csrf = match.group(1) if match else ''
    
    # Login
    resp = client.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'Admin@123',
        'csrf_token': csrf
    }, follow_redirects=False)
    print(f'POST /auth/login: {resp.status_code}')
    
    # Access dashboard
    resp = client.get('/dashboard')
    print(f'GET /dashboard: {resp.status_code}')
    
    if resp.status_code == 500:
        print('ERROR 500 - Response:')
        print(resp.text[:3000])
    
except Exception as e:
    print(f'Exception: {e}')
    traceback.print_exc()
