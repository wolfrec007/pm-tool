"""Test login and register pages."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback

try:
    from app.main import app
    from starlette.testclient import TestClient
    
    client = TestClient(app, raise_server_exceptions=False)
    
    # Test login
    resp = client.get('/auth/login')
    print(f'GET /auth/login: {resp.status_code}')
    
    # Test register
    resp = client.get('/auth/register')
    print(f'GET /auth/register: {resp.status_code}')
    
    # Test dashboard
    resp = client.get('/dashboard')
    print(f'GET /dashboard: {resp.status_code}')
    
    # Test license
    resp = client.get('/license/activate')
    print(f'GET /license/activate: {resp.status_code}')
    
    # Test reports
    resp = client.get('/reports')
    print(f'GET /reports: {resp.status_code}')
    
    # Test admin settings
    resp = client.get('/admin/settings')
    print(f'GET /admin/settings: {resp.status_code}')
    
except Exception as e:
    print(f'Exception: {e}')
    traceback.print_exc()
