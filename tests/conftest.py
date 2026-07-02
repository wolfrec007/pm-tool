"""Test configuration — cleans up test data after each test."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, get_db
from app.main import app
from app.models.models import (
    Assignment,
    BusinessRole,
    Client,
    EmailOutbox,
    Engagement,
    EngagementInstance,
    EngagementStatus,
    EngagementType,
    InstanceStatus,
    Leave,
    RecurrencePattern,
    SystemSetting,
    TeamMember,
    TechnicalRole,
    User,
)


@pytest.fixture(autouse=True)
def clean_tables():
    """Clean up test data after each test."""
    yield
    db = SessionLocal()
    try:
        db.query(EmailOutbox).delete()
        db.query(Leave).delete()
        db.query(Assignment).delete()
        db.query(EngagementInstance).delete()
        db.query(Engagement).delete()
        db.query(Client).delete()
        db.query(TeamMember).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_user(db):
    user = User(
        email="admin@test.com",
        display_name="Admin User",
        technical_role=TechnicalRole.admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def moderator_user(db):
    user = User(
        email="moderator@test.com",
        display_name="Mod User",
        technical_role=TechnicalRole.moderator,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def viewer_user(db):
    user = User(
        email="viewer@test.com",
        display_name="Viewer User",
        technical_role=TechnicalRole.viewer,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def team_member(db):
    tm = TeamMember(
        name="John Doe",
        email="john@test.com",
        technical_role=TechnicalRole.viewer,
        business_role=BusinessRole.staff,
        is_active=True,
    )
    db.add(tm)
    db.commit()
    db.refresh(tm)
    return tm


@pytest.fixture
def client_fixture(db):
    c = Client(name="Test Client", is_active=True)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def engagement(db, client_fixture):
    eng = Engagement(
        client_id=client_fixture.id,
        name="Test Engagement",
        engagement_type=EngagementType.statutory_audit,
        recurrence_pattern=RecurrencePattern.quarterly,
        start_date=date.today(),
        status=EngagementStatus.active,
        is_active=True,
    )
    db.add(eng)
    db.commit()
    db.refresh(eng)
    return eng


@pytest.fixture
def instance(db, engagement):
    inst = EngagementInstance(
        engagement_id=engagement.id,
        period_label="Q1 2026",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        status=InstanceStatus.planned,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst
