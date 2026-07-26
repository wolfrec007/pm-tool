"""Test Gmail registration flow."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.otp_service import find_firm_by_domain, generate_otp
from app.database import SessionLocal

db = SessionLocal()
try:
    email = "test@gmail.com"
    
    # Test domain matching
    print(f"Testing email: {email}")
    firm, reason = find_firm_by_domain(db, email)
    print(f"Firm match: {firm}")
    print(f"Reason: {reason}")
    
    # Test OTP generation
    print("\nGenerating OTP...")
    otp = generate_otp(email)
    print(f"OTP: {otp}")
    print("OTP generated successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
