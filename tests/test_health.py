"""Tests for the /api/v1/health endpoint."""

from fastapi.testclient import TestClient
from heatsense_api.main import app


def test_health_endpoint():
    """Verify health endpoint returns 200 with schema matching 06_API_CONTRACTS.md."""
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["model_loaded"] is False  # initially false before artifacts load
    assert "IN" in data["supported_regions"]
    assert "timestamp" in data
