"""Approval check helper — used by both web and API v1 endpoints.

Usage in a route:
    result = check_approval(db, firm_id, user_id, ResourceType.assignment, OperationType.create, payload)
    if result:
        return result  # Returns 202 with pending request
    # Otherwise, apply the change directly
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.models.models import ResourceType, OperationType
from app.services.approval_service import check_approval_needed, create_approval_request


def check_approval(
    db: Session,
    firm_id: int,
    user_id: int,
    resource_type: ResourceType,
    operation: OperationType,
    payload: dict[str, Any],
    resource_id: int | None = None,
) -> JSONResponse | None:
    """Check if approval is needed. If yes, create pending request and return 202 response.

    Returns None if approval is not needed (proceed with the operation).
    Returns JSONResponse with 202 if approval is required.
    """
    if not check_approval_needed(db, firm_id, resource_type, operation):
        return None

    req = create_approval_request(
        db=db,
        firm_id=firm_id,
        resource_type=resource_type,
        operation=operation,
        user_id=user_id,
        payload=payload,
        resource_id=resource_id,
    )

    return JSONResponse(
        status_code=202,
        content={
            "status": "pending_approval",
            "request_id": req.id,
            "message": f"{resource_type.value} {operation.value} requires approval",
        },
    )
