from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user, require_role
from app.csrf_utils import get_csrf_token, validate_csrf
from app.database import get_db
from app.exceptions import ValidationError
from app.flash import set_flash
from app.models.models import TechnicalRole
from app.schemas.schemas import UserCreate, UserRead, UserUpdate
from app.services import user_service as service
from app.templates_setup import templates

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_class=HTMLResponse)
def list_users(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin)),
):
    firm_id = request.session.get("firm_id")
    items, total = service.list_users(
        db, limit=limit, offset=offset, q=q, is_active=is_active
    )
    # Attach firm_role to each user for template display
    from app.services.firm_service import get_user_role_in_firm
    for u in items:
        u.firm_role = get_user_role_in_firm(db, u.id, firm_id).value if firm_id and get_user_role_in_firm(db, u.id, firm_id) else "viewer"
    return templates.TemplateResponse(request, "users/list.html", {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "q": q or "",
        "is_active": is_active,
        "user": user,
    })


@router.get("/json", response_model=dict)
def list_users_json(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin)),
):
    items, total = service.list_users(
        db, limit=limit, offset=offset, q=q, is_active=is_active
    )
    return {
        "items": [UserRead.model_validate(u) for u in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/new", response_class=HTMLResponse)
def new_user_form(
    request: Request,
    _=Depends(require_role(TechnicalRole.admin)),
):
    return templates.TemplateResponse(request, "users/form.html", {
        "user_obj": None,
        "action": "/users/new",
        "errors": [],
        "csrf_token": get_csrf_token(request),
        "roles": [r.value for r in TechnicalRole],
    })


@router.post("/new")
async def create_user_form(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin)),
):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    errors = []
    data = {}
    data["email"] = form_data.get("email", "").strip()
    data["display_name"] = form_data.get("display_name", "").strip()
    firm_role = form_data.get("technical_role", "viewer")
    password = form_data.get("password", "").strip()

    if not data["email"]:
        errors.append("Email is required")
    if not data["display_name"]:
        errors.append("Display name is required")
    if password and len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not errors:
        try:
            new_user = service.create_user(db, data, password=password or None)
            # Add user to firm with role
            firm_id = request.session.get("firm_id")
            if firm_id:
                from app.services.firm_service import add_user_to_firm
                from app.models.models import TechnicalRole
                add_user_to_firm(db, new_user.id, firm_id, TechnicalRole(firm_role))
            set_flash(request, f"User '{data['display_name']}' created.")
            return RedirectResponse(url="/users", status_code=303)
        except ValidationError as e:
            errors.append(str(e))

    return templates.TemplateResponse(request, "users/form.html", {
        "user_obj": None,
        "action": "/users/new",
        "errors": errors,
        "csrf_token": get_csrf_token(request),
        "roles": [r.value for r in TechnicalRole],
    })


@router.get("/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin)),
):
    user_obj = service.get_user(db, user_id)
    return templates.TemplateResponse(request, "users/form.html", {
        "user_obj": user_obj,
        "action": f"/users/{user_id}/edit",
        "errors": [],
        "csrf_token": get_csrf_token(request),
        "roles": [r.value for r in TechnicalRole],
    })


@router.post("/{user_id}/edit")
async def update_user_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin)),
):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    errors = []
    data = {}
    data["email"] = form_data.get("email", "").strip()
    data["display_name"] = form_data.get("display_name", "").strip()
    firm_role = form_data.get("technical_role")
    password = form_data.get("password", "").strip()

    if not data["email"]:
        errors.append("Email is required")
    if not data["display_name"]:
        errors.append("Display name is required")
    if password and len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not errors:
        try:
            service.update_user(db, user_id, data)
            if password:
                from app.services.auth_service import set_user_password

                user_obj = service.get_user(db, user_id)
                set_user_password(db, user_obj, password)
            # Update firm role if provided
            if firm_role:
                firm_id = request.session.get("firm_id")
                if firm_id:
                    from app.services.firm_service import update_firm_user_role
                    from app.models.models import TechnicalRole
                    try:
                        update_firm_user_role(db, user_id, firm_id, TechnicalRole(firm_role))
                    except Exception:
                        pass  # User might not be in this firm yet
            set_flash(request, f"User '{data['display_name']}' updated.")
            return RedirectResponse(url="/users", status_code=303)
        except ValidationError as e:
            errors.append(str(e))

    user_obj = service.get_user(db, user_id)
    return templates.TemplateResponse(request, "users/form.html", {
        "user_obj": user_obj,
        "action": f"/users/{user_id}/edit",
        "errors": errors,
        "csrf_token": get_csrf_token(request),
        "roles": [r.value for r in TechnicalRole],
    })


@router.post("/{user_id}/deactivate")
def deactivate_user_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(TechnicalRole.admin)),
):
    if user_id == current_user.id:
        set_flash(request, "You cannot deactivate your own account.", "danger")
        return RedirectResponse(url="/users", status_code=303)
    service.soft_delete_user(db, user_id)
    set_flash(request, "User deactivated.", "warning")
    return RedirectResponse(url="/users", status_code=303)


@router.post("", response_model=UserRead, status_code=201)
def create_user_api(
    data: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin)),
):
    result = service.create_user(db, data.model_dump())
    return UserRead.model_validate(result)


@router.patch("/{user_id}", response_model=UserRead)
def update_user_api(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin)),
):
    result = service.update_user(db, user_id, data.model_dump(exclude_unset=True))
    return UserRead.model_validate(result)
