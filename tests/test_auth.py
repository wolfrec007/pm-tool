"""Tests for auth/RBAC gating."""

from app.models.models import TechnicalRole


def _auth_headers(user_id: int):
    return {"X-User-Id": str(user_id)}


class TestRoleGating:
    def test_admin_can_create_client(self, client, admin_user):
        response = client.post(
            "/clients",
            json={"name": "New Client"},
            headers=_auth_headers(admin_user.id),
        )
        assert response.status_code == 201

    def test_viewer_denied_create_client(self, client, viewer_user):
        response = client.post(
            "/clients",
            json={"name": "New Client"},
            headers=_auth_headers(viewer_user.id),
        )
        assert response.status_code == 403

    def test_moderator_allowed_assignment_create(self, client, moderator_user, team_member, instance):
        response = client.post(
            "/assignments",
            json={
                "team_member_id": team_member.id,
                "engagement_instance_id": instance.id,
                "allocation_percent": 50,
                "start_date": str(instance.start_date),
                "end_date": str(instance.end_date),
            },
            headers=_auth_headers(moderator_user.id),
        )
        assert response.status_code == 201

    def test_viewer_denied_assignment_create(self, client, viewer_user, team_member, instance):
        response = client.post(
            "/assignments",
            json={
                "team_member_id": team_member.id,
                "engagement_instance_id": instance.id,
                "allocation_percent": 50,
                "start_date": str(instance.start_date),
                "end_date": str(instance.end_date),
            },
            headers=_auth_headers(viewer_user.id),
        )
        assert response.status_code == 403

    def test_viewer_can_list_assignments(self, client, viewer_user):
        response = client.get(
            "/assignments",
            headers=_auth_headers(viewer_user.id),
        )
        assert response.status_code == 200

    def test_health_public(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_unauthenticated_blocked(self, client):
        response = client.get("/team-members")
        assert response.status_code == 401
