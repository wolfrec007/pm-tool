from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user, require_role
from app.csrf_utils import get_csrf_token, validate_csrf
from app.database import get_db
from app.exceptions import ConflictWithLeaveError, NotFoundError, OverAllocationError, ValidationError
from app.flash import set_flash
from app.models.models import TechnicalRole
from app.schemas.schemas import AssignmentCreate, AssignmentRead, AssignmentUpdate
from app.services import allocation_service as service
from app.services import team_member_service, engagement_service
from app.templates_setup import templates

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _handle_conflict(e: Exception):
    if isinstance(e, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, (OverAllocationError, ConflictWithLeaveError)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if isinstance(e, ValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    raise


@router.get("", response_class=HTMLResponse)
def list_assignments(
    request: Request,
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    team_member_id: Optional[int] = None, engagement_instance_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin, TechnicalRole.moderator, TechnicalRole.viewer)),
):
    items, total = service.list_assignments(
        db, limit=limit, offset=offset, team_member_id=team_member_id, engagement_instance_id=engagement_instance_id
    )
    return templates.TemplateResponse(request, "assignments/list.html", {
        "items": items, "total": total, "limit": limit, "offset": offset,
        "user": user,
    })


@router.get("/assign-staff", response_class=HTMLResponse)
def assign_staff_page(
    request: Request,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin, TechnicalRole.moderator)),
):
    members, _ = team_member_service.list_team_members(db, limit=200, is_active=True, q=q)
    allocations = service.get_member_allocations(db)
    return templates.TemplateResponse(request, "assignments/assign_staff.html", {
        "members": members,
        "allocations": allocations,
        "q": q or "",
        "user": user,
        "csrf_token": get_csrf_token(request),
    })


@router.get("/json", response_model=dict)
def list_assignments_json(
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    team_member_id: Optional[int] = None, engagement_instance_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin, TechnicalRole.moderator, TechnicalRole.viewer)),
):
    items, total = service.list_assignments(
        db, limit=limit, offset=offset, team_member_id=team_member_id, engagement_instance_id=engagement_instance_id
    )
    return {"items": [AssignmentRead.model_validate(a) for a in items], "total": total, "limit": limit, "offset": offset}


@router.get("/new", response_class=HTMLResponse)
def new_assignment_form(
    request: Request, db: Session = Depends(get_db),
    member_id: Optional[int] = None,
    _=Depends(require_role(TechnicalRole.admin, TechnicalRole.moderator)),
):
    members, _ = team_member_service.list_team_members(db, limit=200, is_active=True)
    instances, _ = engagement_service.list_instances(db, limit=200)
    return templates.TemplateResponse(request, "assignments/form.html", {
        "assignment": None, "action": "/assignments/new", "errors": [],
        "members": members,
        "instances": instances,
        "preselected_member_id": member_id,
        "csrf_token": get_csrf_token(request),
    })


@router.post("/new")
async def create_assignment_form(
    request: Request, db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin, TechnicalRole.moderator)),
):
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    errors = []
    try:
        result = service.create_assignment(
            db,
            team_member_id=int(form_data["team_member_id"]),
            engagement_instance_id=int(form_data["engagement_instance_id"]),
            allocation_percent=int(form_data["allocation_percent"]),
            start_date=form_data["start_date"],
            end_date=form_data["end_date"],
            role_on_engagement=form_data.get("role_on_engagement", "").strip() or None,
            created_by_user_id=user.id,
        )
        set_flash(request, f"Assignment created ({result.allocation_percent}% allocation).")
        return RedirectResponse(url="/assignments", status_code=303)
    except (OverAllocationError, ConflictWithLeaveError, ValidationError, NotFoundError) as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(str(e))

    members, _ = team_member_service.list_team_members(db, limit=200, is_active=True)
    instances, _ = engagement_service.list_instances(db, limit=200)
    return templates.TemplateResponse(request, "assignments/form.html", {
        "assignment": None, "action": "/assignments/new", "errors": errors,
        "members": members, "instances": instances,
        "preselected_member_id": None,
        "csrf_token": get_csrf_token(request),
    })


@router.post("", response_model=AssignmentRead, status_code=201)
def create_assignment_api(
    data: AssignmentCreate, db: Session = Depends(get_db),
    user=Depends(require_role(TechnicalRole.admin, TechnicalRole.moderator)),
):
    try:
        result = service.create_assignment(
            db, team_member_id=data.team_member_id, engagement_instance_id=data.engagement_instance_id,
            allocation_percent=data.allocation_percent, start_date=data.start_date, end_date=data.end_date,
            role_on_engagement=data.role_on_engagement, created_by_user_id=user.id,
        )
        return AssignmentRead.model_validate(result)
    except Exception as e:
        _handle_conflict(e)


@router.patch("/{assignment_id}", response_model=AssignmentRead)
def update_assignment_api(
    assignment_id: int, data: AssignmentUpdate, db: Session = Depends(get_db),
    _=Depends(require_role(TechnicalRole.admin, TechnicalRole.moderator)),
):
    try:
        result = service.update_assignment(
            db, assignment_id=assignment_id, allocation_percent=data.allocation_percent,
            start_date=data.start_date, end_date=data.end_date, role_on_engagement=data.role_on_engagement,
        )
        return AssignmentRead.model_validate(result)
    except Exception as e:
        _handle_conflict(e)
