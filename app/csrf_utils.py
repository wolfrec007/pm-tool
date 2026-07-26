import secrets

from fastapi import HTTPException, Request


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


async def require_csrf(request: Request) -> None:
    """FastAPI dependency: validate CSRF token from form data.
    
    Usage:
        @router.post("/some-form")
        async def handle_form(request: Request, _: None = Depends(require_csrf)):
            form_data = await request.form()
            # CSRF is already validated, proceed with form processing
    """
    form = await request.form()
    csrf_token = form.get("csrf_token")
    if not validate_csrf(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
