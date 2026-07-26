"""Reports router — view and export reports."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.csrf_utils import get_csrf_token
from app.database import get_db
from app.models.models import User, TechnicalRole
from app.services import report_service
from app.templates_setup import templates

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_firm_id(request: Request) -> int | None:
    return request.session.get("firm_id")


def _get_user_role(request: Request) -> str:
    return request.session.get("user_role", "viewer")


@router.get("", response_class=HTMLResponse)
def reports_index(
    request: Request,
    _=Depends(get_current_user),
):
    """List available reports for current user's role."""
    user_role = _get_user_role(request)
    available = report_service.list_available_reports(user_role)
    
    return templates.TemplateResponse(request, "reports/index.html", {
        "csrf_token": get_csrf_token(request),
        "reports": available,
        "user_role": user_role,
    })


@router.get("/{report_name}", response_class=HTMLResponse)
def view_report(
    report_name: str,
    request: Request,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    business_role: Optional[str] = Query(None),
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View a report."""
    user_role = _get_user_role(request)
    firm_id = _get_firm_id(request)
    
    if not firm_id:
        return HTMLResponse("No firm selected", status_code=400)
    
    if not report_service.check_report_access(user_role, report_name):
        raise HTTPException(status_code=403, detail="Insufficient permissions for this report")
    
    # Build filters
    filters = {}
    if start_date:
        filters["start_date"] = date.fromisoformat(start_date)
    if end_date:
        filters["end_date"] = date.fromisoformat(end_date)
    if business_role:
        filters["business_role"] = business_role
    
    report = report_service.generate_report(db, firm_id, report_name, filters)
    
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    
    # Get available business roles for filter
    from app.models.firm_business_role import FirmBusinessRole
    roles = db.query(FirmBusinessRole).filter(
        FirmBusinessRole.firm_id == firm_id,
        FirmBusinessRole.is_enabled == True,
    ).all()
    
    return templates.TemplateResponse(request, "reports/view.html", {
        "csrf_token": get_csrf_token(request),
        "report": report,
        "report_name": report_name,
        "filters": filters,
        "business_roles": roles,
        "user_role": user_role,
    })


@router.get("/{report_name}/download")
def download_report(
    report_name: str,
    request: Request,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    business_role: Optional[str] = Query(None),
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download report as CSV."""
    user_role = _get_user_role(request)
    firm_id = _get_firm_id(request)
    
    if not firm_id:
        raise HTTPException(status_code=400, detail="No firm selected")
    
    if not report_service.check_report_access(user_role, report_name):
        raise HTTPException(status_code=403, detail="Insufficient permissions for this report")
    
    filters = {}
    if start_date:
        filters["start_date"] = date.fromisoformat(start_date)
    if end_date:
        filters["end_date"] = date.fromisoformat(end_date)
    if business_role:
        filters["business_role"] = business_role
    
    return StreamingResponse(
        report_service.stream_report_csv(db, firm_id, report_name, filters),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_name}.csv"},
    )
