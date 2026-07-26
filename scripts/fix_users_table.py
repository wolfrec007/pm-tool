"""Fix users table - add deleted_at columns."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE'))
    print('Added deleted_at')
    db.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL'))
    print('Added deleted_by_user_id')
    db.commit()
    print('Done!')
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
finally:
    db.close()
