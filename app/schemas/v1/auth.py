"""Pydantic schemas for auth API endpoints."""

from pydantic import BaseModel, EmailStr

from app.schemas.base import ORMModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(ORMModel):
    id: int
    email: str
    display_name: str
    is_active: bool


class FirmResponse(ORMModel):
    id: int
    name: str
    code: str
    logo_url: str | None = None


class FirmUserResponse(ORMModel):
    firm: FirmResponse
    role: str


class MeResponse(BaseModel):
    user: UserResponse
    firms: list[FirmUserResponse]
    active_firm_id: int | None = None


class FirmSwitchRequest(BaseModel):
    firm_id: int
