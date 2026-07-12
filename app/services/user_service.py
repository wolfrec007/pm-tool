from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ValidationError
from app.models.models import User
from app.services.auth_service import hash_password


def list_users(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    query = db.query(User)
    if q:
        query = query.filter(
            or_(
                User.email.ilike(f"%{q}%"),
                User.display_name.ilike(f"%{q}%"),
            )
        )
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    total = query.count()
    items = query.order_by(User.display_name).limit(limit).offset(offset).all()
    return items, total


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    return user


def create_user(db: Session, data: dict, password: Optional[str] = None) -> User:
    if not data.get("email"):
        raise ValidationError("Email is required")
    existing = db.query(User).filter(User.email == data["email"]).first()
    if existing:
        raise ValidationError(f"User with email {data['email']} already exists")
    user = User(**data)
    if password:
        user.password_hash = hash_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, data: dict) -> User:
    user = get_user(db, user_id)
    if "email" in data and data["email"]:
        existing = db.query(User).filter(User.email == data["email"], User.id != user_id).first()
        if existing:
            raise ValidationError(f"Email {data['email']} is already taken")
    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def soft_delete_user(db: Session, user_id: int) -> User:
    user = get_user(db, user_id)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
