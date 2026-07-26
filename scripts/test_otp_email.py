"""Test OTP email sending."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.otp_service import send_otp_email

print('Testing OTP email sending...')
print('Sending test OTP to test@example.com...')

try:
    send_otp_email('test@example.com', '123456')
    print('OTP email sent successfully!')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
