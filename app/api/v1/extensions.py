"""API v1 extension request endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_firm_user, require_api_role
from app.database import get_db
from app.models.models import FirmUser, TechnicalRole
from app.services import extension_service

router = APIRouter(prefix="/extensions", tags=["api-v1-extensions"])


class ExtensionRequest(BaseModel):
    team_member_id: int
    engagement_instance_id: int
    allocation_percent: int
    start_date: str
    end_date: str
    role_on_engagement: Optional[str] = None
    reason: Optional[str] = None


class ReviewNote(BaseModel):
    note: Optional[str] = None


@router.get("")
def list_extensions(
    status: Optional[str] = Query(None),
    firm_user: FirmUser = Depends(get_current_firm_user),
    db: Session = Depends(get_db),
):
    """List extension requests for the firm."""
    items = extension_service.list_extension_requests(db, firm_user.firm_id, status=status)
    return {
        "items": [
            {
                "id": e.id,
                "team_member_id": e.team_member_id,
                "team_member_name": e.team_member.name if e.team_member else None,
                "engagement_instance_id": e.engagement_instance_id,
                "allocation_percent": e.allocation_percent,
                "start_date": str(e.start_date),
                "end_date": str(e.end_date),
                "role_on_engagement": e.role_on_engagement,
                "reason": e.reason,
                "status": e.status.value,
                "requested_by": e.requested_by.display_name if e.requested_by else None,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in items
        ],
        "total": len(items),
    }


@router.post("", status_code=201)
def create_extension(
    body: ExtensionRequest,
    firm_user: FirmUser = Depends(get_current_firm_user),
    db: Session = Depends(get_db),
):
    """Submit an extension request for additional allocation."""
    from datetime import date as _date
    ext = extension_service.create_extension_request(
        db=db,
        firm_id=firm_user.firm_id,
        user_id=firm_user.user_id,
        team_member_id=body.team_member_id,
        engagement_instance_id=body.engagement_instance_id,
        allocation_percent=body.allocation_percent,
        start_date=_date.fromisoformat(body.start_date),
        end_date=_date.fromisoformat(body.end_date),
        role_on_engagement=body.role_on_engagement,
        reason=body.reason,
    )
    return {
        "id": ext.id,
        "status": "pending",
        "message": "Extension request submitted for approval",
    }


@router.post("/{request_id}/approve")
def approve_extension(
    request_id: int,
    body: ReviewNote | None = None,
    firm_user: FirmUser = Depends(require_api_role(TechnicalRole.admin)),
    db: Session = Depends(get_db),
):
    """Approve an extension request and create the assignment."""
    note = body.note if body else None
    ext = extension_service.approve_extension(db, request_id, firm_user.user_id, note)
    return {
        "id": ext.id,
        "status": "approved",
        "detail": "Extension approved and assignment created",
    }


@router.post("/{request_id}/reject")
def reject_extension(
    request_id: int,
    body: ReviewNote | None = None,
    firm_user: FirmUser = Depends(require_api_role(TechnicalRole.admin)),
    db: Session = Depends(get_db),
):
    """Reject an extension request."""
    note = body.note if body else None
    ext = extension_service.reject_extension(db, request_id, firm_user.user_id, note)
    return {
        "id": ext.id,
        "status": "rejected",
        "detail": "Extension rejected",
    }
