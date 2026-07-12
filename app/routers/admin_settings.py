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


def _render(request, db, saved=False, error="", approval_saved=False, domains_saved=False):
    """Render the settings page with common context."""
    firm_id = request.session.get("firm_id")
    all_settings = service.list_all_settings(db)
    
    # Get approval rules
    from app.services.approval_service import list_approval_rules
    rules = list_approval_rules(db, firm_id) if firm_id else []
    approval_rules = {}
    for rule in rules:
        key = f"{rule.resource_type.value}_{rule.operation.value}"
        approval_rules[key] = rule.is_enabled

    # Get firm domains
    firm_domains = ""
    if firm_id:
        from app.services.firm_service import get_firm
        firm = get_firm(db, firm_id)
        firm_domains = firm.allowed_domains or ""
    
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse(
        request,
        "admin/settings.html",
        {
            "settings": all_settings,
            "saved": saved,
            "error": error,
            "approval_rules": approval_rules,
            "approval_saved": approval_saved,
            "firm_domains": firm_domains,
            "domains_saved": domains_saved,
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


@router.post("/approval", response_class=HTMLResponse)
async def update_approval_rules(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin)),
):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    firm_id = request.session.get("firm_id")
    if not firm_id:
        # Fallback: get user's first firm from FirmUser table
        from app.services.firm_service import get_user_firms
        user_id = request.session.get("user_id")
        if user_id:
            firms = get_user_firms(db, user_id)
            if firms:
                firm_id = firms[0].id
                request.session["firm_id"] = firm_id
    if not firm_id:
        return _render(request, db, error="No firm selected")

    from app.services.approval_service import upsert_approval_rule
    from app.models.models import ResourceType, OperationType

    resources = ["assignment", "engagement", "client", "team_member", "leave"]
    operations = ["create", "update", "delete"]

    for resource in resources:
        for operation in operations:
            key = f"rule_{resource}_{operation}"
            is_enabled = form_data.get(key) == "on"
            upsert_approval_rule(
                db, firm_id=firm_id,
                resource_type=ResourceType(resource),
                operation=OperationType(operation),
                is_enabled=is_enabled,
            )

    return _render(request, db, approval_saved=True)


@router.post("/domains", response_class=HTMLResponse)
async def update_domains(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin)),
):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    firm_id = request.session.get("firm_id")
    if not firm_id:
        from app.services.firm_service import get_user_firms
        user_id = request.session.get("user_id")
        if user_id:
            firms = get_user_firms(db, user_id)
            if firms:
                firm_id = firms[0].id
                request.session["firm_id"] = firm_id

    if not firm_id:
        return _render(request, db, error="No firm selected")

    from app.services.firm_service import get_firm
    firm = get_firm(db, firm_id)
    firm.allowed_domains = form_data.get("allowed_domains", "").strip()
    db.commit()

    return _render(request, db, domains_saved=True)
