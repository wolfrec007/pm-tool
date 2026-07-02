"""Tests for DIY auth — password login, 2FA, OAuth skeleton, password change."""

from unittest.mock import patch

import pyotp
import pytest
from sqlalchemy.orm import Session

from app.models.models import TechnicalRole, User
from app.services.auth_service import (
    authenticate_user,
    disable_totp,
    enable_totp,
    find_or_create_oauth_user,
    generate_totp_secret,
    get_totp_uri,
    hash_password,
    set_user_password,
    verify_password,
    verify_totp,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "securepassword123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_different_hashes(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses random salt


class TestAuthenticateUser:
    def test_valid_password_login(self, db: Session):
        user = User(
            email="auth@test.com",
            display_name="Auth User",
            technical_role=TechnicalRole.viewer,
            password_hash=hash_password("testpass123"),
            is_active=True,
        )
        db.add(user)
        db.commit()

        result = authenticate_user(db, "auth@test.com", "testpass123")
        assert result is not None
        assert result.id == user.id

    def test_wrong_password_returns_none(self, db: Session):
        user = User(
            email="auth2@test.com",
            display_name="Auth2",
            technical_role=TechnicalRole.viewer,
            password_hash=hash_password("testpass123"),
            is_active=True,
        )
        db.add(user)
        db.commit()

        result = authenticate_user(db, "auth2@test.com", "wrongpass")
        assert result is None

    def test_no_password_hash_returns_none(self, db: Session):
        user = User(
            email="nopass@test.com",
            display_name="NoPass",
            technical_role=TechnicalRole.viewer,
            is_active=True,
        )
        db.add(user)
        db.commit()

        result = authenticate_user(db, "nopass@test.com", "anything")
        assert result is None

    def test_inactive_user_returns_none(self, db: Session):
        user = User(
            email="inactive@test.com",
            display_name="Inactive",
            technical_role=TechnicalRole.viewer,
            password_hash=hash_password("testpass"),
            is_active=False,
        )
        db.add(user)
        db.commit()

        result = authenticate_user(db, "inactive@test.com", "testpass")
        assert result is None

    def test_nonexistent_email_returns_none(self, db: Session):
        result = authenticate_user(db, "nobody@test.com", "testpass")
        assert result is None


class TestSetPassword:
    def test_set_password_updates_hash(self, db: Session):
        user = User(
            email="setpw@test.com",
            display_name="SetPW",
            technical_role=TechnicalRole.viewer,
            is_active=True,
        )
        db.add(user)
        db.commit()

        set_user_password(db, user, "newpassword")
        db.refresh(user)
        assert user.password_hash is not None
        assert verify_password("newpassword", user.password_hash) is True


class TestTOTP:
    def test_generate_secret(self):
        secret = generate_totp_secret()
        assert len(secret) == 32  # base32 encoded

    def test_totp_uri_format(self):
        uri = get_totp_uri("JBSWY3DPEHPK3PXP", "test@example.com")
        assert "otpauth://totp/" in uri
        assert "StaffPlan" in uri

    def test_verify_valid_code(self):
        secret = generate_totp_secret()
        code = pyotp.TOTP(secret).now()
        assert verify_totp(secret, code) is True

    def test_verify_invalid_code(self):
        secret = generate_totp_secret()
        assert verify_totp(secret, "000000") is False

    def test_enable_totp_with_valid_code(self, db: Session):
        user = User(
            email="totp@test.com",
            display_name="TOTP",
            technical_role=TechnicalRole.viewer,
            is_active=True,
        )
        db.add(user)
        db.commit()

        secret = generate_totp_secret()
        code = pyotp.TOTP(secret).now()
        assert enable_totp(db, user, secret, code) is True
        db.refresh(user)
        assert user.totp_enabled is True
        assert user.totp_secret == secret

    def test_enable_totp_with_invalid_code(self, db: Session):
        user = User(
            email="totp2@test.com",
            display_name="TOTP2",
            technical_role=TechnicalRole.viewer,
            is_active=True,
        )
        db.add(user)
        db.commit()

        secret = generate_totp_secret()
        assert enable_totp(db, user, secret, "999999") is False
        db.refresh(user)
        assert user.totp_enabled is False

    def test_disable_totp(self, db: Session):
        user = User(
            email="totp3@test.com",
            display_name="TOTP3",
            technical_role=TechnicalRole.viewer,
            totp_secret="JBSWY3DPEHPK3PXP",
            totp_enabled=True,
            is_active=True,
        )
        db.add(user)
        db.commit()

        disable_totp(db, user)
        db.refresh(user)
        assert user.totp_enabled is False
        assert user.totp_secret is None


class TestOAuthUserMapping:
    def test_find_by_azure_oid(self, db: Session):
        user = User(
            email="oid@test.com",
            display_name="OID",
            technical_role=TechnicalRole.viewer,
            azure_oid="test-oid-123",
            is_active=True,
        )
        db.add(user)
        db.commit()

        result = find_or_create_oauth_user(db, {"oid": "test-oid-123", "email": "other@test.com"})
        assert result.id == user.id

    def test_find_by_email_and_link_oid(self, db: Session):
        user = User(
            email="link@test.com",
            display_name="Link",
            technical_role=TechnicalRole.viewer,
            is_active=True,
        )
        db.add(user)
        db.commit()

        result = find_or_create_oauth_user(db, {"oid": "new-oid", "email": "link@test.com"})
        assert result.id == user.id
        db.refresh(user)
        assert user.azure_oid == "new-oid"

    def test_create_new_oauth_user(self, db: Session):
        claims = {
            "oid": "brand-new-oid",
            "email": "newoauth@test.com",
            "name": "New OAuth User",
        }
        result = find_or_create_oauth_user(db, claims)
        assert result is not None
        assert result.email == "newoauth@test.com"
        assert result.display_name == "New OAuth User"
        assert result.technical_role.value == "viewer"
        assert result.azure_oid == "brand-new-oid"

    def test_no_email_returns_none(self, db: Session):
        result = find_or_create_oauth_user(db, {"oid": "some-oid"})
        assert result is None


class TestPasswordLoginFlow:
    """Integration tests for the login endpoint."""

    def test_login_page_renders(self, client):
        response = client.get("/auth/login")
        assert response.status_code == 200

    @patch("app.routers.auth.validate_csrf", return_value=True)
    def test_login_with_valid_password(self, mock_csrf, client, db: Session):
        user = User(
            email="login@test.com",
            display_name="Login User",
            technical_role=TechnicalRole.admin,
            password_hash=hash_password("testpass123"),
            is_active=True,
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/auth/login",
            data={"email": "login@test.com", "password": "testpass123"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @patch("app.routers.auth.validate_csrf", return_value=True)
    def test_login_with_wrong_password(self, mock_csrf, client, db: Session):
        user = User(
            email="login2@test.com",
            display_name="Login2",
            technical_role=TechnicalRole.viewer,
            password_hash=hash_password("testpass123"),
            is_active=True,
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/auth/login",
            data={"email": "login2@test.com", "password": "wrong"},
        )
        assert response.status_code == 200
        assert "Invalid email or password" in response.text

    @patch("app.routers.auth.validate_csrf", return_value=True)
    def test_login_with_2fa_redirects_to_2fa_page(self, mock_csrf, client, db: Session):
        secret = generate_totp_secret()
        user = User(
            email="2falogin@test.com",
            display_name="2FA Login",
            technical_role=TechnicalRole.viewer,
            password_hash=hash_password("testpass123"),
            totp_secret=secret,
            totp_enabled=True,
            is_active=True,
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/auth/login",
            data={"email": "2falogin@test.com", "password": "testpass123"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/auth/2fa" in response.headers["location"]

    def test_change_password_page_requires_auth(self, client):
        response = client.get("/auth/change-password")
        assert response.status_code == 401

    @patch("app.routers.auth.validate_csrf", return_value=True)
    def test_change_password_flow(self, mock_csrf, client, db: Session):
        user = User(
            email="changepw@test.com",
            display_name="ChangePW",
            technical_role=TechnicalRole.viewer,
            password_hash=hash_password("oldpass123"),
            is_active=True,
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/auth/change-password",
            data={
                "current_password": "oldpass123",
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
            headers={"X-User-Id": str(user.id)},
            follow_redirects=False,
        )
        assert response.status_code == 303
        db.refresh(user)
        assert verify_password("newpass123", user.password_hash) is True
