import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth.auth import require_role
from app.csrf_utils import get_csrf_token, validate_csrf
from app.database import get_db
from app.exceptions import NotFoundError
from app.flash import set_flash
from app.models.models import TechnicalRole
from app.schemas.schemas import SystemSettingRead, SystemSettingUpdate
from app.services import settings_service as service
from app.templates_setup import templates

router = APIRouter(prefix="/admin/settings", tags=["settings"])


def _render(request, db, saved=False, error=""):
    """Render the settings page with common context."""
    all_settings = service.list_all_settings(db)
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse(
        request,
        "admin/settings.html",
        {
            "settings": all_settings,
            "saved": saved,
            "error": error,
            "csrf_token": csrf_token,
        },
    )


@router.get("", response_class=HTMLResponse)
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin)),
):
    return _render(request, db)


@router.get("/list", response_model=list[SystemSettingRead])
def list_settings_api(
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin)),
):
    return [SystemSettingRead.model_validate(s) for s in service.list_all_settings(db)]


@router.post("", response_class=HTMLResponse)
async def update_settings(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin)),
):
    form_data = await request.form()

    # CSRF validation
    token = form_data.get("csrf_token")
    if not validate_csrf(request, token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    all_settings = service.list_all_settings(db)
    saved = False
    error = ""

    try:
        for setting in all_settings:
            if setting.key in form_data:
                service.update_setting(
                    db, setting.key, form_data[setting.key], updated_by_user_id=user.id
                )
        saved = True
    except NotFoundError as e:
        error = str(e)
    except Exception as e:
        error = f"Failed to save settings: {e!s}"

    return _render(request, db, saved=saved, error=error)


@router.post("/api", response_model=SystemSettingRead)
def update_setting_api(
    key: str,
    data: SystemSettingUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin)),
):
    result = service.update_setting(db, key, data.value, updated_by_user_id=user.id)
    return SystemSettingRead.model_validate(result)
