"""
Unit and regression tests for Western and Northern Indian geospatial boundary data.
Validates Gujarat, Rajasthan, Punjab, Haryana, and Delhi administrative districts.
"""

import json
import os
from shapely.geometry import shape, Point

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "interim")
UNIFIED_GEOJSON = os.path.join(DATA_DIR, "western_northern_districts_validated.geojson")
CITY_DATA_JSON = os.path.join(DATA_DIR, "western_northern_cities_data.json")


def test_unified_geojson_exists_and_valid():
    """Verify the extracted and healed unified Western-Northern GeoJSON exists."""
    assert os.path.exists(UNIFIED_GEOJSON), f"Missing {UNIFIED_GEOJSON}"
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    # 34 (Gujarat) + 33 (Rajasthan) + 22 (Punjab) + 22 (Haryana) + 11 (Delhi) = 122
    assert len(features) == 122, f"Expected 122 features, found {len(features)}"


def test_no_em_dashes_in_geospatial_outputs():
    """Verify strictly zero em dashes or en dashes in JSON and GeoJSON outputs."""
    for path in [UNIFIED_GEOJSON, CITY_DATA_JSON]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "—" not in content, f"Em dash found in {path}"
        assert "\u2014" not in content, f"Unicode em dash found in {path}"
        assert "\u2013" not in content, f"Unicode en dash found in {path}"


def test_all_geometries_are_topologically_valid_wgs84():
    """Verify all geometries are valid WGS84 polygons without self-intersections."""
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feat in data["features"]:
        props = feat["properties"]
        geom_shape = shape(feat["geometry"])
        assert geom_shape.is_valid, f"Invalid geometry for {props['district']}"
        assert geom_shape.geom_type in ("Polygon", "MultiPolygon")

        # Bbox checks
        min_lon, min_lat, max_lon, max_lat = geom_shape.bounds
        assert 20.0 <= min_lat <= 33.5, f"Latitude out of bounds for {props['district']}: {min_lat}"
        assert 68.0 <= min_lon <= 79.0, f"Longitude out of bounds for {props['district']}: {min_lon}"
        assert min_lat < max_lat
        assert min_lon < max_lon


def test_zero_consecutive_duplicate_vertices():
    """Verify zero consecutive duplicate vertices to ensure zero-flicker WebGL rendering."""
    with open(CITY_DATA_JSON, "r", encoding="utf-8") as f:
        cities = json.load(f)

    for city in cities:
        coords = city["polygonCoordinates"]
        assert len(coords) >= 4, f"Fewer than 4 vertices in {city['name']}"
        # Ring closure
        assert coords[0] == coords[-1], f"Ring not closed in {city['name']}"
        # No consecutive duplicates
        for i in range(len(coords) - 1):
            assert coords[i] != coords[i + 1], f"Duplicate consecutive vertex in {city['name']} at index {i}"


def test_district_headquarters_inside_boundary():
    """Verify district headquarters coordinates lie inside their respective boundary polygon."""
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feat in data["features"]:
        props = feat["properties"]
        geom_shape = shape(feat["geometry"])
        hq_point = Point(props["hq_lon"], props["hq_lat"])
        assert geom_shape.contains(hq_point), (
            f"HQ {props['hq_name']} ({props['hq_lat']}, {props['hq_lon']}) "
            f"is outside {props['district']} ({props['state']})"
        )
