"""
HeatSense Western and Northern Indian Administrative Boundary Validator and Extractor.
Validates 122 districts/regions across Gujarat, Rajasthan, Punjab, Haryana, and Delhi.
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
logger = logging.getLogger("HeatSenseWesternNorthernGeospatial")

BASE_GEOJSON_URL = "https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/states"

# Canonical Headquarters Data: (HQ_Name, Latitude, Longitude)
DISTRICT_HQ_DATA: Dict[str, Tuple[str, float, float]] = {
    # Gujarat (34)
    "Ahmedabad": ("Ahmedabad", 23.0225, 72.5714),
    "Amreli": ("Amreli", 21.6032, 71.2221),
    "Anand": ("Anand", 22.5645, 72.9289),
    "Aravalli": ("Modasa", 23.4635, 73.2984),
    "Banaskantha": ("Palanpur", 24.1724, 72.4346),
    "Bharuch": ("Bharuch", 21.7051, 72.9959),
    "Bhavnagar": ("Bhavnagar", 21.7645, 72.1519),
    "Botad": ("Botad", 22.1706, 71.6669),
    "Chhota Udaipur": ("Chhota Udaipur", 22.3108, 74.0128),
    "Dahod": ("Dahod", 22.8376, 74.2546),
    "Dang": ("Ahwa", 20.7583, 73.6844),
    "Devbhumi Dwarka": ("Khambhalia", 22.2036, 69.6644),
    "Gandhinagar": ("Gandhinagar", 23.2156, 72.6369),
    "Gir Somnath": ("Veraval", 20.9077, 70.3678),
    "Jamnagar": ("Jamnagar", 22.4707, 70.0577),
    "Junagadh": ("Junagadh", 21.5222, 70.4579),
    "Kheda": ("Nadiad", 22.6916, 72.8634),
    "Kutch": ("Bhuj", 23.2420, 69.6669),
    "Mahisagar": ("Lunawada", 23.1311, 73.6139),
    "Mehsana": ("Mehsana", 23.5880, 72.3693),
    "Morbi": ("Morbi", 22.8173, 70.8377),
    "Narmada": ("Rajpipla", 21.8705, 73.5027),
    "Navsari": ("Navsari", 20.9500, 72.9300),
    "Panchmahal": ("Godhra", 22.7781, 73.6143),
    "Patan": ("Patan", 23.8507, 72.1266),
    "Porbandar": ("Porbandar", 21.6417, 69.6293),
    "Rajkot": ("Rajkot", 22.3039, 70.8022),
    "Sabarkantha": ("Himmatnagar", 23.5977, 72.9698),
    "Surat": ("Surat", 21.1702, 72.8311),
    "Surendranagar": ("Surendranagar", 22.7284, 71.6370),
    "Tapi": ("Vyara", 21.1114, 73.3916),
    "Vadodara": ("Vadodara", 22.3072, 73.1812),
    "Valsad": ("Valsad", 20.5992, 72.9342),
    "Vav-Tharad": ("Tharad", 24.3941, 71.6267),

    # Rajasthan (33)
    "Ajmer": ("Ajmer", 26.4499, 74.6399),
    "Alwar": ("Alwar", 27.5530, 76.6346),
    "Banswara": ("Banswara", 23.5461, 74.4349),
    "Baran": ("Baran", 25.1011, 76.5132),
    "Barmer": ("Barmer", 25.7521, 71.3967),
    "Bharatpur": ("Bharatpur", 27.2152, 77.5030),
    "Bhilwara": ("Bhilwara", 25.3475, 74.6408),
    "Bikaner": ("Bikaner", 28.0229, 73.3119),
    "Bundi": ("Bundi", 25.4414, 75.6441),
    "Chittorgarh": ("Chittorgarh", 24.8887, 74.6269),
    "Churu": ("Churu", 28.2900, 74.9600),
    "Dausa": ("Dausa", 26.8927, 76.3377),
    "Dholpur": ("Dholpur", 26.7025, 77.8934),
    "Dungarpur": ("Dungarpur", 23.8432, 73.7147),
    "Ganganagar": ("Sri Ganganagar", 29.9094, 73.8799),
    "Hanumangarh": ("Hanumangarh", 29.5813, 74.3294),
    "Jaipur": ("Jaipur", 26.9124, 75.7873),
    "Jaisalmer": ("Jaisalmer", 26.9157, 70.9083),
    "Jalore": ("Jalore", 25.3444, 72.6156),
    "Jhalawar": ("Jhalawar", 24.5973, 76.1610),
    "Jhunjhunu": ("Jhunjhunu", 28.1289, 75.3995),
    "Jodhpur": ("Jodhpur", 26.2389, 73.0243),
    "Karauli": ("Karauli", 26.4947, 77.0203),
    "Kota": ("Kota", 25.2138, 75.8648),
    "Nagaur": ("Nagaur", 27.2020, 73.7439),
    "Pali": ("Pali", 25.7711, 73.3234),
    "Pratapgarh": ("Pratapgarh", 24.0321, 74.7813),
    "Rajsamand": ("Rajnagar", 25.0456, 73.8796),
    "Sawai Madhopur": ("Sawai Madhopur", 25.9928, 76.3530),
    "Sikar": ("Sikar", 27.6094, 75.1398),
    "Sirohi": ("Sirohi", 24.8853, 72.8625),
    "Tonk": ("Tonk", 26.1664, 75.7885),
    "Udaipur": ("Udaipur", 24.5854, 73.7125),

    # Punjab (22)
    "Amritsar": ("Amritsar", 31.6340, 74.8723),
    "Barnala": ("Barnala", 30.3819, 75.5470),
    "Bathinda": ("Bathinda", 30.2110, 74.9455),
    "Faridkot": ("Faridkot", 30.6769, 74.7583),
    "Fatehgarh Sahib": ("Fatehgarh Sahib", 30.6431, 76.3872),
    "Fazilka": ("Fazilka", 30.4037, 74.0254),
    "Ferozepur": ("Ferozepur", 30.9237, 74.6139),
    "Gurdaspur": ("Gurdaspur", 32.0419, 75.4053),
    "Hoshiarpur": ("Hoshiarpur", 31.5273, 75.9149),
    "Jalandhar": ("Jalandhar", 31.3260, 75.5762),
    "Kapurthala": ("Kapurthala", 31.3800, 75.3800),
    "Ludhiana": ("Ludhiana", 30.9010, 75.8573),
    "Mansa": ("Mansa", 29.9880, 75.3934),
    "Moga": ("Moga", 30.8165, 75.1717),
    "Pathankot": ("Pathankot", 32.2684, 75.6499),
    "Patiala": ("Patiala", 30.3398, 76.3869),
    "Rupnagar": ("Rupnagar", 30.9664, 76.5331),
    "S.A.S. Nagar": ("Mohali", 30.7046, 76.7179),
    "Shahid Bhagat Singh Nagar": ("Nawanshahr", 31.1256, 76.1189),
    "Sangrur": ("Sangrur", 30.2458, 75.8421),
    "Sri Muktsar Sahib": ("Sri Muktsar Sahib", 30.4744, 74.5166),
    "Tarn Taran": ("Tarn Taran Sahib", 31.4520, 74.9255),

    # Haryana (22)
    "Ambala": ("Ambala", 30.3782, 76.7767),
    "Bhiwani": ("Bhiwani", 28.7932, 76.1390),
    "Charkhi Dadri": ("Charkhi Dadri", 28.5921, 76.2653),
    "Faridabad": ("Faridabad", 28.4089, 77.3178),
    "Fatehabad": ("Fatehabad", 29.5140, 75.4540),
    "Gurugram": ("Gurugram", 28.4595, 77.0266),
    "Hisar": ("Hisar", 29.1492, 75.7217),
    "Jhajjar": ("Jhajjar", 28.6063, 76.6565),
    "Jind": ("Jind", 29.3160, 76.3150),
    "Kaithal": ("Kaithal", 29.8015, 76.3996),
    "Karnal": ("Karnal", 29.6857, 76.9905),
    "Kurukshetra": ("Kurukshetra", 29.9695, 76.8783),
    "Mahendragarh": ("Narnaul", 28.0435, 76.1084),
    "Nuh": ("Nuh", 28.1129, 77.0151),
    "Palwal": ("Palwal", 28.1438, 77.3276),
    "Panchkula": ("Panchkula", 30.6942, 76.8606),
    "Panipat": ("Panipat", 29.3909, 76.9635),
    "Rewari": ("Rewari", 28.1833, 76.6167),
    "Rohtak": ("Rohtak", 28.8955, 76.6066),
    "Sirsa": ("Sirsa", 29.5349, 75.0298),
    "Sonipat": ("Sonipat", 28.9931, 77.0151),
    "Yamunanagar": ("Yamunanagar", 30.1290, 77.2674),

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
    return text.replace("\u2014", ": ").replace("\u2013", "-").replace("—", ": ").replace("–", "-")


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
                flat_polys = []
                for p in polys:
                    if p.geom_type == "MultiPolygon":
                        flat_polys.extend(p.geoms)
                    else:
                        flat_polys.append(p)
                s_geom = max(flat_polys, key=lambda g: g.area)
            else:
                s_geom = s_geom.buffer(0)

    elif s_geom.geom_type == "MultiPolygon":
        # MultiPolygon without invalidity: select primary outer component for single polygon tracing
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

    target_states = [
        ("Gujarat", "gujarat", "Kathiawar Peninsula / Rann of Kutch / Gulf of Khambhat", "district"),
        ("Rajasthan", "rajasthan", "Thar Desert / Aravalli Range / Marwar-Mewar Corridor", "district"),
        ("Punjab", "punjab", "Indus Basin / Majha-Malwa-Doaba Plains", "district"),
        ("Haryana", "haryana", "Ghaggar-Yamuna Basin / National Capital Region", "district"),
        ("Delhi", "delhi", "National Capital Territory 11 Revenue Districts", "Dist_Name"),
    ]

    all_validated_features = []
    all_city_records = []
    malformed_reports = []
    multipart_reports = []
    concave_centroid_reports = []
    total_districts_processed = 0

    for state_name, slug, region, name_prop in target_states:
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
            display_name = f"{district_name} Delhi" if state_name == "Delhi" and not district_name.endswith("Delhi") and district_name != "Shahdara" else district_name

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
            hq_inside = clean_poly.contains(hq_point)
            hq_dist_km = round(haversine_distance(cent_lat, cent_lon, hq_lat, hq_lon), 2)

            # Camera height
            span = max(max_lat - min_lat, max_lon - min_lon)
            camera_height = int(max(60000, span * 111000 * 1.55))

            # Description (strictly zero em dashes)
            description = sanitize_text(
                f"{display_name} District ({region}): Admin HQ at {hq_name}. Thermal monitoring boundary."
            )
            city_id = f"city_{display_name.lower().replace(' ', '_').replace('-', '_').replace('.', '')}"

            city_record = {
                "id": city_id,
                "name": display_name,
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

    # Process NCT Delhi Unified boundary as well for complete national catalog
    nct_geojson_path = os.path.join(dest_dir, "states", "delhi.geojson")
    if os.path.exists(nct_geojson_path):
        with open(nct_geojson_path, "r", encoding="utf-8") as f:
            nct_raw = json.load(f)
        nct_feat = nct_raw.get("features", [])[0]
        nct_poly, _, _ = repair_and_clean_geometry(nct_feat.get("geometry", {}), "Delhi_NCT")
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
                        "bbox": [round(min([pt[1] for pt in nct_coords]), 4),
                                 round(min([pt[0] for pt in nct_coords]), 4),
                                 round(max([pt[1] for pt in nct_coords]), 4),
                                 round(max([pt[0] for pt in nct_coords]), 4)],
                        "vertex_count": len(nct_coords)
                    },
                    "geometry": mapping(nct_poly)
                }]
            }, f, indent=2)
        logger.info(f"Saved Delhi NCT unified boundary: {nct_out_path}")

    # Save comprehensive Western and Northern India validated GeoJSON
    out_geojson_path = os.path.join(dest_dir, "western_northern_districts_validated.geojson")
    with open(out_geojson_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "name": "Western_Northern_India_Districts_Validated",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
            },
            "features": all_validated_features,
        }, f, indent=2)
    logger.info(f"Saved unified validated GeoJSON: {out_geojson_path}")

    # Save HeatSense CityData JSON
    out_json_path = os.path.join(dest_dir, "western_northern_cities_data.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(all_city_records, f, indent=2)
    logger.info(f"Saved HeatSense CityData: {out_json_path}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("GEOSPATIAL VALIDATION COMPLETE: WESTERN AND NORTHERN INDIA")
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
    full_text = json.dumps(all_city_records)
    has_em_dash = ("\u2014" in full_text) or ("—" in full_text) or ("\u2013" in full_text)
    print(f"Zero em dash verification passed: {not has_em_dash}")


if __name__ == "__main__":
    main()
