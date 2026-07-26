"""Test dashboard with login to capture the actual error."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback

try:
    from app.database import SessionLocal
    from app.models.models import User, FirmUser, Firm
    from app.services.auth_service import authenticate_user
    
    db = SessionLocal()
    
    # Test auth
    user = authenticate_user(db, 'admin@test.com', 'Admin@123')
    print(f'User: {user.email if user else None}')
    
    if user:
        # Get firm
        firm_user = db.query(FirmUser).filter(FirmUser.user_id == user.id).first()
        print(f'FirmUser: {firm_user}')
        
        if firm_user:
            firm = db.query(Firm).filter(Firm.id == firm_user.firm_id).first()
            print(f'Firm: {firm.name if firm else None}')
            
            # Test license check
            from app.services.license_service import check_license, get_days_remaining
            license_status = check_license(firm)
            days_remaining = get_days_remaining(firm)
            print(f'License status: {license_status}')
            print(f'Days remaining: {days_remaining}')
            
            # Test dashboard query
            from sqlalchemy import func
            from app.models.models import TeamMember, Assignment, Engagement, Client, Leave
            from datetime import date
            
            today = date.today()
            firm_id = firm.id
            
            total_members = db.query(func.count(TeamMember.id)).filter(
                TeamMember.firm_id == firm_id, TeamMember.is_active == True
            ).scalar() or 0
            print(f'Total members: {total_members}')
            
            # Test show_onboarding logic
            from datetime import datetime, timedelta, timezone
            show_onboarding = False
            if firm.created_at and firm.created_at > datetime.now(timezone.utc) - timedelta(days=7):
                if total_members == 0:
                    show_onboarding = True
            print(f'Show onboarding: {show_onboarding}')
            print(f'Firm created: {firm.created_at}')
            print(f'7 days ago: {datetime.now(timezone.utc) - timedelta(days=7)}')
            
    db.close()
    print('SUCCESS')
    
except Exception as e:
    print(f'Exception: {e}')
    traceback.print_exc()
