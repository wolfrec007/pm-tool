from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.exceptions import NotFoundError
from app.models.models import Engagement, EngagementInstance


def list_engagements(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    status: Optional[str] = None,
):
    query = db.query(Engagement).options(joinedload(Engagement.client))
    if q:
        query = query.filter(Engagement.name.ilike(f"%{q}%"))
    if is_active is not None:
        query = query.filter(Engagement.is_active == is_active)
    if status:
        query = query.filter(Engagement.status == status)
    total = query.count()
    items = query.order_by(Engagement.name).limit(limit).offset(offset).all()
    return items, total


def get_engagement(db: Session, engagement_id: int) -> Engagement:
    eng = (
        db.query(Engagement)
        .options(joinedload(Engagement.client))
        .filter(Engagement.id == engagement_id)
        .first()
    )
    if not eng:
        raise NotFoundError(f"Engagement {engagement_id} not found")
    return eng


def create_engagement(db: Session, data: dict) -> Engagement:
    eng = Engagement(**data)
    db.add(eng)
    db.commit()
    db.refresh(eng)
    return eng


def update_engagement(db: Session, engagement_id: int, data: dict) -> Engagement:
    eng = get_engagement(db, engagement_id)
    for key, value in data.items():
        if value is not None:
            setattr(eng, key, value)
    db.commit()
    db.refresh(eng)
    return eng


def soft_delete_engagement(db: Session, engagement_id: int) -> Engagement:
    eng = get_engagement(db, engagement_id)
    eng.is_active = False
    db.commit()
    db.refresh(eng)
    return eng


# ── EngagementInstance ──


def list_instances(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    engagement_id: Optional[int] = None,
    status: Optional[str] = None,
):
    query = db.query(EngagementInstance).options(joinedload(EngagementInstance.engagement))
    if engagement_id:
        query = query.filter(EngagementInstance.engagement_id == engagement_id)
    if status:
        query = query.filter(EngagementInstance.status == status)
    total = query.count()
    items = query.order_by(EngagementInstance.start_date.desc()).limit(limit).offset(offset).all()
    return items, total


def get_instance(db: Session, instance_id: int) -> EngagementInstance:
    inst = (
        db.query(EngagementInstance)
        .options(joinedload(EngagementInstance.engagement))
        .filter(EngagementInstance.id == instance_id)
        .first()
    )
    if not inst:
        raise NotFoundError(f"EngagementInstance {instance_id} not found")
    return inst


def create_instance(db: Session, data: dict) -> EngagementInstance:
    inst = EngagementInstance(**data)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def update_instance(db: Session, instance_id: int, data: dict) -> EngagementInstance:
    inst = get_instance(db, instance_id)
    for key, value in data.items():
        if value is not None:
            setattr(inst, key, value)
    db.commit()
    db.refresh(inst)
    return inst
