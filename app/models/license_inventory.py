"""LicenseInventory model — stored license keys for dev portal management."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from app.database import Base


class LicenseInventory(Base):
    __tablename__ = "license_inventory"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(255), unique=True, nullable=False)
    license_key_hash = Column(String(255), unique=True, nullable=False)
    tier = Column(String(50), nullable=False)
    duration_days = Column(Integer, nullable=False)
    status = Column(String(50), default="available", nullable=False)
    note = Column(Text, nullable=True)
    assigned_firm_id = Column(Integer, ForeignKey("firms.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    generated_by_id = Column(Integer, ForeignKey("super_admins.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
