"""Create an admin user for testing."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.models import User, FirmUser, TechnicalRole
from app.services.auth_service import hash_password

db = SessionLocal()
try:
    # Check if user exists
    existing = db.query(User).filter(User.email == 'admin@test.com').first()
    if existing:
        print(f'User already exists: {existing.email} (ID: {existing.id})')
    else:
        user = User(
            email='admin@test.com',
            display_name='Admin User',
            password_hash=hash_password('Admin@123'),
            is_active=True,
        )
        db.add(user)
        db.flush()
        print(f'Created user: admin@test.com (ID: {user.id})')
        
        # Add to firm 1 as admin
        firm_user = FirmUser(
            user_id=user.id,
            firm_id=1,
            technical_role=TechnicalRole.admin,
            is_active=True,
        )
        db.add(firm_user)
        db.commit()
        print(f'Password: Admin@123')
        print('User added to firm 1 as admin')
except Exception as e:
    db.rollback()
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
