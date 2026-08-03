"""Password expiry middleware — forces password change when policy expires."""

import logging
from datetime import datetime, timedelta, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse

from app.database import SessionLocal
from app.models.models import User
from app.services.settings_service import get_password_expiry_days

logger = logging.getLogger(__name__)

# Paths that bypass password expiry check
EXEMPT_PATHS = [
    "/auth/login",
    "/auth/logout",
    "/auth/register",
    "/auth/forgot-password",
    "/auth/change-password",
    "/auth/accept-invitation",
    "/auth/ms365",
    "/auth/callback",
    "/auth/firm-select",
    "/auth/2fa",
    "/auth/2fa-setup",
    "/auth/2fa-setup-optional",
    "/auth/login-verify",
    "/auth/theme",
    "/health",
    "/static/",
    "/license/",
    "/favicon.ico",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/",
    "/contact",
    "/dev-portal/",
]


class PasswordExpiryMiddleware(BaseHTTPMiddleware):
    """Redirect users to change-password when their password has expired."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt paths
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        # Skip if not logged in
        user_id = request.session.get("user_id")
        firm_id = request.session.get("firm_id")
        if not user_id or not firm_id:
            return await call_next(request)

        db = SessionLocal()
        try:
            expiry_days = get_password_expiry_days(db, firm_id)
            if expiry_days <= 0:
                return await call_next(request)

            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.password_changed_at:
                return await call_next(request)

            cutoff = datetime.now(timezone.utc) - timedelta(days=expiry_days)
            if user.password_changed_at < cutoff:
                # Password expired
                if path.startswith("/api/"):
                    return JSONResponse(
                        {"detail": "password_expired", "message": "Your password has expired. Please change it."},
                        status_code=403,
                    )
                return RedirectResponse("/auth/change-password?forced=1", status_code=302)
        finally:
            db.close()

        return await call_next(request)
