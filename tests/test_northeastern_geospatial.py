"""
Unit and regression tests for North-Eastern Indian geospatial boundary data.
Validates Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, and Tripura administrative districts.
"""

import json
import os
import pytest
from shapely.geometry import shape, Point

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "interim")
UNIFIED_GEOJSON = os.path.join(DATA_DIR, "northeastern_districts_validated.geojson")
CITY_DATA_JSON = os.path.join(DATA_DIR, "northeastern_cities_data.json")

EXPECTED_STATE_COUNTS = {
    "Arunachal Pradesh": 25,
    "Assam": 33,
    "Manipur": 16,
    "Meghalaya": 11,
    "Mizoram": 10,
    "Nagaland": 11,
    "Sikkim": 4,
    "Tripura": 8,
}
TOTAL_NE_DISTRICTS = 118


def test_unified_geojson_exists_and_valid():
    """Verify the extracted and healed unified North-Eastern GeoJSON exists and has 118 districts."""
    assert os.path.exists(UNIFIED_GEOJSON), f"Missing {UNIFIED_GEOJSON}"
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) == TOTAL_NE_DISTRICTS, f"Expected {TOTAL_NE_DISTRICTS} features, found {len(features)}"

    # Check state breakdown
    counts = {}
    for feat in features:
        st = feat["properties"]["state"]
        counts[st] = counts.get(st, 0) + 1

    for st, expected_count in EXPECTED_STATE_COUNTS.items():
        assert counts.get(st) == expected_count, f"State {st}: expected {expected_count}, got {counts.get(st)}"


def test_state_specific_geojsons_exist():
    """Verify each state's individual validated GeoJSON exists and matches expected district counts."""
    state_slugs = {
        "arunachal_pradesh": ("Arunachal Pradesh", 25),
        "assam": ("Assam", 33),
        "manipur": ("Manipur", 16),
        "meghalaya": ("Meghalaya", 11),
        "mizoram": ("Mizoram", 10),
        "nagaland": ("Nagaland", 11),
        "sikkim": ("Sikkim", 4),
        "tripura": ("Tripura", 8),
    }

    for slug, (state_name, count) in state_slugs.items():
        state_path = os.path.join(DATA_DIR, f"{slug}_districts_validated.geojson")
        assert os.path.exists(state_path), f"Missing state file: {state_path}"
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data.get("features", [])
        assert len(features) == count, f"State {state_name}: expected {count} features, found {len(features)}"


def test_no_em_dashes_in_geospatial_outputs():
    """Verify strictly zero em dashes or en dashes in JSON and GeoJSON outputs."""
    check_files = [UNIFIED_GEOJSON, CITY_DATA_JSON]
    for slug in ["arunachal_pradesh", "assam", "manipur", "meghalaya", "mizoram", "nagaland", "sikkim", "tripura"]:
        check_files.append(os.path.join(DATA_DIR, f"{slug}_districts_validated.geojson"))

    for path in check_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "\u2014" not in content, f"Unicode em dash found in {path}"
        assert "\u2013" not in content, f"Unicode en dash found in {path}"


def test_all_geometries_are_topologically_valid_wgs84():
    """Verify all geometries are valid WGS84 polygons without self-intersections."""
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feat in data["features"]:
        props = feat["properties"]
        geom_shape = shape(feat["geometry"])
        assert geom_shape.is_valid, f"Invalid geometry for {props['district']} ({props['state']})"
        assert geom_shape.geom_type in ("Polygon", "MultiPolygon")

        # Bbox checks: North-East India spans ~21.5°N to 30.0°N and ~88.0°E to 98.0°E
        min_lon, min_lat, max_lon, max_lat = geom_shape.bounds
        assert 21.5 <= min_lat <= 30.0, f"Latitude out of bounds for {props['district']}: {min_lat}"
        assert 88.0 <= min_lon <= 98.0, f"Longitude out of bounds for {props['district']}: {min_lon}"
        assert min_lat < max_lat
        assert min_lon < max_lon


def test_zero_consecutive_duplicate_vertices():
    """Verify zero consecutive duplicate vertices to ensure zero-flicker WebGL rendering."""
    with open(CITY_DATA_JSON, "r", encoding="utf-8") as f:
        cities = json.load(f)

    assert len(cities) == TOTAL_NE_DISTRICTS, f"Expected {TOTAL_NE_DISTRICTS} city records, found {len(cities)}"

    for city in cities:
        coords = city["polygonCoordinates"]
        assert len(coords) >= 4, f"Fewer than 4 vertices in {city['name']}"
        # Ring closure
        assert coords[0] == coords[-1], f"Ring not closed in {city['name']}"
        # No consecutive duplicates
        for i in range(len(coords) - 1):
            assert coords[i] != coords[i + 1], f"Duplicate consecutive vertex in {city['name']} at index {i}"


def test_district_headquarters_inside_boundary():
    """Verify all 118 district headquarters coordinates lie strictly inside their respective boundary polygon."""
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


def test_repaired_malformed_geometries():
    """Verify known malformed districts (Kakching, Chandel, Churachandpur, Aizawl, Kolasib, Mamit) are marked repaired and valid."""
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    repaired_districts = {
        ("Manipur", "Kakching"),
        ("Manipur", "Chandel"),
        ("Manipur", "Churachandpur"),
        ("Mizoram", "Aizawl"),
        ("Mizoram", "Kolasib"),
        ("Mizoram", "Mamit"),
    }

    found_repaired = set()
    for feat in data["features"]:
        props = feat["properties"]
        key = (props["state"], props["district"])
        if key in repaired_districts:
            assert props["repaired"] is True, f"{key} should have been repaired"
            geom = shape(feat["geometry"])
            assert geom.is_valid, f"{key} repaired geometry is not valid"
            found_repaired.add(key)

    assert found_repaired == repaired_districts


def test_concave_districts_use_interior_focus_points():
    """Verify concave districts use representative interior point for camera focus inside the polygon."""
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    concave_targets = {
        ("Arunachal Pradesh", "West Siang"),
        ("Assam", "Dhubri"),
        ("Assam", "South Salmara Mankachar"),
    }

    for feat in data["features"]:
        props = feat["properties"]
        key = (props["state"], props["district"])
        if key in concave_targets:
            geom = shape(feat["geometry"])
            focus_pt = Point(props["focus_lon"], props["focus_lat"])
            assert geom.contains(focus_pt), f"Focus point for {key} is not inside boundary"
