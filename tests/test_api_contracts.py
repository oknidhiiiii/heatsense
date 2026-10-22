"""Contract tests for all HeatSense FastAPI endpoints matching 06_API_CONTRACTS.md."""

import pytest
from fastapi.testclient import TestClient
from heatsense_api.main import app


@pytest.fixture(scope="module")
def client():
    """Module-scoped client triggering FastAPI lifespan (model loading)."""
    with TestClient(app) as c:
        yield c


def test_api_health_contract(client):
    """Verify health endpoint shows model_loaded is true once artifacts exist."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["model_loaded"] is True
    assert "IN" in data["supported_regions"]


def test_location_search_mumbai(client):
    """Verify search returns supported location with expected bounding box."""
    response = client.get("/api/v1/locations/search?q=Mumbai&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert item["name"] == "Mumbai"
    assert item["coverage_status"] == "supported"
    assert item["country_code"] == "IN"
    assert item["bbox"] is not None


def test_location_search_maharashtra_cities(client):
    """Verify search finds regional Maharashtra cities and alias lookups."""
    # Search for Nagpur
    res_nagpur = client.get("/api/v1/locations/search?q=Nagpur&limit=5")
    assert res_nagpur.status_code == 200
    items_nagpur = res_nagpur.json()["items"]
    assert len(items_nagpur) >= 1
    assert items_nagpur[0]["name"] == "Nagpur"
    assert items_nagpur[0]["coverage_status"] == "supported"

    # Search for Aurangabad (resolves Chhatrapati Sambhajinagar via admin2 alias)
    res_aurangabad = client.get("/api/v1/locations/search?q=Aurangabad&limit=5")
    assert res_aurangabad.status_code == 200
    items_aurangabad = res_aurangabad.json()["items"]
    assert len(items_aurangabad) >= 1
    assert items_aurangabad[0]["name"] == "Chhatrapati Sambhajinagar"
    assert items_aurangabad[0]["coverage_status"] == "supported"


def test_location_search_unsupported_city(client):
    """Verify unsupported cities are marked as unsupported."""
    response = client.get("/api/v1/locations/search?q=Delhi")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert data["items"][0]["coverage_status"] == "unsupported"


def test_location_search_missing_query(client):
    """Verify missing query returns 422 with standard error schema."""
    response = client.get("/api/v1/locations/search")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_history_endpoint_contract(client):
    """Verify historical time series returns typed points in degC."""
    response = client.get(
        "/api/v1/history?lat=18.93&lon=72.83&start=2024-01-01T00:00:00&end=2024-01-02T23:00:00"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unit"] == "degC"
    assert data["source"]["id"] == "ERA5-Land"
    assert len(data["points"]) > 0
    assert "timestamp" in data["points"][0]
    assert isinstance(data["points"][0]["value"], float)


def test_history_invalid_date_range(client):
    """Verify start > end returns 400 error."""
    response = client.get(
        "/api/v1/history?lat=18.93&lon=72.83&start=2024-05-01&end=2024-01-01"
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_prediction_24h_contract(client):
    """Verify +24h prediction endpoint returns HeatSense-trained model inference."""
    response = client.get("/api/v1/predictions?lat=18.93&lon=72.83&horizon_hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["horizon_hours"] == 24
    assert isinstance(data["temperature_c"], float)
    assert 10.0 <= data["temperature_c"] <= 50.0
    assert "heatsense" in data["model_id"]
    assert data["model_version"] == "v1"
    assert "initialized_at" in data
    assert "valid_at" in data


def test_prediction_48h_contract(client):
    """Verify +48h prediction endpoint returns HeatSense-trained model inference."""
    response = client.get("/api/v1/predictions?lat=18.52&lon=73.85&horizon_hours=48")
    assert response.status_code == 200
    data = response.json()
    assert data["horizon_hours"] == 48
    assert isinstance(data["temperature_c"], float)


def test_prediction_unsupported_horizon(client):
    """Verify horizons other than 24 or 48 return 400 validation error."""
    response = client.get("/api/v1/predictions?lat=18.93&lon=72.83&horizon_hours=72")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_map_grid_historical_layer(client):
    """Verify historical grid returns cell polygons with values."""
    response = client.get(
        "/api/v1/map/grid?region_id=state_IN_MH&layer=historical&bbox=18.8,72.7,19.2,73.1"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["layer"] == "historical"
    assert len(data["cells"]) > 0
    cell = data["cells"][0]
    assert cell["bounds"] is not None
    assert isinstance(cell["value"], float)


def test_map_grid_forecast24_layer(client):
    """Verify forecast24 layer generates predictions across grid cells."""
    response = client.get(
        "/api/v1/map/grid?region_id=state_IN_MH&layer=forecast24&bbox=18.8,72.7,19.2,73.1"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["layer"] == "forecast24"
    assert len(data["cells"]) > 0
    assert data["model_version"] == "v1"
    for c in data["cells"]:
        assert c["value"] is not None


def test_map_grid_heat_risk_deferred(client):
    """Verify heat_risk layer returns 501 Not Implemented per ADR 0007."""
    response = client.get("/api/v1/map/grid?region_id=state_IN_MH&layer=heat_risk")
    assert response.status_code == 501
    data = response.json()
    assert "error" in data


def test_map_grid_oversized_bbox_rejected(client):
    """Verify oversized spatial requests are bounded and rejected."""
    # 20.0 x 20.0 = 400 deg^2 (exceeds 25 deg^2 limit)
    response = client.get(
        "/api/v1/map/grid?region_id=IN&layer=historical&bbox=10.0,70.0,30.0,90.0"
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_models_metrics_endpoint(client):
    """Verify /api/v1/models/metrics returns held-out evaluation metrics from artifacts."""
    response = client.get("/api/v1/models/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 2
    horizons = {item["horizon_hours"] for item in data["items"]}
    assert 24 in horizons
    assert 48 in horizons
