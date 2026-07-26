"""Test registration flow."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback

try:
    from app.routers.auth import register_check_domain
    from app.database import get_db
    from app.templates_setup import templates
    from fastapi import Request
    from starlette.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    
    # Get register page to get CSRF token
    resp = client.get('/auth/register')
    print(f'GET /register: {resp.status_code}')
    
    # Extract CSRF
    import re
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.text)
    if match:
        csrf = match.group(1)
        print(f'CSRF token found: {csrf[:20]}...')
    else:
        csrf = ''
        print('No CSRF token found')
    
    # Test check-domain
    resp = client.post('/auth/register/check-domain', data={
        'email': 'test@gmail.com',
        'csrf_token': csrf
    })
    print(f'POST check-domain: {resp.status_code}')
    
    if resp.status_code == 500:
        # Try to get the actual error
        print('\n--- Testing individual components ---')
        
        from app.database import SessionLocal
        from app.models.models import User
        
        db = SessionLocal()
        
        # Test DB query
        try:
            existing = db.query(User).filter(User.email == 'test@gmail.com').first()
            print(f'User query OK: {existing}')
        except Exception as e:
            print(f'User query FAILED: {e}')
        
        # Test find_firm_by_domain
        try:
            from app.services.otp_service import find_firm_by_domain
            firm, reason = find_firm_by_domain(db, 'test@gmail.com')
            print(f'find_firm_by_domain OK: firm={firm}, reason={reason}')
        except Exception as e:
            print(f'find_firm_by_domain FAILED: {e}')
        
        # Test template rendering
        try:
            from starlette.requests import Request as StarletteRequest
            from starlette.datastructures import Headers
            scope = {'type': 'http', 'method': 'POST', 'path': '/auth/register/check-domain', 
                     'headers': [], 'session': {}}
            req = StarletteRequest(scope)
            resp = templates.TemplateResponse(req, "auth/register.html", {
                "csrf_token": "test",
                "error": "",
                "step": "2",
                "email": "test@gmail.com",
                "otp_sent": True,
            })
            print(f'Template render OK')
        except Exception as e:
            print(f'Template render FAILED: {e}')
            traceback.print_exc()
        
        db.close()
    
except Exception as e:
    print(f'Exception: {e}')
    traceback.print_exc()
