"""Dev portal auth dependency — access code gate + session validation."""

import hashlib
import hmac
import time

from fastapi import HTTPException, Request

from app.config import settings


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def check_gate(request: Request) -> bool:
    gate_cookie = request.cookies.get("dev_portal_gate")
    if not gate_cookie:
        return False
    expected = _hash_code(settings.DEV_PORTAL_ACCESS_CODE)
    return hmac.compare_digest(gate_cookie, expected)


def require_dev_portal(request: Request):
    """Dependency: require valid gate cookie + active dev portal session."""
    if not check_gate(request):
        raise HTTPException(status_code=404, detail="Not found")

    sa_id = request.session.get("dev_portal_sa_id")
    if not sa_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_started = request.session.get("dev_portal_started_at", 0)
    if time.time() - session_started > settings.DEV_PORTAL_SESSION_MAX_AGE:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session expired")

    request.session["dev_portal_started_at"] = time.time()
    return sa_id
