"""Auth service — password hashing, TOTP 2FA, MS365 OAuth."""

import secrets
from typing import Optional

import bcrypt
import pyotp
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import User


# ── Password ──

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate by email + password. Returns User or None."""
    user = db.query(User).filter(User.email == email, User.is_active).first()
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def set_user_password(db: Session, user: User, password: str) -> None:
    user.password_hash = hash_password(password)
    db.commit()


# ── TOTP 2FA ──

def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.APP_NAME,
    )


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def enable_totp(db: Session, user: User, secret: str, code: str) -> bool:
    """Enable TOTP after verifying the code matches the secret."""
    if not verify_totp(secret, code):
        return False
    user.totp_secret = secret
    user.totp_enabled = True
    db.commit()
    return True


def disable_totp(db: Session, user: User) -> None:
    user.totp_secret = None
    user.totp_enabled = False
    db.commit()


# ── MS365 OAuth ──

def get_ms365_oauth_client():
    """Create an OAuth client for Microsoft 365 / Entra ID.

    Returns None if OAuth is not configured.
    """
    if not settings.MS365_CLIENT_ID or not settings.MS365_CLIENT_SECRET:
        return None

    from authlib.integrations.starlette_client import OAuth

    oauth = OAuth()
    oauth.register(
        name="microsoft",
        client_id=settings.MS365_CLIENT_ID,
        client_secret=settings.MS365_CLIENT_SECRET,
        server_metadata_url=(
            f"https://login.microsoftonline.com/{settings.MS365_TENANT_ID}"
            "/v2.0/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile"},
    )
    return oauth.microsoft


def find_or_create_oauth_user(db: Session, claims: dict) -> Optional[User]:
    """Find existing user by azure_oid or email, or create one from OAuth claims."""
    oid = claims.get("oid")
    email = claims.get("email") or claims.get("preferred_username")

    # Try by azure_oid first
    if oid:
        user = db.query(User).filter(User.azure_oid == oid).first()
        if user:
            return user

    # Try by email
    if email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Link azure_oid if not set
            if oid and not user.azure_oid:
                user.azure_oid = oid
                db.commit()
            return user

    # Create new user if email present
    if email:
        display_name = claims.get("name", email.split("@")[0])
        user = User(
            email=email,
            display_name=display_name,
            azure_oid=oid,
            technical_role="viewer",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return None
