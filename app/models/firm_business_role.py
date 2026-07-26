"""Firm-specific business role configuration with cost rates."""

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String,
    UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class FirmBusinessRole(Base):
    """Per-firm configuration for business roles (enable/disable + cost rate)."""
    __tablename__ = "firm_business_roles"

    id = Column(Integer, primary_key=True, index=True)
    firm_id = Column(Integer, ForeignKey("firms.id", ondelete="CASCADE"), nullable=False)
    role_code = Column(String(50), nullable=False)  # From BusinessRole enum
    is_enabled = Column(Boolean, default=True, nullable=False)
    rate_type = Column(String(10), nullable=True)  # "hourly" or "daily"
    rate_value = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    firm = relationship("Firm")

    __table_args__ = (
        UniqueConstraint("firm_id", "role_code", name="uq_firm_business_role"),
    )
