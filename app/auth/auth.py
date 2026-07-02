import secrets
from typing import Optional

from fastapi import Depends, Form, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, TechnicalRole

# Session-based auth skeleton.
# In production, wire MS365 OAuth flow here.
# For now, we support a simple session cookie or basic header for dev.


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract current user from session cookie.

    Falls back to X-User-Id header for dev/testing convenience.
    Replace with real OIDC validation in production.
    """
    user_id = request.session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active).first()
        if user:
            return user

    # Dev fallback: X-User-Id header
    header_id = request.headers.get("X-User-Id")
    if header_id:
        try:
            user = db.query(User).filter(
                User.id == int(header_id), User.is_active
            ).first()
            if user:
                return user
        except (ValueError, TypeError):
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


def require_role(*roles: TechnicalRole):
    """Dependency factory: require current user to have one of the given roles."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.technical_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _check
