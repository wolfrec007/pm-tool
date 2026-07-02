"""Tests for user management CRUD."""

from app.models.models import TechnicalRole


def _auth_headers(user_id: int):
    return {"X-User-Id": str(user_id)}


class TestUserList:
    def test_admin_can_list_users(self, client, admin_user):
        response = client.get("/users", headers=_auth_headers(admin_user.id))
        assert response.status_code == 200

    def test_viewer_denied_list_users(self, client, viewer_user):
        response = client.get("/users", headers=_auth_headers(viewer_user.id))
        assert response.status_code == 403

    def test_list_users_json(self, client, admin_user, viewer_user):
        response = client.get("/users/json", headers=_auth_headers(admin_user.id))
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_users_search(self, client, admin_user):
        response = client.get(
            "/users?q=admin",
            headers=_auth_headers(admin_user.id),
        )
        assert response.status_code == 200

    def test_list_users_filter_role(self, client, admin_user):
        response = client.get(
            "/users?technical_role=admin",
            headers=_auth_headers(admin_user.id),
        )
        assert response.status_code == 200


class TestUserCreate:
    def test_admin_can_create_user_form(self, client, admin_user):
        response = client.get("/users/new", headers=_auth_headers(admin_user.id))
        assert response.status_code == 200

    def test_admin_can_create_user(self, client, admin_user):
        response = client.post(
            "/users",
            json={"email": "new@test.com", "display_name": "New User", "technical_role": "moderator"},
            headers=_auth_headers(admin_user.id),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@test.com"
        assert data["technical_role"] == "moderator"

    def test_create_user_duplicate_email(self, client, admin_user, viewer_user):
        response = client.post(
            "/users",
            json={"email": viewer_user.email, "display_name": "Duplicate", "technical_role": "viewer"},
            headers=_auth_headers(admin_user.id),
        )
        assert response.status_code == 422

    def test_viewer_denied_create_user(self, client, viewer_user):
        response = client.post(
            "/users",
            json={"email": "bad@test.com", "display_name": "Bad", "technical_role": "viewer"},
            headers=_auth_headers(viewer_user.id),
        )
        assert response.status_code == 403


class TestUserUpdate:
    def test_admin_can_update_user(self, client, admin_user, viewer_user):
        response = client.patch(
            f"/users/{viewer_user.id}",
            json={"display_name": "Updated Name"},
            headers=_auth_headers(admin_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"

    def test_update_user_change_role(self, client, admin_user, viewer_user):
        response = client.patch(
            f"/users/{viewer_user.id}",
            json={"technical_role": "moderator"},
            headers=_auth_headers(admin_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["technical_role"] == "moderator"

    def test_viewer_denied_update_user(self, client, viewer_user, admin_user):
        response = client.patch(
            f"/users/{admin_user.id}",
            json={"display_name": "Hacked"},
            headers=_auth_headers(viewer_user.id),
        )
        assert response.status_code == 403


class TestUserDeactivate:
    def test_admin_can_deactivate_user(self, client, admin_user, viewer_user):
        response = client.post(
            f"/users/{viewer_user.id}/deactivate",
            headers=_auth_headers(admin_user.id),
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_admin_cannot_deactivate_self(self, client, admin_user):
        response = client.post(
            f"/users/{admin_user.id}/deactivate",
            headers=_auth_headers(admin_user.id),
            follow_redirects=False,
        )
        assert response.status_code == 303
        # Verify admin is still active
        response = client.get("/users/json", headers=_auth_headers(admin_user.id))
        assert response.status_code == 200

    def test_viewer_denied_deactivate(self, client, viewer_user, admin_user):
        response = client.post(
            f"/users/{admin_user.id}/deactivate",
            headers=_auth_headers(viewer_user.id),
        )
        assert response.status_code == 403
