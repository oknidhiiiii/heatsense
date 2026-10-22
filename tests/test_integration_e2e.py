"""Full end-to-end integration tests verifying the entire journey from data artifacts to API."""

import pytest
from fastapi.testclient import TestClient
from heatsense_api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_full_user_journey_mumbai(client):
    """Simulate Persona A user journey:

    1. Checks health.
    2. Searches 'Mumbai'.
    3. Selects historical layer for Mumbai coordinates.
    4. Switches to +24h forecast prediction.
    5. Switches to +48h forecast prediction.
    6. Queries spatial heat grid for city viewport.
    7. Inspects model card metrics.
    """
    # 1. Health
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["model_loaded"] is True

    # 2. Search
    res_search = client.get("/api/v1/locations/search?q=Mumbai")
    assert res_search.status_code == 200
    items = res_search.json()["items"]
    assert len(items) >= 1
    mumbai = items[0]
    lat = mumbai["latitude"]
    lon = mumbai["longitude"]

    # 3. Historical series
    res_hist = client.get(
        f"/api/v1/history?lat={lat}&lon={lon}&start=2024-01-01T00:00:00&end=2024-01-03T23:00:00"
    )
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert hist_data["unit"] == "degC"
    assert len(hist_data["points"]) == 72

    # 4. +24h Forecast Prediction
    res_pred24 = client.get(f"/api/v1/predictions?lat={lat}&lon={lon}&horizon_hours=24")
    assert res_pred24.status_code == 200
    pred24 = res_pred24.json()
    assert pred24["horizon_hours"] == 24
    assert 15.0 <= pred24["temperature_c"] <= 45.0
    assert pred24["model_version"] == "v1"

    # 5. +48h Forecast Prediction
    res_pred48 = client.get(f"/api/v1/predictions?lat={lat}&lon={lon}&horizon_hours=48")
    assert res_pred48.status_code == 200
    pred48 = res_pred48.json()
    assert pred48["horizon_hours"] == 48
    assert 15.0 <= pred48["temperature_c"] <= 45.0

    # 6. Map Grid overlay
    bbox_str = ",".join(map(str, mumbai["bbox"]))
    res_grid = client.get(f"/api/v1/map/grid?region_id={mumbai['id']}&layer=forecast24&bbox={bbox_str}")
    assert res_grid.status_code == 200
    grid = res_grid.json()
    assert grid["layer"] == "forecast24"
    assert len(grid["cells"]) > 0

    # 7. Model Transparency
    res_metrics = client.get("/api/v1/models/metrics")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()["items"]
    assert any(m["horizon_hours"] == 24 for m in metrics)
    assert any(m["horizon_hours"] == 48 for m in metrics)
