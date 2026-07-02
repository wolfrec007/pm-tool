import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class TechnicalRole(str, enum.Enum):
    admin = "admin"
    moderator = "moderator"
    viewer = "viewer"


class BusinessRole(str, enum.Enum):
    partner = "partner"
    director = "director"
    ca_manager = "ca_manager"
    paid_assistant = "paid_assistant"
    staff = "staff"
    article = "article"
    data_analyst = "data_analyst"


class EngagementType(str, enum.Enum):
    statutory_audit = "statutory_audit"
    internal_audit = "internal_audit"
    tax_audit = "tax_audit"
    consulting = "consulting"
    special_assignment = "special_assignment"
    other = "other"


class RecurrencePattern(str, enum.Enum):
    one_off = "one_off"
    weekly = "weekly"
    fortnightly = "fortnightly"
    monthly = "monthly"
    quarterly = "quarterly"
    annual = "annual"


class EngagementStatus(str, enum.Enum):
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    lost_client = "lost_client"


class InstanceStatus(str, enum.Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    delayed = "delayed"


class LeaveType(str, enum.Enum):
    sick = "sick"
    vacation = "vacation"
    exam_leave = "exam_leave"
    other = "other"


class LeaveStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False)
    technical_role = Column(Enum(TechnicalRole), nullable=False, default=TechnicalRole.viewer)
    is_active = Column(Boolean, default=True, nullable=False)
    azure_oid = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True, nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    technical_role = Column(Enum(TechnicalRole), nullable=False, default=TechnicalRole.viewer)
    business_role = Column(Enum(BusinessRole), nullable=False)
    is_oversight_only = Column(Boolean, default=False, nullable=False)
    seniority_level = Column(String(100), nullable=True)
    date_of_joining = Column(Date, nullable=True)
    date_of_relieving = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    assignments = relationship("Assignment", back_populates="team_member")
    leaves = relationship("Leave", back_populates="team_member")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=True)
    industry = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    engagements = relationship("Engagement", back_populates="client")


class Engagement(Base):
    __tablename__ = "engagements"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(255), nullable=False)
    engagement_type = Column(Enum(EngagementType), nullable=False)
    recurrence_pattern = Column(Enum(RecurrencePattern), nullable=False)
    default_team_template_json = Column(JSON, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    status = Column(Enum(EngagementStatus), nullable=False, default=EngagementStatus.active)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    client = relationship("Client", back_populates="engagements")
    instances = relationship("EngagementInstance", back_populates="engagement")


class EngagementInstance(Base):
    __tablename__ = "engagement_instances"

    id = Column(Integer, primary_key=True, index=True)
    engagement_id = Column(
        Integer, ForeignKey("engagements.id", ondelete="RESTRICT"), nullable=False
    )
    period_label = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(Enum(InstanceStatus), nullable=False, default=InstanceStatus.planned)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    engagement = relationship("Engagement", back_populates="instances")
    assignments = relationship("Assignment", back_populates="engagement_instance")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    team_member_id = Column(
        Integer, ForeignKey("team_members.id", ondelete="RESTRICT"), nullable=False
    )
    engagement_instance_id = Column(
        Integer, ForeignKey("engagement_instances.id", ondelete="RESTRICT"), nullable=False
    )
    role_on_engagement = Column(String(255), nullable=True)
    allocation_percent = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    team_member = relationship("TeamMember", back_populates="assignments")
    engagement_instance = relationship("EngagementInstance", back_populates="assignments")
    created_by = relationship("User")

    __table_args__ = (
        Index("ix_assignment_team_member_dates", "team_member_id", "start_date", "end_date"),
        Index("ix_assignment_instance", "engagement_instance_id"),
        Index("ix_assignment_team_instance", "team_member_id", "engagement_instance_id"),
    )


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    team_member_id = Column(
        Integer, ForeignKey("team_members.id", ondelete="RESTRICT"), nullable=False
    )
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(LeaveStatus), nullable=False, default=LeaveStatus.pending)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    team_member = relationship("TeamMember", back_populates="leaves")

    __table_args__ = (Index("ix_leave_team_member_dates", "team_member_id", "start_date", "end_date"),)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EmailOutbox(Base):
    __tablename__ = "email_outbox"

    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    assignment_id = Column(
        Integer, ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)
