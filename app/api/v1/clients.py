"""API v1 clients endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_firm_user, require_api_role
from app.database import get_db
from app.models.models import FirmUser, TechnicalRole
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["api-v1-clients"])


@router.get("")
def list_clients(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    firm_user: FirmUser = Depends(get_current_firm_user),
    db: Session = Depends(get_db),
):
    items, total = client_service.list_clients(
        db, firm_id=firm_user.firm_id, limit=limit, offset=offset,
        q=q, is_active=is_active,
    )
    return {
        "items": [
            {"id": c.id, "name": c.name, "code": c.code, "industry": c.industry, "is_active": c.is_active}
            for c in items
        ],
        "total": total, "limit": limit, "offset": offset,
    }


@router.get("/{client_id}")
def get_client(
    client_id: int,
    firm_user: FirmUser = Depends(get_current_firm_user),
    db: Session = Depends(get_db),
):
    c = client_service.get_client(db, client_id, firm_id=firm_user.firm_id)
    return {"id": c.id, "name": c.name, "code": c.code, "industry": c.industry, "is_active": c.is_active}


@router.post("", status_code=201)
def create_client(
    body: dict,
    firm_user: FirmUser = Depends(require_api_role(TechnicalRole.admin, TechnicalRole.moderator)),
    db: Session = Depends(get_db),
):
    data = body.copy()
    data["firm_id"] = firm_user.firm_id
    c = client_service.create_client(db, data)
    return {"id": c.id, "name": c.name, "code": c.code}


@router.patch("/{client_id}")
def update_client(
    client_id: int,
    body: dict,
    firm_user: FirmUser = Depends(require_api_role(TechnicalRole.admin, TechnicalRole.moderator)),
    db: Session = Depends(get_db),
):
    c = client_service.update_client(db, client_id, body)
    return {"id": c.id, "name": c.name, "code": c.code}


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    firm_user: FirmUser = Depends(require_api_role(TechnicalRole.admin)),
    db: Session = Depends(get_db),
):
    client_service.soft_delete_client(db, client_id)
    return {"detail": "Client deactivated"}
