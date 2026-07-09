import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_ok(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_returns_app_name(self):
        response = client.get("/health")
        data = response.json()
        assert "app" in data
        assert "CV Chacha" in data["app"]

    def test_health_returns_version(self):
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "1.0.0"
