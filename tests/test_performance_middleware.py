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
