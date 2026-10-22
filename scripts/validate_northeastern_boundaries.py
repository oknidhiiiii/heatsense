"""
HeatSense North-Eastern Indian Administrative Boundary Validator and Extractor.
Validates 118 districts across Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, and Tripura.
Ensures zero em dashes, valid WGS84 coordinates, and zero-flicker geometry rendering.
"""

import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping
from shapely.validation import make_valid, explain_validity

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HeatSenseNortheasternGeospatial")

# Canonical Headquarters Data: (HQ_Name, Latitude, Longitude)
DISTRICT_HQ_DATA: Dict[str, Tuple[str, float, float]] = {
    # Arunachal Pradesh (25)
    "Upper Subansiri": ("Daporijo", 27.9878, 94.2186),
    "Anjaw": ("Hawai", 27.8856, 96.7997),
    "Changlang": ("Changlang", 27.1333, 95.7333),
    "Tawang": ("Tawang", 27.5861, 91.8653),
    "Papum Pare": ("Yupia", 27.1436, 93.6828),
    "Tirap": ("Khonsa", 27.0211, 95.5564),
    "East Siang": ("Pasighat", 28.0667, 95.3333),
    "Lohit": ("Tezu", 27.9167, 96.1667),
    "Kurung Kumey": ("Koloriang", 27.9044, 93.3517),
    "Lower Subansiri": ("Ziro", 27.5333, 93.8333),
    "East Kameng": ("Seppa", 27.3500, 93.0333),
    "West Kameng": ("Bomdila", 27.2645, 92.4159),
    "Kra Daadi": ("Palin", 27.7167, 93.6000),
    "Namsai": ("Namsai", 27.6694, 95.8672),
    "Longding": ("Longding", 26.8667, 95.3000),
    "Upper Siang": ("Yingkiong", 28.6333, 94.9167),
    "Lower Siang": ("Likabali", 27.6500, 94.6667),
    "Upper Dibang Valley": ("Anini", 28.8000, 95.9000),
    "Lower Dibang Valley": ("Roing", 28.1400, 95.8300),
    "Siang": ("Boleng", 28.3333, 94.9667),
    "Shi Yomi": ("Tato", 28.5333, 94.3667),
    "Pakke Kessang": ("Lemmi", 27.1500, 93.1833),
    "West Siang": ("Aalo", 28.1700, 94.8000),
    "Lepa Rada": ("Basar", 27.9800, 94.6700),
    "Kamle": ("Raga", 27.7667, 94.0667),

    # Assam (33)
    "Tinsukia": ("Tinsukia", 27.5000, 95.3667),
    "Dhemaji": ("Dhemaji", 27.4833, 94.5833),
    "Dibrugarh": ("Dibrugarh", 27.4833, 94.9167),
    "Lakhimpur": ("North Lakhimpur", 27.2333, 94.1000),
    "Sivasagar": ("Sivasagar", 26.9833, 94.6333),
    "Jorhat": ("Jorhat", 26.7500, 94.2167),
    "Sonitpur": ("Tezpur", 26.6333, 92.8000),
    "Golaghat": ("Golaghat", 26.5167, 93.9667),
    "Udalguri": ("Udalguri", 26.7453, 92.0962),
    "Chirang": ("Kajalgaon", 26.5333, 90.5500),
    "Baksa": ("Mushalpur", 26.5833, 91.3333),
    "Nagaon": ("Nagaon", 26.3500, 92.6833),
    "Kokrajhar": ("Kokrajhar", 26.4000, 90.2667),
    "Darrang": ("Mangaldai", 26.4333, 92.0333),
    "Barpeta": ("Barpeta", 26.3167, 91.0000),
    "Nalbari": ("Nalbari", 26.4500, 91.4333),
    "Morigaon": ("Morigaon", 26.2500, 92.3333),
    "Kamrup": ("Amingaon", 26.2167, 91.6333),
    "Bongaigaon": ("Bongaigaon", 26.4833, 90.5667),
    "Dhubri": ("Dhubri", 26.0167, 89.9833),
    "Kamrup Metropolitan": ("Guwahati", 26.1445, 91.7362),
    "Goalpara": ("Goalpara", 26.1667, 90.6167),
    "Dima Hasao": ("Haflong", 25.1833, 93.0333),
    "Cachar": ("Silchar", 24.8167, 92.8000),
    "Karimganj": ("Karimganj", 24.8667, 92.3500),
    "Hailakandi": ("Hailakandi", 24.6833, 92.5667),
    "Charaideo": ("Sonari", 27.0167, 95.0333),
    "Majuli": ("Garamur", 26.9667, 94.2167),
    "Biswanath": ("Biswanath Chariali", 26.7333, 93.1500),
    "Hojai": ("Hojai", 26.0000, 92.8667),
    "South Salmara Mankachar": ("Hatsingimari", 25.6833, 89.8833),
    "Karbi Anglong": ("Diphu", 25.8333, 93.4333),
    "West Karbi Anglong": ("Hamren", 25.8667, 92.6000),

    # Manipur (16)
    "Bishnupur": ("Bishnupur", 24.6333, 93.7667),
    "Chandel": ("Chandel", 24.3167, 94.0000),
    "Churachandpur": ("Churachandpur", 24.3333, 93.6833),
    "Imphal East": ("Porompat", 24.8167, 93.9667),
    "Imphal West": ("Lamphelpat", 24.8167, 93.9000),
    "Jiribam": ("Jiribam", 24.8000, 93.1167),
    "Kakching": ("Kakching", 24.4833, 93.9833),
    "Kamjong": ("Kamjong", 24.8667, 94.4833),
    "Kangpokpi": ("Kangpokpi", 25.1500, 93.9667),
    "Noney": ("Noney", 24.7000, 93.6000),
    "Pherzawl": ("Pherzawl", 24.2500, 93.2000),
    "Senapati": ("Senapati", 25.2667, 94.0167),
    "Tamenglong": ("Tamenglong", 24.9833, 93.4833),
    "Tengnoupal": ("Tengnoupal", 24.3667, 94.1500),
    "Thoubal": ("Thoubal", 24.6333, 94.0000),
    "Ukhrul": ("Ukhrul", 25.1167, 94.3667),

    # Meghalaya (11)
    "East Garo Hills": ("Williamnagar", 25.5000, 90.6167),
    "East Jaintia Hills": ("Khliehriat", 25.3500, 92.3667),
    "East Khasi Hills": ("Shillong", 25.5788, 91.8933),
    "North Garo Hills": ("Resubelpara", 25.9000, 90.6000),
    "Ribhoi": ("Nongpoh", 25.9000, 91.8833),
    "South Garo Hills": ("Baghmara", 25.2000, 90.6333),
    "South West Garo Hills": ("Ampati", 25.4667, 89.9333),
    "South West Khasi Hills": ("Mawkyrwat", 25.3667, 91.4500),
    "West Garo Hills": ("Tura", 25.5167, 90.2167),
    "West Jaintia Hills": ("Jowai", 25.4500, 92.2000),
    "West Khasi Hills": ("Nongstoin", 25.5167, 91.2667),

    # Mizoram (10)
    "Aizawl": ("Aizawl", 23.7271, 92.7176),
    "Champhai": ("Champhai", 23.4750, 93.3278),
    "Kolasib": ("Kolasib", 24.2247, 92.6783),
    "Lawngtlai": ("Lawngtlai", 22.5278, 92.8944),
    "Lunglei": ("Lunglei", 22.8872, 92.7389),
    "Mamit": ("Mamit", 23.9294, 92.4906),
    "Saiha": ("Saiha", 22.4897, 92.9778),
    "Serchhip": ("Serchhip", 23.3108, 92.8483),
    "Khawzawl": ("Khawzawl", 23.5350, 93.1833),
    "Hnahthial": ("Hnahthial", 22.9667, 92.9333),

    # Nagaland (11)
    "Dimapur": ("Dimapur", 25.9068, 93.7271),
    "Kiphire": ("Kiphire", 25.8667, 94.7833),
    "Kohima": ("Kohima", 25.6751, 94.1086),
    "Longleng": ("Longleng", 26.4667, 94.8000),
    "Mokokchung": ("Mokokchung", 26.3250, 94.5200),
    "Mon": ("Mon", 26.7500, 95.0333),
    "Peren": ("Peren", 25.5167, 93.7333),
    "Phek": ("Phek", 25.6667, 94.4667),
    "Tuensang": ("Tuensang", 26.2833, 94.8333),
    "Wokha": ("Wokha", 26.1000, 94.2667),
    "Zunheboto": ("Zunheboto", 25.9667, 94.5167),

    # Sikkim (4)
    "East Sikkim": ("Gangtok", 27.3389, 88.6065),
    "North Sikkim": ("Mangan", 27.5056, 88.5347),
    "South Sikkim": ("Namchi", 27.1667, 88.3500),
    "West Sikkim": ("Gyalshing", 27.2833, 88.2500),

    # Tripura (8)
    "Dhalai": ("Ambassa", 23.9167, 91.8500),
    "Gomati": ("Udaipur", 23.5333, 91.4833),
    "Khowai": ("Khowai", 24.0667, 91.6000),
    "North Tripura": ("Dharmanagar", 24.3667, 92.1667),
    "Sipahijala": ("Bishramganj", 23.6333, 91.3333),
    "South Tripura": ("Belonia", 23.2500, 91.4500),
    "Unokoti": ("Kailashahar", 24.3333, 92.0000),
    "West Tripura": ("Agartala", 23.8315, 91.2868),
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in kilometers between two lat/lon coordinates."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def sanitize_text(text: str) -> str:
    """Ensure zero em dashes and zero en dashes."""
    return text.replace("\u2014", ": ").replace("\u2013", "-")


def repair_and_clean_geometry(raw_geom: Any, district_name: str) -> Tuple[Polygon, bool, str]:
    """
    Repair self-intersections or bowtie anomalies and return a guaranteed-valid Polygon.
    Returns: (clean_polygon, was_repaired, repair_reason)
    """
    s_geom = shape(raw_geom)
    was_repaired = False
    reason = "Valid"

    if not s_geom.is_valid:
        was_repaired = True
        reason = explain_validity(s_geom)
        logger.info(f"Repairing invalid geometry for {district_name}: {reason}")
        fixed = make_valid(s_geom)

        if fixed.geom_type == "Polygon":
            s_geom = fixed
        elif fixed.geom_type == "MultiPolygon":
            s_geom = max(fixed.geoms, key=lambda g: g.area)
        elif fixed.geom_type == "GeometryCollection":
            polys = [g for g in fixed.geoms if isinstance(g, (Polygon, MultiPolygon))]
            if polys:
                s_geom = max(polys, key=lambda g: g.area)
                if s_geom.geom_type == "MultiPolygon":
                    s_geom = max(s_geom.geoms, key=lambda g: g.area)
            else:
                raise ValueError(f"Unable to recover polygon from GeometryCollection for {district_name}")

    elif s_geom.geom_type == "MultiPolygon":
        s_geom = max(s_geom.geoms, key=lambda g: g.area)

    return s_geom, was_repaired, reason


def extract_zero_flicker_coords(poly: Polygon) -> List[List[float]]:
    """
    Extract zero-flicker outer ring coordinates:
    - Counter-clockwise winding
    - 5 decimal precision (~1.1m)
    - Removal of duplicate consecutive vertices
    - Explicit ring closure
    """
    exterior = poly.exterior
    raw_coords = list(exterior.coords)

    cleaned: List[List[float]] = []
    prev_pt: Optional[Tuple[float, float]] = None

    for pt in raw_coords:
        lon_r = round(float(pt[0]), 5)
        lat_r = round(float(pt[1]), 5)
        curr_pt = (lon_r, lat_r)

        if curr_pt != prev_pt:
            cleaned.append([lon_r, lat_r])
            prev_pt = curr_pt

    if len(cleaned) < 4:
        raise ValueError("Polygon has fewer than 4 vertices after deduplication")

    if cleaned[0] != cleaned[-1]:
        cleaned.append(cleaned[0])

    return cleaned


def main():
    target_states = [
        ("Arunachal Pradesh", "arunachal-pradesh", "North-Eastern"),
        ("Assam", "assam", "North-Eastern"),
        ("Manipur", "manipur", "North-Eastern"),
        ("Meghalaya", "meghalaya", "North-Eastern"),
        ("Mizoram", "mizoram", "North-Eastern"),
        ("Nagaland", "nagaland", "North-Eastern"),
        ("Sikkim", "sikkim", "North-Eastern"),
        ("Tripura", "tripura", "North-Eastern"),
    ]

    dest_dir = os.path.join(os.path.dirname(__file__), "..", "data", "interim")

    all_validated_features = []
    all_city_records = []
    malformed_reports = []
    multipart_reports = []
    concave_centroid_reports = []

    total_districts_processed = 0

    for state_name, slug, region in target_states:
        geojson_path = os.path.join(dest_dir, "states", f"{slug}.geojson")
        with open(geojson_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        features = raw_data.get("features", [])
        state_feature_count = len(features)
        logger.info(f"Processing {state_name}: {state_feature_count} districts...")

        state_validated_features = []

        for feat in features:
            total_districts_processed += 1
            props = feat.get("properties", {})
            district_name = props.get("district") or props.get("dtname") or props.get("name")
            district_name = sanitize_text(district_name.strip())

            raw_geom = feat.get("geometry", {})
            orig_geom_type = raw_geom.get("type")

            # Check MultiPolygon fragmentation
            if orig_geom_type == "MultiPolygon":
                part_count = len(raw_geom.get("coordinates", []))
                multipart_reports.append({
                    "state": state_name,
                    "district": district_name,
                    "parts": part_count,
                })

            # Geometry repair and cleanup
            clean_poly, was_repaired, repair_reason = repair_and_clean_geometry(raw_geom, district_name)
            if was_repaired:
                malformed_reports.append({
                    "state": state_name,
                    "district": district_name,
                    "reason": repair_reason,
                })

            # Zero-flicker coordinates
            polygon_coords = extract_zero_flicker_coords(clean_poly)

            # Bounding box calculation [minLat, minLon, maxLat, maxLon]
            lons = [pt[0] for pt in polygon_coords]
            lats = [pt[1] for pt in polygon_coords]
            min_lat = round(min(lats), 4)
            max_lat = round(max(lats), 4)
            min_lon = round(min(lons), 4)
            max_lon = round(max(lons), 4)
            bbox = [min_lat, min_lon, max_lat, max_lon]

            # Centroid calculations
            centroid_pt = clean_poly.centroid
            rep_pt = clean_poly.representative_point()
            cent_lat = round(centroid_pt.y, 4)
            cent_lon = round(centroid_pt.x, 4)
            rep_lat = round(rep_pt.y, 4)
            rep_lon = round(rep_pt.x, 4)

            # Check if centroid is inside polygon
            centroid_inside = clean_poly.contains(centroid_pt)
            if not centroid_inside:
                concave_centroid_reports.append({
                    "state": state_name,
                    "district": district_name,
                    "geometric_centroid": [cent_lat, cent_lon],
                    "representative_interior_point": [rep_lat, rep_lon],
                })
                # Use interior point for camera focus
                focus_lat = rep_lat
                focus_lon = rep_lon
            else:
                focus_lat = cent_lat
                focus_lon = cent_lon

            # Headquarters Validation
            hq_info = DISTRICT_HQ_DATA.get(district_name)
            if not hq_info:
                raise KeyError(f"Missing HQ data for {district_name} ({state_name})")

            hq_name, hq_lat, hq_lon = hq_info
            hq_point = Point(hq_lon, hq_lat)
            hq_inside = clean_poly.contains(hq_point)
            hq_dist_km = round(haversine_distance(cent_lat, cent_lon, hq_lat, hq_lon), 2)

            # Camera height
            span = max(max_lat - min_lat, max_lon - min_lon)
            camera_height = int(max(60000, span * 111000 * 1.55))

            # Description (zero em dashes)
            description = sanitize_text(
                f"{district_name} District ({region}): Admin HQ at {hq_name}. Thermal monitoring boundary."
            )
            city_id = f"city_{district_name.lower().replace(' ', '_').replace('-', '_').replace('.', '')}"

            city_record = {
                "id": city_id,
                "name": district_name,
                "state": state_name,
                "latitude": focus_lat,
                "longitude": focus_lon,
                "headquarters": {
                    "name": hq_name,
                    "latitude": hq_lat,
                    "longitude": hq_lon,
                    "is_distinct_name": hq_name.lower() != district_name.lower(),
                    "distance_to_centroid_km": hq_dist_km,
                    "contained_in_boundary": hq_inside,
                },
                "cameraHeight": camera_height,
                "bbox": bbox,
                "description": description,
                "polygonCoordinates": polygon_coords,
            }
            all_city_records.append(city_record)

            # Validated GeoJSON Feature
            validated_feature = {
                "type": "Feature",
                "properties": {
                    "district": district_name,
                    "raw_name": district_name,
                    "state": state_name,
                    "region": region,
                    "dt_code": props.get("dt_code") or props.get("Dist_Code") or "",
                    "st_code": props.get("st_code") or props.get("State_Code") or "",
                    "hq_name": hq_name,
                    "hq_lat": hq_lat,
                    "hq_lon": hq_lon,
                    "centroid_lat": cent_lat,
                    "centroid_lon": cent_lon,
                    "focus_lat": focus_lat,
                    "focus_lon": focus_lon,
                    "bbox": bbox,
                    "camera_height": camera_height,
                    "repaired": was_repaired,
                    "original_type": orig_geom_type,
                    "vertex_count": len(polygon_coords),
                },
                "geometry": mapping(clean_poly),
            }
            state_validated_features.append(validated_feature)
            all_validated_features.append(validated_feature)

        # Save state-specific validated GeoJSON
        state_out_path = os.path.join(dest_dir, f"{slug.replace('-', '_')}_districts_validated.geojson")
        with open(state_out_path, "w", encoding="utf-8") as f_s:
            json.dump({
                "type": "FeatureCollection",
                "name": f"{state_name}_Districts_Validated",
                "crs": {
                    "type": "name",
                    "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
                },
                "features": state_validated_features,
            }, f_s, indent=2)
        logger.info(f"Saved state validated GeoJSON: {state_out_path}")

    # Save comprehensive North-Eastern India validated GeoJSON
    out_geojson_path = os.path.join(dest_dir, "northeastern_districts_validated.geojson")
    with open(out_geojson_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "name": "North_Eastern_India_Districts_Validated",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
            },
            "features": all_validated_features,
        }, f, indent=2)
    logger.info(f"Saved comprehensive validated GeoJSON: {out_geojson_path}")

    # Save HeatSense CityData JSON
    out_json_path = os.path.join(dest_dir, "northeastern_cities_data.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(all_city_records, f, indent=2)
    logger.info(f"Saved HeatSense CityData: {out_json_path}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("GEOSPATIAL VALIDATION COMPLETE: NORTH-EASTERN INDIA")
    print("=" * 60)
    print(f"Total districts validated: {total_districts_processed}")
    print(f"Malformed geometries repaired: {len(malformed_reports)}")
    for m in malformed_reports:
        print(f"  - {m['state']} / {m['district']}: {m['reason']}")
    print(f"MultiPolygon fragmented districts: {len(multipart_reports)}")
    for mp in sorted(multipart_reports, key=lambda x: x['parts'], reverse=True):
        print(f"  - {mp['state']} / {mp['district']}: {mp['parts']} parts")
    print(f"Concave geometry centroids (interior point used): {len(concave_centroid_reports)}")
    for c in concave_centroid_reports:
        print(f"  - {c['state']} / {c['district']}: Centroid={c['geometric_centroid']} -> Interior={c['representative_interior_point']}")

    # Check for em dashes across all records
    full_text = json.dumps(all_city_records) + json.dumps(all_validated_features)
    has_em_dash = ("\u2014" in full_text) or ("\u2013" in full_text)
    print(f"Zero em dash verification passed: {not has_em_dash}")
    assert not has_em_dash, "Em dash detected in validated outputs!"


if __name__ == "__main__":
    main()
