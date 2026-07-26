"""OTP service for email verification during registration."""

import logging
import random
import smtplib
import string
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory OTP store (for production, use Redis or DB)
_otp_store: dict[str, dict] = {}

# Rate limiting: track last send time per email
_last_sent: dict[str, datetime] = {}

# Rate limit constants
RESEND_COOLDOWN_SECONDS = 60
MAX_OTP_PER_HOUR = 5


def can_resend_otp(email: str) -> tuple[bool, int]:
    """Check if OTP can be resent. Returns (can_resend, seconds_remaining)."""
    now = datetime.now(timezone.utc)
    last_sent = _last_sent.get(email)
    if last_sent:
        elapsed = (now - last_sent).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            return False, int(RESEND_COOLDOWN_SECONDS - elapsed)
    return True, 0


def generate_otp(email: str, length: int = 6, purpose: str = "verification") -> str:
    """Generate a numeric OTP and store it with expiry.
    
    Args:
        email: Recipient email
        length: OTP length (default 6)
        purpose: "verification" or "password_reset" — controls email template
    """
    now = datetime.now(timezone.utc)
    
    stored = _otp_store.get(email)
    if stored:
        if stored.get("hourly_count", 0) >= MAX_OTP_PER_HOUR:
            if now < stored.get("hourly_reset", now):
                raise ValueError("Too many OTP requests. Please try again later.")
            stored["hourly_count"] = 0
            stored["hourly_reset"] = now + timedelta(hours=1)
    
    otp = "".join(random.choices(string.digits, k=length))
    
    hourly_count = (stored.get("hourly_count", 0) + 1) if stored else 1
    hourly_reset = stored.get("hourly_reset", now + timedelta(hours=1)) if stored else now + timedelta(hours=1)
    
    _otp_store[email] = {
        "otp": otp,
        "expires_at": now + timedelta(minutes=10),
        "attempts": 0,
        "hourly_count": hourly_count,
        "hourly_reset": hourly_reset,
    }
    
    _last_sent[email] = now
    
    try:
        send_otp_email(email, otp, purpose=purpose)
        logger.info(f"OTP sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        logger.info(f"OTP for {email}: {otp}")
    
    return otp


def verify_otp(email: str, otp: str) -> bool:
    """Verify OTP. Returns True if valid."""
    stored = _otp_store.get(email)
    if not stored:
        return False

    now = datetime.now(timezone.utc)
    
    if now > stored["expires_at"]:
        _otp_store.pop(email, None)
        return False

    stored["attempts"] += 1
    if stored["attempts"] > 5:
        _otp_store.pop(email, None)
        return False

    if stored["otp"] == otp:
        _otp_store.pop(email, None)
        return True

    return False


def _build_verification_email_html(otp: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 400px; margin: 0 auto; padding: 20px; }}
            .code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px; text-align: center; padding: 20px; background: #f4f4f5; border-radius: 8px; margin: 20px 0; }}
            .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Verification Code</h2>
            <p>Your verification code for splanly is:</p>
            <div class="code">{otp}</div>
            <p>This code will expire in <strong>10 minutes</strong>.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <div class="footer">
                <p>&mdash; The splanly Team</p>
            </div>
        </div>
    </body>
    </html>
    """


def _build_reset_email_html(otp: str) -> str:
    return f"""
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en">
    <head>
    <meta charset="UTF-8" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width" />
    <style type="text/css">
        body {{ margin:0; padding:0; background-color:#E0E0E0; -webkit-font-smoothing:antialiased; }}
        table {{ border-collapse:separate; }}
        a {{ text-decoration:none; }}
        @media (max-width: 480px) {{
            .main-cell {{ padding:20px 30px !important; }}
        }}
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Albert+Sans:wght@500;800&amp;display=swap" rel="stylesheet" type="text/css" />
    </head>
    <body style="min-width:100%;margin:0;padding:0;background-color:#E0E0E0;">
    <div style="background-color:#E0E0E0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" align="center">
    <tr><td style="font-size:0;line-height:0;background-color:#E0E0E0;" valign="top" align="center">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" align="center">
    <tr><td align="center">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-left:auto;margin-right:auto;">
    <tr><td style="width:566px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td style="padding:50px 10px 31px 10px;">
    <div style="width:100%;text-align:left;">
    <div style="display:inline-block;">
    <table role="presentation" cellpadding="0" cellspacing="0" align="left" valign="top">
    <tr>
    <td></td>
    <td width="546" valign="top">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="background-color:transparent;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <!-- Header -->
    <tr><td align="center">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-left:auto;margin-right:auto;">
    <tr><td style="width:600px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td>
    <div style="width:100%;text-align:left;">
    <div style="display:inline-block;">
    <table role="presentation" cellpadding="0" cellspacing="0" align="left" valign="top">
    <tr>
    <td></td>
    <td width="546" valign="top">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="overflow:hidden;background-color:#A2B6DE;padding:43px 50px 42px 50px;border-radius:18px 18px 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="left">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-right:auto;">
    <tr><td style="width:85px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td>
    <div style="font-size:0px;">
        <div style="width:85px;height:85px;border-radius:20px;background:linear-gradient(135deg,#14304d 0%,#1e4468 100%);display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'Albert Sans',sans-serif;font-size:28px;font-weight:800;color:#ffffff;letter-spacing:-1px;">splanly</span>
        </div>
    </div>
    </td></tr></table>
    </td></tr></table>
    </td></tr></table>
    </td></tr></table>
    </td>
    <td></td></tr>
    </table></div></div>
    </td></tr></table>
    </td></tr></table>
    </td></tr></table>
    </td></tr>
    <!-- Body -->
    <tr><td align="center">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-left:auto;margin-right:auto;">
    <tr><td style="width:600px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td>
    <div style="width:100%;text-align:left;">
    <div style="display:inline-block;">
    <table role="presentation" cellpadding="0" cellspacing="0" align="left" valign="top">
    <tr>
    <td></td>
    <td width="546" valign="top">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="overflow:hidden;background-color:#F8F8F8;padding:40px 50px 40px 50px;border-radius:0 0 18px 18px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-left:auto;margin-right:auto;">
    <tr><td style="width:381px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td>
    <h1 style="margin:0;font-family:'Albert Sans',BlinkMacSystemFont,'Segoe UI',Helvetica Neue,Arial,sans-serif;line-height:41px;font-weight:800;font-size:30px;letter-spacing:-1.56px;color:#191919;text-align:left;">
        Forgot your password?<br/>It happens to the best of us.
    </h1>
    </td></tr></table>
    </td></tr></table>
    </td></tr>
    <tr><td><div style="line-height:25px;font-size:1px;display:block;">&nbsp;</div></td></tr>
    <tr><td align="left">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-right:auto;">
    <tr><td style="width:563px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td>
    <p style="margin:0;font-family:'Albert Sans',sans-serif;line-height:22px;font-weight:500;font-size:14px;letter-spacing:-0.56px;color:#333333;text-align:left;">
        To reset your password, enter the verification code below. The code will expire in 10 minutes.
    </p>
    </td></tr></table>
    </td></tr></table>
    </td></tr>
    <tr><td><div style="line-height:15px;font-size:1px;display:block;">&nbsp;</div></td></tr>
    <!-- OTP Code Box -->
    <tr><td align="center">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-left:auto;margin-right:auto;">
    <tr><td style="width:234px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td style="overflow:hidden;background-color:#1A41B8;text-align:center;line-height:44px;padding:10px 30px 10px 30px;border-radius:40px;">
    <span style="display:block;margin:0;font-family:'Albert Sans',sans-serif;line-height:44px;font-weight:800;font-size:24px;letter-spacing:8px;color:#FFFFFF;">
        {otp}
    </span>
    </td></tr></table>
    </td></tr></table>
    </td></tr>
    <tr><td><div style="line-height:15px;font-size:1px;display:block;">&nbsp;</div></td></tr>
    <tr><td align="left">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-right:auto;">
    <tr><td style="width:563px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td>
    <p style="margin:0;font-family:'Albert Sans',sans-serif;line-height:22px;font-weight:500;font-size:14px;letter-spacing:-0.56px;color:#333333;text-align:left;">
        If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
    </p>
    </td></tr></table>
    </td></tr></table>
    </td></tr>
    </table></td></tr></table>
    </td>
    <td></td></tr>
    </table></div></div>
    </td></tr></table>
    </td></tr></table>
    </td></tr>
    </table></td></tr></table>
    </td></tr></table>
    </td>
    <td></td></tr>
    </table></div></div>
    </td></tr></table>
    </td></tr></table>
    </td></tr>
    <!-- Footer -->
    <tr><td align="center">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-left:auto;margin-right:auto;">
    <tr><td style="width:600px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td>
    <div style="width:100%;text-align:left;">
    <div style="display:inline-block;">
    <table role="presentation" cellpadding="0" cellspacing="0" align="left" valign="top">
    <tr>
    <td></td>
    <td width="600" valign="top">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="padding:0 50px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-left:auto;margin-right:auto;">
    <tr><td style="width:600px;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr><td>
    <p style="margin:0;font-family:'Albert Sans',sans-serif;line-height:22px;font-weight:500;font-size:12px;color:#888888;text-align:center;">
        &copy; 2026 SkilledCA Enterprises &mdash; All Rights Reserved
    </p>
    </td></tr></table>
    </td></tr></table>
    </td></tr></table>
    </td></tr></table>
    </td>
    <td></td></tr>
    </table></div></div>
    </td></tr></table>
    </td></tr></table>
    </td></tr>
    <tr><td><div style="line-height:50px;font-size:1px;display:block;">&nbsp;</div></td></tr>
    </table></td></tr></table>
    </div>
    </body>
    </html>
    """


def send_otp_email(to_email: str, otp: str, purpose: str = "verification") -> None:
    """Send OTP via email using SMTP."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP not configured, skipping email send")
        logger.info(f"OTP for {to_email}: {otp}")
        return

    msg = MIMEMultipart("alternative")

    if purpose == "password_reset":
        msg["Subject"] = "Reset your splanly password"
        html = _build_reset_email_html(otp)
    else:
        msg["Subject"] = "Your splanly Verification Code"
        html = _build_verification_email_html(otp)

    msg["From"] = f"splanly <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                logger.info(f"OTP email sent to {to_email}")
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                logger.info(f"OTP email sent to {to_email}")
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        raise


def find_firm_by_domain(db, email: str):
    """Find firm by email domain.
    
    Returns:
        (Firm, "Domain matches {firm_name}") if domain matches a firm
        (None, "No firm found for this domain") if no match
    """
    from app.models.models import Firm
    
    domain = email.split("@")[-1].lower().strip()
    firms = db.query(Firm).filter(Firm.is_active == True).all()
    
    for firm in firms:
        if firm.allowed_domains:
            allowed = [d.strip().lower() for d in firm.allowed_domains.split(",") if d.strip()]
            if domain in allowed:
                return firm, f"Domain matches {firm.name}"
    
    return None, "No firm found for this domain"


def is_valid_email_domain(email: str, allowed_domains: str | None) -> bool:
    """Check if email domain matches any of the allowed domains."""
    if not allowed_domains:
        return False
    domain = email.split("@")[-1].lower().strip()
    allowed = [d.strip().lower() for d in allowed_domains.split(",") if d.strip()]
    return domain in allowed
