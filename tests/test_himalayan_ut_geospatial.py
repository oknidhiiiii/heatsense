"""
Unit and regression tests for Northern Himalayan states and Union Territories geospatial boundary data.
Validates Ladakh, Jammu and Kashmir, Himachal Pradesh, Uttarakhand, Chandigarh,
Delhi, Andaman and Nicobar Islands, Lakshadweep, Puducherry, DNH and DD, and Goa.
"""

import json
import os
from shapely.geometry import shape, Point

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "interim")
UNIFIED_GEOJSON = os.path.join(DATA_DIR, "himalayan_ut_districts_validated.geojson")
CITY_DATA_JSON = os.path.join(DATA_DIR, "himalayan_ut_cities_data.json")
DELHI_NCT_GEOJSON = os.path.join(DATA_DIR, "delhi_nct_validated.geojson")

STATE_GEOJSONS = [
    ("ladakh_districts_validated.geojson", 2),
    ("jammu_and_kashmir_districts_validated.geojson", 22),
    ("himachal_pradesh_districts_validated.geojson", 12),
    ("uttarakhand_districts_validated.geojson", 13),
    ("chandigarh_districts_validated.geojson", 1),
    ("delhi_districts_validated.geojson", 11),
    ("andaman_and_nicobar_islands_districts_validated.geojson", 3),
    ("lakshadweep_districts_validated.geojson", 1),
    ("puducherry_districts_validated.geojson", 4),
    ("dnh_and_dd_districts_validated.geojson", 3),
    ("goa_districts_validated.geojson", 2),
]


def test_unified_geojson_exists_and_feature_count():
    """Verify the extracted and healed unified Himalayan and UT GeoJSON exists and has 74 features."""
    assert os.path.exists(UNIFIED_GEOJSON), f"Missing {UNIFIED_GEOJSON}"
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    # 2 (Ladakh) + 22 (J&K) + 12 (HP) + 13 (UK) + 1 (CHD) + 11 (Delhi) + 3 (A&N) + 1 (LD) + 4 (PUD) + 3 (DNH&DD) + 2 (Goa) = 74
    assert len(features) == 74, f"Expected 74 features, found {len(features)}"


def test_individual_state_geojsons_exist_and_counts():
    """Verify each state/UT-specific validated GeoJSON file exists with expected feature count."""
    for filename, expected_count in STATE_GEOJSONS:
        filepath = os.path.join(DATA_DIR, filename)
        assert os.path.exists(filepath), f"Missing {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("type") == "FeatureCollection"
        features = data.get("features", [])
        assert len(features) == expected_count, (
            f"Expected {expected_count} features in {filename}, found {len(features)}"
        )


def test_delhi_nct_unified_boundary():
    """Verify Delhi NCT unified boundary GeoJSON is valid and properly formatted."""
    assert os.path.exists(DELHI_NCT_GEOJSON), f"Missing {DELHI_NCT_GEOJSON}"
    with open(DELHI_NCT_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) == 1
    props = features[0]["properties"]
    assert props["name"] == "National Capital Territory of Delhi"
    geom = shape(features[0]["geometry"])
    assert geom.is_valid
    assert geom.geom_type == "Polygon"


def test_strictly_zero_em_dashes():
    """Verify strictly zero em dashes or en dashes across all JSON and GeoJSON outputs."""
    check_files = [UNIFIED_GEOJSON, CITY_DATA_JSON, DELHI_NCT_GEOJSON] + [
        os.path.join(DATA_DIR, f) for f, _ in STATE_GEOJSONS
    ]
    for path in check_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert chr(8212) not in content, f"Em dash (chr 8212) found in {path}"
        assert chr(8211) not in content, f"En dash (chr 8211) found in {path}"


def test_all_geometries_topologically_valid_wgs84():
    """Verify all geometries are valid WGS84 polygons without self-intersections within India coordinate space."""
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feat in data["features"]:
        props = feat["properties"]
        geom_shape = shape(feat["geometry"])
        assert geom_shape.is_valid, f"Invalid geometry for {props['district']}"
        assert geom_shape.geom_type in ("Polygon", "MultiPolygon")

        # Bounds checks: India extents (6.0 to 38.0 Lat, 68.0 to 98.0 Lon)
        min_lon, min_lat, max_lon, max_lat = geom_shape.bounds
        assert 6.0 <= min_lat <= 38.0, f"Latitude out of bounds for {props['district']}: {min_lat}"
        assert 68.0 <= min_lon <= 98.0, f"Longitude out of bounds for {props['district']}: {min_lon}"
        assert min_lat < max_lat
        assert min_lon < max_lon


def test_zero_consecutive_duplicate_vertices():
    """Verify zero consecutive duplicate vertices to ensure zero-flicker WebGL rendering."""
    with open(CITY_DATA_JSON, "r", encoding="utf-8") as f:
        cities = json.load(f)

    assert len(cities) == 74, f"Expected 74 city records, found {len(cities)}"
    for city in cities:
        coords = city["polygonCoordinates"]
        assert len(coords) >= 4, f"Fewer than 4 vertices in {city['name']}"
        # Ring closure
        assert coords[0] == coords[-1], f"Ring not closed in {city['name']}"
        # No consecutive duplicates
        for i in range(len(coords) - 1):
            assert coords[i] != coords[i + 1], f"Duplicate consecutive vertex in {city['name']} at index {i}"


def test_district_headquarters_inside_boundary():
    """Verify district headquarters coordinates lie strictly inside their respective boundary polygon."""
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


def test_focus_coordinates_inside_boundary():
    """Verify focus coordinates (centroid or representative point) lie strictly inside the polygon."""
    with open(UNIFIED_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feat in data["features"]:
        props = feat["properties"]
        geom_shape = shape(feat["geometry"])
        focus_point = Point(props["focus_lon"], props["focus_lat"])
        assert geom_shape.contains(focus_point), (
            f"Focus point ({props['focus_lat']}, {props['focus_lon']}) "
            f"is outside {props['district']} ({props['state']})"
        )
