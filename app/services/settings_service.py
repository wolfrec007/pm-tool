from typing import Optional

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.models import SystemSetting


def get_setting(db: Session, key: str) -> Optional[SystemSetting]:
    return db.query(SystemSetting).filter(SystemSetting.key == key).first()


def get_setting_value(db: Session, key: str, default: str = "") -> str:
    setting = get_setting(db, key)
    return setting.value if setting else default


def update_setting(db: Session, key: str, value: str, updated_by_user_id: Optional[int] = None):
    setting = get_setting(db, key)
    if not setting:
        raise NotFoundError(f"Setting '{key}' not found")
    setting.value = value
    setting.updated_by_user_id = updated_by_user_id
    db.commit()
    db.refresh(setting)
    return setting


def list_all_settings(db: Session):
    return db.query(SystemSetting).order_by(SystemSetting.key).all()
