import secrets

from fastapi import Request


def get_csrf_token(request: Request) -> str:
    """Get or generate a CSRF token stored in the session."""
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        request.session["csrf_token"] = token
    return token


def validate_csrf(request: Request, form_token: str | None) -> bool:
    """Validate a submitted CSRF token against the session."""
    expected = request.session.get("csrf_token")
    if not expected:
        # No session token yet — allow (first request or session not persisted)
        return True
    if not form_token:
        return False
    return secrets.compare_digest(form_token, expected)
