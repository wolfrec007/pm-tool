"""Firm, Branch, and FirmUser service layer."""

from typing import Optional

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ValidationError
from app.models.models import Firm, Branch, FirmUser, TechnicalRole


# ── Firm ──

def list_firms(db: Session, is_active: bool = True) -> list[Firm]:
    q = db.query(Firm)
    if is_active is not None:
        q = q.filter(Firm.is_active == is_active)
    return q.order_by(Firm.name).all()


def get_firm(db: Session, firm_id: int) -> Firm:
    firm = db.query(Firm).filter(Firm.id == firm_id).first()
    if not firm:
        raise NotFoundError(f"Firm {firm_id} not found")
    return firm


def create_firm(db: Session, name: str, code: str, logo_url: str | None = None) -> Firm:
    if db.query(Firm).filter(Firm.code == code).first():
        raise ValidationError(f"Firm with code '{code}' already exists")
    firm = Firm(name=name, code=code, logo_url=logo_url)
    db.add(firm)
    db.commit()
    db.refresh(firm)
    return firm


def update_firm(db: Session, firm_id: int, **kwargs) -> Firm:
    firm = get_firm(db, firm_id)
    for k, v in kwargs.items():
        if v is not None and hasattr(firm, k):
            setattr(firm, k, v)
    db.commit()
    db.refresh(firm)
    return firm


# ── Branch ──

def list_branches(db: Session, firm_id: int, is_active: bool | None = True) -> list[Branch]:
    q = db.query(Branch).filter(Branch.firm_id == firm_id)
    if is_active is not None:
        q = q.filter(Branch.is_active == is_active)
    return q.order_by(Branch.name).all()


def get_branch(db: Session, branch_id: int, firm_id: int | None = None) -> Branch:
    q = db.query(Branch).filter(Branch.id == branch_id)
    if firm_id is not None:
        q = q.filter(Branch.firm_id == firm_id)
    branch = q.first()
    if not branch:
        raise NotFoundError(f"Branch {branch_id} not found")
    return branch


def create_branch(db: Session, firm_id: int, name: str, code: str | None = None,
                  city: str | None = None, address: str | None = None) -> Branch:
    branch = Branch(firm_id=firm_id, name=name, code=code, city=city, address=address)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def update_branch(db: Session, branch_id: int, **kwargs) -> Branch:
    branch = get_branch(db, branch_id)
    for k, v in kwargs.items():
        if v is not None and hasattr(branch, k):
            setattr(branch, k, v)
    db.commit()
    db.refresh(branch)
    return branch


def soft_delete_branch(db: Session, branch_id: int) -> Branch:
    branch = get_branch(db, branch_id)
    branch.is_active = False
    db.commit()
    db.refresh(branch)
    return branch


# ── FirmUser ──

def list_firm_users(db: Session, firm_id: int) -> list[FirmUser]:
    return db.query(FirmUser).filter(
        FirmUser.firm_id == firm_id,
        FirmUser.is_active == True,
    ).all()


def get_firm_user(db: Session, user_id: int, firm_id: int) -> FirmUser | None:
    return db.query(FirmUser).filter(
        FirmUser.user_id == user_id,
        FirmUser.firm_id == firm_id,
    ).first()


def add_user_to_firm(db: Session, user_id: int, firm_id: int,
                     role: TechnicalRole = TechnicalRole.viewer) -> FirmUser:
    existing = get_firm_user(db, user_id, firm_id)
    if existing:
        if existing.is_active:
            raise ValidationError(f"User {user_id} is already in firm {firm_id}")
        existing.is_active = True
        existing.technical_role = role
        db.commit()
        db.refresh(existing)
        return existing

    firm_user = FirmUser(user_id=user_id, firm_id=firm_id, technical_role=role)
    db.add(firm_user)
    db.commit()
    db.refresh(firm_user)
    return firm_user


def update_firm_user_role(db: Session, user_id: int, firm_id: int,
                          role: TechnicalRole) -> FirmUser:
    firm_user = get_firm_user(db, user_id, firm_id)
    if not firm_user:
        raise NotFoundError(f"User {user_id} not found in firm {firm_id}")
    firm_user.technical_role = role
    db.commit()
    db.refresh(firm_user)
    return firm_user


def remove_user_from_firm(db: Session, user_id: int, firm_id: int) -> None:
    firm_user = get_firm_user(db, user_id, firm_id)
    if firm_user:
        firm_user.is_active = False
        db.commit()


def get_user_firms(db: Session, user_id: int) -> list[Firm]:
    """Get all active firms a user belongs to."""
    firm_users = db.query(FirmUser).filter(
        FirmUser.user_id == user_id,
        FirmUser.is_active == True,
    ).all()
    firm_ids = [fu.firm_id for fu in firm_users]
    return db.query(Firm).filter(Firm.id.in_(firm_ids), Firm.is_active == True).all()


def get_user_role_in_firm(db: Session, user_id: int, firm_id: int) -> TechnicalRole | None:
    """Get user's role in a specific firm."""
    fu = get_firm_user(db, user_id, firm_id)
    return fu.technical_role if fu and fu.is_active else None
