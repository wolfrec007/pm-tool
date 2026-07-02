"""Tests for /health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_public_no_auth():
    """/health should be accessible without any auth headers."""
    response = client.get("/health", headers={})
    assert response.status_code == 200
