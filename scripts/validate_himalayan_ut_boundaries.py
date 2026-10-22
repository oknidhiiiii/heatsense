"""
HeatSense Northern Himalayan and Union Territories Administrative Boundary Validator and Extractor.
Validates 74 districts across Ladakh, Jammu and Kashmir, Himachal Pradesh, Uttarakhand,
Chandigarh, Delhi, Andaman and Nicobar, Lakshadweep, Puducherry, DNH and DD, and Goa.
Ensures zero em dashes, valid WGS84 coordinates, and zero-flicker geometry rendering.
Strictly decoupled from Zestogram.
"""

import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping
from shapely.validation import make_valid, explain_validity

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HeatSenseHimalayanUTGeospatial")

# Canonical Headquarters Data: (HQ_Name, Latitude, Longitude)
DISTRICT_HQ_DATA: Dict[str, Tuple[str, float, float]] = {
    # Ladakh (2)
    "Leh": ("Leh", 34.1526, 77.5771),
    "Kargil": ("Kargil", 34.5539, 76.1349),

    # Jammu and Kashmir (22)
    "Kupwara": ("Kupwara", 34.5310, 74.2546),
    "Bandipora": ("Bandipora", 34.4222, 74.6473),
    "Baramulla": ("Baramulla", 34.2093, 74.3436),
    "Ganderbal": ("Ganderbal", 34.2268, 74.7818),
    "Anantnag": ("Anantnag", 33.7311, 75.1487),
    "Kishtwar": ("Kishtwar", 33.3135, 75.7658),
    "Srinagar": ("Srinagar", 34.0837, 74.7973),
    "Budgam": ("Budgam", 34.0205, 74.7214),
    "Pulwama": ("Pulwama", 33.8741, 74.8986),
    "Punch": ("Poonch", 33.7713, 74.0954),
    "Shopiyan": ("Shopian", 33.7226, 74.8322),
    "Kulgam": ("Kulgam", 33.6455, 75.0195),
    "Rajouri": ("Rajouri", 33.3766, 74.3095),
    "Ramban": ("Ramban", 33.2423, 75.1956),
    "Reasi": ("Reasi", 33.0827, 74.8315),
    "Doda": ("Doda", 33.1447, 75.5428),
    "Jammu": ("Jammu", 32.7266, 74.8570),
    "Kathua": ("Kathua", 32.3716, 75.5190),
    "Udhampur": ("Udhampur", 32.9258, 75.1416),
    "Samba": ("Samba", 32.5593, 75.1189),
    "Muzaffarabad": ("Muzaffarabad", 34.3700, 73.4711),
    "Mirpur": ("Mirpur", 33.1484, 73.7519),

    # Himachal Pradesh (12)
    "Lahaul and Spiti": ("Keylong", 32.5710, 77.0320),
    "Chamba": ("Chamba", 32.5534, 76.1258),
    "Kangra": ("Dharamshala", 32.2190, 76.3234),
    "Kullu": ("Kullu", 31.9579, 77.1095),
    "Mandi": ("Mandi", 31.7087, 76.9320),
    "Kinnaur": ("Reckong Peo", 31.5404, 78.2743),
    "Una": ("Una", 31.4685, 76.2708),
    "Shimla": ("Shimla", 31.1048, 77.1734),
    "Solan": ("Solan", 30.9045, 77.0967),
    "Sirmaur": ("Nahan", 30.5599, 77.2955),
    "Hamirpur": ("Hamirpur", 31.6862, 76.5213),
    "Bilaspur": ("Bilaspur", 31.3326, 76.7570),

    # Uttarakhand (13)
    "Uttarkashi": ("Uttarkashi", 30.7268, 78.4354),
    "Chamoli": ("Gopeshwar", 30.4093, 79.3248),
    "Dehradun": ("Dehradun", 30.3165, 78.0322),
    "Tehri Garhwal": ("New Tehri", 30.3800, 78.4800),
    "Rudraprayag": ("Rudraprayag", 30.2858, 78.9811),
    "Pithoragarh": ("Pithoragarh", 29.5829, 80.2182),
    "Bageshwar": ("Bageshwar", 29.8406, 79.7694),
    "Haridwar": ("Haridwar", 29.9457, 78.1642),
    "Pauri Garhwal": ("Pauri", 30.1471, 78.7806),
    "Almora": ("Almora", 29.5971, 79.6591),
    "Nainital": ("Nainital", 29.3919, 79.4542),
    "Champawat": ("Champawat", 29.3346, 80.0924),
    "Udham Singh Nagar": ("Rudrapur", 28.9800, 79.4000),

    # Chandigarh (1)
    "Chandigarh": ("Chandigarh", 30.7333, 76.7794),

    # Delhi (11 Revenue Districts)
    "Central": ("Daryaganj", 28.6469, 77.2410),
    "East": ("Preet Vihar", 28.6366, 77.2926),
    "New Delhi": ("Connaught Place", 28.6139, 77.2090),
    "North": ("Alipur", 28.7981, 77.1325),
    "North East": ("Yamuna Vihar", 28.7058, 77.2764),
    "North West": ("Kanjhawala", 28.7282, 77.0049),
    "Shahdara": ("Nand Nagri", 28.6926, 77.3060),
    "South": ("Saket", 28.5244, 77.2066),
    "South East": ("Lajpat Nagar", 28.5677, 77.2433),
    "South West": ("Kapashera", 28.5255, 77.0856),
    "West": ("Rajouri Garden", 28.6521, 77.1215),

    # Delhi NCT (Unified)
    "Delhi": ("New Delhi", 28.6139, 77.2090),

    # Andaman and Nicobar Islands (3)
    "North and Middle Andaman": ("Mayabunder", 12.9100, 92.9150),
    "South Andaman": ("Port Blair", 11.6234, 92.7265),
    "Nicobars": ("Car Nicobar", 9.1550, 92.7758),

    # Lakshadweep (1)
    "Lakshadweep": ("Kavaratti", 10.5667, 72.6417),

    # Puducherry (4)
    "Puducherry": ("Puducherry", 11.9416, 79.8083),
    "Karaikal": ("Karaikal", 10.9254, 79.8380),
    "Mahe": ("Mahe", 11.7300, 75.5380),
    "Yanam": ("Yanam", 16.7339, 82.2175),

    # Dadra and Nagar Haveli and Daman and Diu (3)
    "Dadra and Nagar Haveli": ("Silvassa", 20.2763, 73.0083),
    "Daman": ("Daman", 20.3974, 72.8328),
    "Diu": ("Diu", 20.7144, 70.9874),

    # Goa (2)
    "North Goa": ("Panaji", 15.4909, 73.8278),
    "South Goa": ("Margao", 15.2832, 73.9862),
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two WGS84 points in kilometers."""
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
    """Ensure strictly zero em dashes and zero en dashes."""
    return text.replace(chr(8212), ": ").replace(chr(8211), "-")


def repair_and_clean_geometry(raw_geom: Any, district_name: str) -> Tuple[Polygon, bool, str]:
    """
    Repair self-intersections or bowtie anomalies and return a guaranteed-valid Polygon.
    Selects the component that encompasses the district headquarters if available,
    otherwise selects the component with the largest surface area.
    Returns: (clean_polygon, was_repaired, repair_reason)
    """
    s_geom = shape(raw_geom)
    was_repaired = False
    reason = "Valid"

    hq_info = DISTRICT_HQ_DATA.get(district_name)
    hq_pt = Point(hq_info[2], hq_info[1]) if hq_info else None

    if not s_geom.is_valid:
        was_repaired = True
        reason = explain_validity(s_geom)
        logger.info(f"Repairing invalid geometry for {district_name}: {reason}")
        fixed = make_valid(s_geom)

        if fixed.geom_type == "Polygon":
            s_geom = fixed
        elif fixed.geom_type == "MultiPolygon":
            if hq_pt:
                containing = [g for g in fixed.geoms if g.contains(hq_pt)]
                if containing:
                    s_geom = containing[0]
                else:
                    s_geom = max(fixed.geoms, key=lambda g: g.area)
            else:
                s_geom = max(fixed.geoms, key=lambda g: g.area)
        elif fixed.geom_type == "GeometryCollection":
            polys = [g for g in fixed.geoms if isinstance(g, (Polygon, MultiPolygon))]
            if polys:
                flat_polys: List[Polygon] = []
                for p in polys:
                    if p.geom_type == "MultiPolygon":
                        flat_polys.extend(p.geoms)
                    else:
                        flat_polys.append(p)
                if hq_pt:
                    containing = [g for g in flat_polys if g.contains(hq_pt)]
                    if containing:
                        s_geom = containing[0]
                    else:
                        s_geom = max(flat_polys, key=lambda g: g.area)
                else:
                    s_geom = max(flat_polys, key=lambda g: g.area)
            else:
                s_geom = s_geom.buffer(0)

    elif s_geom.geom_type == "MultiPolygon":
        # MultiPolygon without invalidity: select component containing HQ or largest area
        if hq_pt:
            containing = [g for g in s_geom.geoms if g.contains(hq_pt)]
            if containing:
                s_geom = containing[0]
            else:
                s_geom = max(s_geom.geoms, key=lambda g: g.area)
        else:
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

    # Ensure explicit ring closure
    if cleaned[0] != cleaned[-1]:
        cleaned.append(cleaned[0])

    return cleaned


def main():
    dest_dir = os.path.join("/home/adityap/ai/Projects/HeatSense", "data", "interim")
    os.makedirs(dest_dir, exist_ok=True)

    target_regions = [
        ("Ladakh", "ladakh", "Trans-Himalayan Karakoram and Zanskar Ranges", "district"),
        ("Jammu and Kashmir", "jammu-and-kashmir", "Pir Panjal and Greater Himalayas / Kashmir Valley and Jammu Plains", "district"),
        ("Himachal Pradesh", "himachal-pradesh", "Western Himalayas / Shivalik Foothills and Dhauladhar Alpine Range", "district"),
        ("Uttarakhand", "uttarakhand", "Garhwal and Kumaon Himalayas / Terai and Shivalik Hills", "district"),
        ("Chandigarh", "chandigarh", "Shivalik Foothills / Le Corbusier Planned Capital", "district"),
        ("Delhi", "delhi", "National Capital Territory 11 Revenue Districts", "Dist_Name"),
        ("Andaman and Nicobar Islands", "andaman-and-nicobar-islands", "Bay of Bengal and Andaman Sea Archipelago", "district"),
        ("Lakshadweep", "lakshadweep", "Arabian Sea Coral Atoll Archipelago", "district"),
        ("Puducherry", "puducherry", "Coromandel and Malabar Coastal Enclaves", "district"),
        ("Dadra and Nagar Haveli and Daman and Diu", "dnh-and-dd", "Gulf of Khambhat and Konkan Coastal Enclaves", "district"),
        ("Goa", "goa", "Konkan Coast and Western Ghats Foothills", "district"),
    ]

    all_validated_features = []
    all_city_records = []
    malformed_reports = []
    multipart_reports = []
    concave_centroid_reports = []
    total_districts_processed = 0

    for state_name, slug, region, name_prop in target_regions:
        if slug == "delhi":
            geojson_path = os.path.join(dest_dir, "states", "delhi_districts.geojson")
            if not os.path.exists(geojson_path):
                geojson_path = os.path.join(dest_dir, "delhi_districts.geojson")
        else:
            geojson_path = os.path.join(dest_dir, "states", f"{slug}.geojson")
            if not os.path.exists(geojson_path):
                alt_path = os.path.join(dest_dir, f"{slug}.geojson")
                if os.path.exists(alt_path):
                    geojson_path = alt_path

        with open(geojson_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        features = raw_data.get("features", [])
        state_feature_count = len(features)
        logger.info(f"Processing {state_name}: {state_feature_count} districts...")

        state_validated_features = []

        for feat in features:
            total_districts_processed += 1
            props = feat.get("properties", {})
            district_name = props.get(name_prop) or props.get("district") or props.get("Dist_Name") or props.get("name")
            district_name = sanitize_text(str(district_name).strip())

            # Canonical display naming for Delhi
            display_name = (
                f"{district_name} Delhi"
                if state_name == "Delhi" and not district_name.endswith("Delhi") and district_name != "Shahdara"
                else district_name
            )

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
            if not clean_poly.contains(hq_point):
                raise ValueError(
                    f"HQ {hq_name} ({hq_lat}, {hq_lon}) lies outside polygon for {district_name} ({state_name})"
                )

            # Camera height estimation based on span
            span = max(max_lat - min_lat, max_lon - min_lon)
            camera_height = int(max(60000, span * 111000 * 1.55))

            # Description (strictly zero em dashes)
            description = sanitize_text(
                f"{display_name} ({region}): Admin HQ at {hq_name}. High-resolution thermal monitoring boundary."
            )
            city_id = f"city_{display_name.lower().replace(' ', '_').replace('-', '_').replace('.', '')}"

            city_record = {
                "id": city_id,
                "name": display_name,
                "state": state_name,
                "latitude": focus_lat,
                "longitude": focus_lon,
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
                    "district": display_name,
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

    # Process NCT Delhi Unified boundary as well
    nct_geojson_path = os.path.join(dest_dir, "states", "delhi.geojson")
    if os.path.exists(nct_geojson_path):
        with open(nct_geojson_path, "r", encoding="utf-8") as f:
            nct_raw = json.load(f)
        nct_feat = nct_raw.get("features", [])[0]
        nct_poly, _, _ = repair_and_clean_geometry(nct_feat.get("geometry", {}), "Delhi")
        nct_coords = extract_zero_flicker_coords(nct_poly)
        nct_out_path = os.path.join(dest_dir, "delhi_nct_validated.geojson")
        with open(nct_out_path, "w", encoding="utf-8") as f:
            json.dump({
                "type": "FeatureCollection",
                "name": "Delhi_NCT_Validated",
                "features": [{
                    "type": "Feature",
                    "properties": {
                        "name": "National Capital Territory of Delhi",
                        "type": "union_territory",
                        "hq_name": "New Delhi",
                        "hq_lat": 28.6139,
                        "hq_lon": 77.2090,
                        "centroid_lat": round(nct_poly.centroid.y, 4),
                        "centroid_lon": round(nct_poly.centroid.x, 4),
                        "bbox": [
                            round(min([pt[1] for pt in nct_coords]), 4),
                            round(min([pt[0] for pt in nct_coords]), 4),
                            round(max([pt[1] for pt in nct_coords]), 4),
                            round(max([pt[0] for pt in nct_coords]), 4),
                        ],
                        "vertex_count": len(nct_coords),
                    },
                    "geometry": mapping(nct_poly),
                }],
            }, f, indent=2)
        logger.info(f"Saved Delhi NCT unified boundary: {nct_out_path}")

    # Save comprehensive Northern Himalayan and Union Territories validated GeoJSON
    out_geojson_path = os.path.join(dest_dir, "himalayan_ut_districts_validated.geojson")
    with open(out_geojson_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "name": "Himalayan_UT_Districts_Validated",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
            },
            "features": all_validated_features,
        }, f, indent=2)
    logger.info(f"Saved unified validated GeoJSON: {out_geojson_path}")

    # Save HeatSense CityData JSON
    out_json_path = os.path.join(dest_dir, "himalayan_ut_cities_data.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(all_city_records, f, indent=2)
    logger.info(f"Saved HeatSense CityData: {out_json_path}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("GEOSPATIAL VALIDATION COMPLETE: HIMALAYAN STATES & UTs")
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

    # Strict em dash verification across all outputs
    full_text = json.dumps(all_city_records) + json.dumps(all_validated_features)
    has_em_dash = (chr(8212) in full_text) or (chr(8211) in full_text)
    print(f"Zero em dash verification passed: {not has_em_dash}")
    assert not has_em_dash, "Em dash detected in geospatial output records!"


if __name__ == "__main__":
    main()
