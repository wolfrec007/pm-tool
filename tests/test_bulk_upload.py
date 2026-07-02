"""Tests for bulk CSV upload."""

import csv
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.models import BusinessRole, TechnicalRole, User


def _make_csv(rows: list[dict]) -> bytes:
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def _auth_headers(user_id: int):
    return {"X-User-Id": str(user_id)}


class TestBulkUpload:
    def test_all_valid_rows(self, client, db):
        admin = User(
            email="admin@bulk1.com",
            display_name="Bulk Admin",
            technical_role=TechnicalRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()

        rows = [
            {"name": "Alice", "email": "alice@test.com", "business_role": "staff"},
            {"name": "Bob", "email": "bob@test.com", "business_role": "staff"},
        ]
        response = client.post(
            "/team-members/bulk-upload",
            files={"file": ("test.csv", _make_csv(rows), "text/csv")},
            headers=_auth_headers(admin.id),
            follow_redirects=False,
        )
        # Now returns redirect after upload
        assert response.status_code == 303

        # Verify data was inserted via JSON API
        check = client.get("/team-members/json", headers=_auth_headers(admin.id))
        assert check.status_code == 200
        assert check.json()["total"] == 2

    def test_duplicate_emails_in_file(self, client, db):
        admin = User(
            email="admin@bulk2.com",
            display_name="Bulk Admin",
            technical_role=TechnicalRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()

        rows = [
            {"name": "Alice", "email": "alice@test.com", "business_role": "staff"},
            {"name": "Alice 2", "email": "alice@test.com", "business_role": "staff"},
        ]
        response = client.post(
            "/team-members/bulk-upload",
            files={"file": ("test.csv", _make_csv(rows), "text/csv")},
            headers=_auth_headers(admin.id),
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Only first row should be inserted
        check = client.get("/team-members/json", headers=_auth_headers(admin.id))
        assert check.json()["total"] == 1

    def test_duplicate_against_db(self, client, db):
        admin = User(
            email="admin@bulk3.com",
            display_name="Bulk Admin",
            technical_role=TechnicalRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()

        from app.models.models import TeamMember

        db.add(TeamMember(
            name="Existing User",
            email="existing@test.com",
            business_role=BusinessRole.staff,
        ))
        db.commit()

        rows = [
            {"name": "Existing User", "email": "existing@test.com", "business_role": "staff"},
        ]
        response = client.post(
            "/team-members/bulk-upload",
            files={"file": ("test.csv", _make_csv(rows), "text/csv")},
            headers=_auth_headers(admin.id),
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_auth_gating(self, client, db):
        """Non-admin should not be able to upload."""
        viewer = User(
            email="viewer@bulk.com",
            display_name="Viewer",
            technical_role=TechnicalRole.viewer,
            is_active=True,
        )
        db.add(viewer)
        db.commit()

        rows = [{"name": "Alice", "email": "alice@test.com", "business_role": "staff"}]
        response = client.post(
            "/team-members/bulk-upload",
            files={"file": ("test.csv", _make_csv(rows), "text/csv")},
            headers=_auth_headers(viewer.id),
        )
        assert response.status_code == 403
