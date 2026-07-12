from typing import Optional

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.models import SystemSetting


def get_setting(db: Session, key: str, firm_id: int | None = None) -> Optional[SystemSetting]:
    """Get a setting. If firm_id provided, returns firm-specific or global (NULL firm_id) setting."""
    query = db.query(SystemSetting).filter(SystemSetting.key == key)
    if firm_id is not None:
        # Prefer firm-specific, fallback to global
        setting = query.filter(SystemSetting.firm_id == firm_id).first()
        if setting:
            return setting
        return query.filter(SystemSetting.firm_id.is_(None)).first()
    return query.first()


def get_setting_value(db: Session, key: str, firm_id: int | None = None, default: str = "") -> str:
    setting = get_setting(db, key, firm_id)
    return setting.value if setting else default


def update_setting(db: Session, key: str, value: str, updated_by_user_id: Optional[int] = None,
                   firm_id: int | None = None):
    setting = get_setting(db, key, firm_id)
    if not setting:
        # Create firm-specific setting
        setting = SystemSetting(key=key, value=value, firm_id=firm_id, updated_by_user_id=updated_by_user_id)
        db.add(setting)
    else:
        setting.value = value
        setting.updated_by_user_id = updated_by_user_id
    db.commit()
    db.refresh(setting)
    return setting


def list_all_settings(db: Session, firm_id: int | None = None):
    """List settings: firm-specific + global (NULL firm_id)."""
    query = db.query(SystemSetting)
    if firm_id is not None:
        from sqlalchemy import or_
        query = query.filter(or_(
            SystemSetting.firm_id == firm_id,
            SystemSetting.firm_id.is_(None),
        ))
    return query.order_by(SystemSetting.key).all()
