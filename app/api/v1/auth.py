"""API v1 auth endpoints — login, me, refresh, firm-switch."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token, create_refresh_token, decode_refresh_token
from app.database import get_db
from app.models.models import User
from app.schemas.v1.auth import (
    LoginRequest, TokenResponse, RefreshRequest,
    MeResponse, UserResponse, FirmResponse, FirmUserResponse,
    FirmSwitchRequest,
)
from app.services.auth_service import authenticate_user
from app.services.firm_service import get_user_firms, get_firm_user

router = APIRouter(prefix="/auth", tags=["api-auth"])


@router.post("/login", response_model=TokenResponse)
def api_login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email/password, return JWT tokens."""
    user = authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Get user's first firm for initial token
    firms = get_user_firms(db, user.id)
    firm_id = firms[0].id if firms else None

    access_token = create_access_token(user.id, firm_id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def api_refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = decode_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.is_active).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    firms = get_user_firms(db, user.id)
    firm_id = firms[0].id if firms else None

    access_token = create_access_token(user.id, firm_id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=MeResponse)
def api_me(request: Request, db: Session = Depends(get_db)):
    """Get current user info, firms, and active firm."""
    from app.auth.auth import get_current_user
    from app.api.v1.deps import get_firm_id

    # Get user from JWT or session
    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        from app.auth.jwt import decode_access_token
        token = auth_header[7:]
        payload = decode_access_token(token)
        if payload:
            user = db.query(User).filter(User.id == int(payload["sub"]), User.is_active).first()
    
    if not user:
        user_id = request.session.get("user_id")
        if user_id:
            user = db.query(User).filter(User.id == user_id, User.is_active).first()

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get firms
    firms = get_user_firms(db, user.id)
    firm_users = []
    for f in firms:
        fu = get_firm_user(db, user.id, f.id)
        if fu:
            firm_users.append(FirmUserResponse(
                firm=FirmResponse.model_validate(f),
                role=fu.technical_role.value,
            ))

    # Get active firm_id
    active_firm_id = None
    firm_id = request.session.get("firm_id")
    if firm_id:
        active_firm_id = int(firm_id)
    elif firms:
        active_firm_id = firms[0].id

    return MeResponse(
        user=UserResponse.model_validate(user),
        firms=firm_users,
        active_firm_id=active_firm_id,
    )


@router.post("/firm/switch")
def api_firm_switch(body: FirmSwitchRequest, request: Request,
                    db: Session = Depends(get_db)):
    """Switch active firm. Updates session and returns new token."""
    from app.auth.auth import get_current_user

    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        from app.auth.jwt import decode_access_token
        token = auth_header[7:]
        payload = decode_access_token(token)
        if payload:
            user = db.query(User).filter(User.id == int(payload["sub"]), User.is_active).first()

    if not user:
        user_id = request.session.get("user_id")
        if user_id:
            user = db.query(User).filter(User.id == user_id, User.is_active).first()

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify user belongs to this firm
    fu = get_firm_user(db, user.id, body.firm_id)
    if not fu or not fu.is_active:
        raise HTTPException(status_code=403, detail="Not a member of this firm")

    # Update session
    request.session["firm_id"] = body.firm_id

    # Return new token with updated firm_id
    access_token = create_access_token(user.id, body.firm_id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
