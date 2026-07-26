"""Update firm domains to restrict registration."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Update PKF firm to only allow specific domains
    db.execute(text("UPDATE firms SET allowed_domains = 'pkf.in,skilledca.in' WHERE id = 1"))
    db.commit()
    print('Updated PKF firm domains to: pkf.in, skilledca.in')
    
    # Verify the change
    result = db.execute(text('SELECT id, name, allowed_domains FROM firms WHERE id = 1')).fetchone()
    print(f'Firm: {result[1]}, Domains: {result[2]}')
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
    import traceback
    traceback.print_exc()
finally:
    db.close()
