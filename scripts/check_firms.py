"""Check firms in database."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text('SELECT id, name, code, allowed_domains FROM firms')).fetchall()
    print('Firms in database:')
    for r in result:
        print(f'  ID: {r[0]}, Name: {r[1]}, Code: {r[2]}, Domains: {r[3]}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
