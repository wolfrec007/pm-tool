"""Check system time and license status."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

print(f'System time: {datetime.now()}')
print(f'UTC time: {datetime.now(timezone.utc)}')

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text('SELECT id, name, license_tier, license_expires_at, license_activated_at FROM firms')).fetchone()
    print(f'Firm: {result}')
    
    # Check if license is expired
    if result and result[3]:  # license_expires_at
        now = datetime.now(timezone.utc)
        expires_at = result[3]
        print(f'License expires: {expires_at}')
        print(f'Current time: {now}')
        print(f'Is expired: {now > expires_at}')
except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()
