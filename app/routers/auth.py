"""Auth router — password login, 2FA, MS365 OAuth, password change."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.config import settings
from app.csrf_utils import get_csrf_token, validate_csrf
from app.database import get_db
from app.flash import set_flash
from app.models.models import User
from app.services.auth_service import (
    authenticate_user,
    disable_totp,
    enable_totp,
    generate_totp_secret,
    get_ms365_oauth_client,
    get_totp_uri,
    set_user_password,
    verify_totp,
)
from app.templates_setup import templates

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session(request: Request, user: User) -> None:
    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    request.session["user_name"] = user.display_name
    request.session["user_role"] = user.technical_role.value


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    # Redirect to home if already logged in
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)
    ms365 = get_ms365_oauth_client()
    return templates.TemplateResponse(request, "auth/login.html", {
        "csrf_token": get_csrf_token(request),
        "error": error,
        "ms365_enabled": ms365 is not None,
    })


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    form_token = form_data.get("csrf_token")
    session_token = request.session.get("csrf_token")
    print(f"DEBUG: form_token={form_token!r}, session_token={session_token!r}")
    if not validate_csrf(request, form_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    email = form_data.get("email", "").strip().lower()
    password = form_data.get("password", "")

    if not email or not password:
        return templates.TemplateResponse(request, "auth/login.html", {
            "csrf_token": get_csrf_token(request),
            "error": "Email and password are required",
            "ms365_enabled": get_ms365_oauth_client() is not None,
        })

    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(request, "auth/login.html", {
            "csrf_token": get_csrf_token(request),
            "error": "Invalid email or password",
            "ms365_enabled": get_ms365_oauth_client() is not None,
        })

    # If 2FA enabled, redirect to 2FA verification
    if user.totp_enabled:
        request.session["pending_2fa_user_id"] = user.id
        return RedirectResponse(url="/auth/2fa", status_code=303)

    _set_session(request, user)
    set_flash(request, f"Welcome back, {user.display_name}!")
    return RedirectResponse(url="/", status_code=303)


# ── 2FA ──

@router.get("/2fa", response_class=HTMLResponse)
def twofa_page(request: Request):
    if not request.session.get("pending_2fa_user_id"):
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse(request, "auth/2fa.html", {
        "csrf_token": get_csrf_token(request),
        "error": "",
    })


@router.post("/2fa")
async def twofa_verify(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user_id = request.session.get("pending_2fa_user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)

    code = form_data.get("code", "").strip()
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.totp_secret:
        return RedirectResponse(url="/auth/login", status_code=303)

    if not verify_totp(user.totp_secret, code):
        return templates.TemplateResponse(request, "auth/2fa.html", {
            "csrf_token": get_csrf_token(request),
            "error": "Invalid code. Try again.",
        })

    request.session.pop("pending_2fa_user_id", None)
    _set_session(request, user)
    set_flash(request, f"Welcome back, {user.display_name}!")
    return RedirectResponse(url="/", status_code=303)


# ── MS365 OAuth ──

@router.get("/ms365")
async def ms365_login(request: Request):
    ms365 = get_ms365_oauth_client()
    if not ms365:
        raise HTTPException(status_code=501, detail="MS365 OAuth not configured")
    redirect_uri = settings.MS365_REDIRECT_URI
    return await ms365.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def ms365_callback(request: Request, db: Session = Depends(get_db)):
    ms365 = get_ms365_oauth_client()
    if not ms365:
        raise HTTPException(status_code=501, detail="MS365 OAuth not configured")

    token = await ms365.authorize_access_token(request)
    claims = token.get("userinfo") or {}
    if not claims:
        # Fetch user info manually if not in token
        resp = await ms365.get("https://graph.microsoft.com/v1.0/me", token=token)
        if resp.status_code == 200:
            profile = resp.json()
            claims = {
                "oid": profile.get("id"),
                "email": profile.get("mail") or profile.get("userPrincipalName"),
                "name": profile.get("displayName"),
            }

    from app.services.auth_service import find_or_create_oauth_user

    user = find_or_create_oauth_user(db, claims)
    if not user:
        return templates.TemplateResponse(request, "auth/login.html", {
            "csrf_token": get_csrf_token(request),
            "error": "Could not find or create user from MS365 account",
            "ms365_enabled": True,
        })

    if not user.is_active:
        return templates.TemplateResponse(request, "auth/login.html", {
            "csrf_token": get_csrf_token(request),
            "error": "Your account has been deactivated",
            "ms365_enabled": True,
        })

    # 2FA check for OAuth users too
    if user.totp_enabled:
        request.session["pending_2fa_user_id"] = user.id
        return RedirectResponse(url="/auth/2fa", status_code=303)

    _set_session(request, user)
    set_flash(request, f"Welcome, {user.display_name}!")
    return RedirectResponse(url="/", status_code=303)


# ── Logout ──

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=303)


# ── Password change (logged-in users) ──

@router.get("/change-password", response_class=HTMLResponse)
def change_password_form(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(request, "auth/change_password.html", {
        "csrf_token": get_csrf_token(request),
        "errors": [],
        "user": user,
    })


@router.post("/change-password")
async def change_password(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    current = form_data.get("current_password", "")
    new = form_data.get("new_password", "")
    confirm = form_data.get("confirm_password", "")
    errors = []

    if not current:
        errors.append("Current password is required")
    if len(new) < 8:
        errors.append("New password must be at least 8 characters")
    if new != confirm:
        errors.append("Passwords do not match")

    if not errors:
        if user.password_hash and not authenticate_user(db, user.email, current):
            errors.append("Current password is incorrect")
        else:
            set_user_password(db, user, new)
            set_flash(request, "Password changed successfully.")
            return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(request, "auth/change_password.html", {
        "csrf_token": get_csrf_token(request),
        "errors": errors,
        "user": user,
    })


# ── 2FA setup (logged-in users) ──

@router.get("/2fa-setup", response_class=HTMLResponse)
def twofa_setup_page(request: Request, user=Depends(get_current_user)):
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, user.email)
    return templates.TemplateResponse(request, "auth/2fa_setup.html", {
        "csrf_token": get_csrf_token(request),
        "secret": secret,
        "totp_uri": uri,
        "error": "",
        "user": user,
    })


@router.post("/2fa-setup")
async def twofa_enable(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    secret = form_data.get("secret", "")
    code = form_data.get("code", "").strip()

    if enable_totp(db, user, secret, code):
        set_flash(request, "Two-factor authentication enabled.")
        return RedirectResponse(url="/", status_code=303)

    uri = get_totp_uri(secret, user.email)
    return templates.TemplateResponse(request, "auth/2fa_setup.html", {
        "csrf_token": get_csrf_token(request),
        "secret": secret,
        "totp_uri": uri,
        "error": "Invalid code. Make sure you entered the correct code from your authenticator.",
        "user": user,
    })


@router.post("/2fa-disable")
async def twofa_disable(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    disable_totp(db, user)
    set_flash(request, "Two-factor authentication disabled.", "warning")
    return RedirectResponse(url="/", status_code=303)
