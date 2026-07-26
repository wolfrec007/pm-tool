"""Check firm domains."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text('SELECT id, name, allowed_domains FROM firms')).fetchall()
    print('Firm domains:')
    for r in result:
        print(f'  ID: {r[0]}, Name: {r[1]}, Domains: {r[2]}')
except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()
