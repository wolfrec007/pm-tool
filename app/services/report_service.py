import csv
import io
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.models import Assignment, TeamMember


def stream_allocation_csv(db: Session):
    """Generator that yields CSV rows as strings, streaming from DB."""
    yield "Team Member,Email,Business Role,Engagement,Period,Allocation %,Start Date,End Date\n"

    query = (
        db.query(Assignment)
        .options(
            joinedload(Assignment.team_member),
            joinedload(Assignment.engagement_instance).joinedload(
                Assignment.engagement_instance.engagement  # type: ignore
            ),
        )
        .order_by(Assignment.team_member_id, Assignment.start_date)
    )

    for batch in query.yield_per(500):
        for a in batch:
            tm = a.team_member
            instance = a.engagement_instance
            eng = instance.engagement if instance else None
            yield (
                f"{tm.name},{tm.email},{tm.business_role.value if tm.business_role else ''},"
                f"{eng.name if eng else ''},{instance.period_label if instance else ''},"
                f"{a.allocation_percent},{a.start_date},{a.end_date}\n"
            )


def get_bench_data(db: Session):
    """Return team members currently on bench and those rolling off soon."""
    rolloff_days = settings.DEFAULT_BENCH_ROLLOFF_DAYS
    # Try reading from system settings
    from app.models.models import SystemSetting

    setting = db.query(SystemSetting).filter(SystemSetting.key == "bench_rolloff_days").first()
    if setting:
        try:
            rolloff_days = int(setting.value)
        except (ValueError, TypeError):
            pass

    today = date.today()
    rolling_off_threshold = today + timedelta(days=rolloff_days)

    # Subquery: latest assignment end date per team member
    latest_assignment = (
        db.query(
            Assignment.team_member_id,
            func.max(Assignment.end_date).label("last_end"),
        )
        .group_by(Assignment.team_member_id)
        .subquery()
    )

    members = (
        db.query(TeamMember, latest_assignment.c.last_end)
        .outerjoin(
            latest_assignment,
            TeamMember.id == latest_assignment.c.team_member_id,
        )
        .filter(TeamMember.is_active == True)
        .order_by(TeamMember.name)
        .all()
    )

    bench_items = []
    for member, last_end in members:
        if last_end is None or last_end < today:
            # Currently on bench
            days_since = (today - last_end).days if last_end else None
            is_rolling = (
                last_end is not None
                and last_end >= today
                and last_end <= rolling_off_threshold
            )
            bench_items.append(
                {
                    "team_member_id": member.id,
                    "name": member.name,
                    "business_role": member.business_role.value,
                    "last_assignment_end": last_end,
                    "days_since_last_assignment": days_since,
                    "is_rolling_off": bool(is_rolling),
                }
            )

    return bench_items
