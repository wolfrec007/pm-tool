"""License validation middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import SessionLocal
from app.models.models import Firm
from app.services.license_service import check_license

# Paths that don't require a license
EXEMPT_PATHS = [
    "/auth/",
    "/health",
    "/static/",
    "/super-admin/",
    "/api/v1/auth/",
    "/license/",
    "/favicon.ico",
    "/docs",
    "/openapi.json",
    "/redoc",
]


class LicenseMiddleware(BaseHTTPMiddleware):
    """Check that the user's firm has a valid license before accessing the app."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt paths
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        # Skip if no firm context (user hasn't logged in or selected firm)
        firm_id = request.session.get("firm_id")
        if not firm_id:
            return await call_next(request)

        # Check license
        db = SessionLocal()
        try:
            firm = db.query(Firm).filter(Firm.id == firm_id).first()
            if not firm:
                return await call_next(request)

            status = check_license(firm)

            if status == "no_license":
                # Redirect to activation page
                if path.startswith("/api/"):
                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        {"detail": "License required. Please activate a license key."},
                        status_code=403,
                    )
                return RedirectResponse("/license/activate", status_code=302)

            if status == "expired":
                # Hard cutoff
                if path.startswith("/api/"):
                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        {"detail": "License expired. Please renew your license."},
                        status_code=403,
                    )
                return RedirectResponse("/license/expired", status_code=302)

            if status == "grace":
                # Set flag for templates to show warning
                request.state.license_grace = True
                request.state.license_expires_at = firm.license_expires_at

            request.state.license_status = status
            request.state.license_tier = firm.license_tier

        finally:
            db.close()

        return await call_next(request)
