"""Tests for performance middleware: dynamic compression, ETags, and 304 caching."""

from fastapi.testclient import TestClient
from heatsense_api.main import app


def test_etag_header_generated():
    """Verify GET requests return an ETag header and Cache-Control header."""
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "etag" in response.headers
        etag = response.headers["etag"]
        assert etag.startswith('W/"')
        assert "cache-control" in response.headers


def test_etag_conditional_request_304():
    """Verify sending matching If-None-Match returns HTTP 304 Not Modified."""
    with TestClient(app) as client:
        # Initial request
        res1 = client.get("/api/v1/locations/search?q=Mumbai")
        assert res1.status_code == 200
        etag = res1.headers.get("etag")
        assert etag is not None

        # Conditional request with matching ETag
        res2 = client.get(
            "/api/v1/locations/search?q=Mumbai",
            headers={"if-none-match": etag},
        )
        assert res2.status_code == 304
        assert res2.text == ""
        assert res2.headers.get("etag") == etag


def test_gzip_compression_for_large_payloads():
    """Verify large responses (>1000 bytes) are gzip compressed when requested."""
    with TestClient(app) as client:
        # Search for a broad query or grid layer that produces >1000 bytes
        response = client.get(
            "/api/v1/locations/search?q=a&limit=20",
            headers={"accept-encoding": "gzip"},
        )
        assert response.status_code == 200
        # If payload was >= 1000 bytes, GZipMiddleware adds content-encoding
        if len(response.content) >= 1000:
            assert response.headers.get("content-encoding") == "gzip"


def test_boundaries_geojson_and_etag():
    """Verify boundaries endpoint returns GeoJSON FeatureCollection and supports 304."""
    with TestClient(app) as client:
        res = client.get("/api/v1/locations/boundaries?state=Maharashtra")
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        etag = res.headers.get("etag")
        assert etag is not None

        # Verify 304 Not Modified
        res_304 = client.get(
            "/api/v1/locations/boundaries?state=Maharashtra",
            headers={"if-none-match": etag},
        )
        assert res_304.status_code == 304
        assert res_304.text == ""

        # Verify single city boundary
        res_city = client.get("/api/v1/locations/boundaries/city_mumbai")
        assert res_city.status_code == 200
        city_data = res_city.json()
        assert city_data["type"] == "Feature"
        assert city_data["properties"]["name"] == "Mumbai"


def test_in_memory_lru_cache_bounded():
    """Verify InMemoryCache enforces max_size and evicts oldest entries."""
    from heatsense_api.services.cache import InMemoryCache

    test_cache = InMemoryCache(default_ttl_seconds=60, max_size=3)
    test_cache.set("k1", "v1")
    test_cache.set("k2", "v2")
    test_cache.set("k3", "v3")

    assert test_cache.size() == 3
    assert test_cache.get("k1") == "v1"

    # Adding 4th item should evict k2 (since k1 was accessed most recently)
    test_cache.set("k4", "v4")
    assert test_cache.size() == 3
    assert test_cache.get("k2") is None
    assert test_cache.get("k1") == "v1"
    assert test_cache.get("k3") == "v3"
    assert test_cache.get("k4") == "v4"


def test_ckdtree_nearest_cell_lookup():
    """Verify WeatherGridRepository cKDTree resolves closest coordinate accurately."""
    from heatsense_api.repositories.weather_grid import WeatherGridRepository

    repo = WeatherGridRepository()
    # Query Mumbai coordinate
    cell_id, lat, lon = repo.find_nearest_cell(18.93, 72.83)
    assert cell_id is not None
    assert 18.0 <= lat <= 20.0
    assert 72.0 <= lon <= 74.0
