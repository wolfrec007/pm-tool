from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.auth.auth import get_current_user
from app.database import get_db
from app.models.models import (
    Assignment,
    Client,
    Engagement,
    EngagementInstance,
    FirmUser,
    Leave,
    TeamMember,
    User,
)
from app.services import report_service
from app.templates_setup import templates

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_class=HTMLResponse)
def home_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Dashboard home page with key metrics."""
    today = date.today()
    thirty_days_later = today + timedelta(days=30)

    # Team metrics
    total_members = db.query(func.count(TeamMember.id)).filter(TeamMember.is_active == True).scalar() or 0
    total_admins = db.query(func.count(FirmUser.id)).filter(
        FirmUser.firm_id == request.session.get("firm_id"),
        FirmUser.technical_role == "admin",
        FirmUser.is_active == True,
    ).scalar() or 0

    # Engagement metrics
    active_engagements = db.query(func.count(Engagement.id)).filter(Engagement.status == "active").scalar() or 0
    total_clients = db.query(func.count(Client.id)).filter(Client.is_active == True).scalar() or 0

    # Assignment metrics
    current_assignments = (
        db.query(func.count(Assignment.id))
        .filter(Assignment.start_date <= today, Assignment.end_date >= today)
        .scalar() or 0
    )

    # Bench count (members without current assignment)
    assigned_member_ids = select(Assignment.team_member_id).where(
        Assignment.start_date <= today, Assignment.end_date >= today
    ).distinct()
    bench_count = (
        db.query(func.count(TeamMember.id))
        .filter(TeamMember.is_active == True, TeamMember.id.not_in(assigned_member_ids))
        .scalar() or 0
    )

    # Leave metrics
    pending_leaves = db.query(func.count(Leave.id)).filter(Leave.status == "pending").scalar() or 0
    upcoming_leaves = (
        db.query(func.count(Leave.id))
        .filter(Leave.status == "approved", Leave.start_date > today, Leave.start_date <= thirty_days_later)
        .scalar() or 0
    )

    # Recent assignments (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_assignments = (
        db.query(Assignment)
        .options(
            joinedload(Assignment.team_member),
            joinedload(Assignment.engagement_instance),
        )
        .filter(Assignment.created_at >= week_ago)
        .order_by(Assignment.created_at.desc())
        .limit(5)
        .all()
    )

    return templates.TemplateResponse(request, "dashboard/home.html", {
        "total_members": total_members,
        "total_admins": total_admins,
        "active_engagements": active_engagements,
        "total_clients": total_clients,
        "current_assignments": current_assignments,
        "bench_count": bench_count,
        "pending_leaves": pending_leaves,
        "upcoming_leaves": upcoming_leaves,
        "recent_assignments": recent_assignments,
    })


@router.get("/bench", response_class=HTMLResponse)
def bench_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    items = report_service.get_bench_data(db)
    return templates.TemplateResponse(request, "dashboard/bench.html", {
        "items": items,
    })
