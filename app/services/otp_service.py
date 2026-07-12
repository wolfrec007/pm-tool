"""OTP service for email verification during registration."""

import random
import string
from datetime import datetime, timedelta, timezone

# In-memory OTP store (for production, use Redis or DB)
_otp_store: dict[str, dict] = {}


def generate_otp(email: str, length: int = 6) -> str:
    """Generate a numeric OTP and store it with expiry."""
    otp = "".join(random.choices(string.digits, k=length))
    _otp_store[email] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "attempts": 0,
    }
    return otp


def verify_otp(email: str, otp: str) -> bool:
    """Verify OTP. Returns True if valid."""
    stored = _otp_store.get(email)
    if not stored:
        return False

    if datetime.now(timezone.utc) > stored["expires_at"]:
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


def is_valid_email_domain(email: str, allowed_domains: str | None) -> bool:
    """Check if email domain matches any of the allowed domains.

    If allowed_domains is None or empty, all domains are allowed.
    """
    if not allowed_domains:
        return True

    domain = email.split("@")[-1].lower().strip()
    allowed = [d.strip().lower() for d in allowed_domains.split(",") if d.strip()]
    return domain in allowed


def get_firm_for_email(db, email: str):
    """Find the firm that allows this email domain.

    Returns (Firm, match_reason) or (None, reason).
    """
    from app.models.models import Firm

    domain = email.split("@")[-1].lower().strip()
    firms = db.query(Firm).filter(Firm.is_active == True).all()

    for firm in firms:
        if is_valid_email_domain(email, firm.allowed_domains):
            return firm, f"Domain matches {firm.name}"

    return None, "No firm matches your email domain"
