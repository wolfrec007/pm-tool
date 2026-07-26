"""Test SMTP connection."""
import smtplib
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

print('Testing SMTP connection...')
print(f'Host: {settings.SMTP_HOST}')
print(f'Port: {settings.SMTP_PORT}')
print(f'User: {settings.SMTP_USER}')
print(f'From: {settings.SMTP_FROM_EMAIL}')
print(f'Password configured: {bool(settings.SMTP_PASSWORD)}')
print()

try:
    print('Connecting to SMTP server...')
    if settings.SMTP_USE_SSL:
        # SSL connection (port 465)
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            print('Connected via SSL!')
            print('Logging in...')
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            print('Login successful!')
    else:
        # TLS connection (port 587)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            print('Connected via TLS!')
            print('Starting TLS...')
            server.starttls()
            print('Logging in...')
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            print('Login successful!')
    
    print()
    print('SMTP is configured correctly!')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
