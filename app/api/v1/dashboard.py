"""API v1 dashboard endpoint — returns stats as JSON."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_firm_user
from app.database import get_db
from app.models.models import (
    Assignment, Client, Engagement, FirmUser, Leave, TeamMember,
)

router = APIRouter(prefix="/dashboard", tags=["api-v1-dashboard"])


@router.get("")
def get_dashboard_stats(
    firm_user: FirmUser = Depends(get_current_firm_user),
    db: Session = Depends(get_db),
):
    """Return dashboard statistics for the current firm."""
    firm_id = firm_user.firm_id
    today = date.today()
    thirty_days_later = today + timedelta(days=30)

    total_members = db.query(func.count(TeamMember.id)).filter(
        TeamMember.firm_id == firm_id, TeamMember.is_active == True
    ).scalar() or 0

    total_clients = db.query(func.count(Client.id)).filter(
        Client.firm_id == firm_id, Client.is_active == True
    ).scalar() or 0

    # Engagements through clients
    from app.models.models import Engagement as EngModel, Client as ClientModel
    active_engagements = db.query(func.count(EngModel.id)).join(
        ClientModel, EngModel.client_id == ClientModel.id
    ).filter(
        ClientModel.firm_id == firm_id, EngModel.status == "active"
    ).scalar() or 0

    # Current assignments (through team_members)
    current_assignments = db.query(func.count(Assignment.id)).join(
        TeamMember, Assignment.team_member_id == TeamMember.id
    ).filter(
        TeamMember.firm_id == firm_id,
        Assignment.start_date <= today,
        Assignment.end_date >= today,
    ).scalar() or 0

    # Bench count
    assigned_ids = select(Assignment.team_member_id).where(
        Assignment.start_date <= today,
        Assignment.end_date >= today,
    ).distinct()
    bench_count = db.query(func.count(TeamMember.id)).filter(
        TeamMember.firm_id == firm_id,
        TeamMember.is_active == True,
        TeamMember.id.not_in(assigned_ids),
    ).scalar() or 0

    # Leaves
    pending_leaves = db.query(func.count(Leave.id)).join(
        TeamMember, Leave.team_member_id == TeamMember.id
    ).filter(
        TeamMember.firm_id == firm_id, Leave.status == "pending"
    ).scalar() or 0

    upcoming_leaves = db.query(func.count(Leave.id)).join(
        TeamMember, Leave.team_member_id == TeamMember.id
    ).filter(
        TeamMember.firm_id == firm_id,
        Leave.status == "approved",
        Leave.start_date > today,
        Leave.start_date <= thirty_days_later,
    ).scalar() or 0

    return {
        "total_members": total_members,
        "total_clients": total_clients,
        "active_engagements": active_engagements,
        "current_assignments": current_assignments,
        "bench_count": bench_count,
        "pending_leaves": pending_leaves,
        "upcoming_leaves": upcoming_leaves,
    }
