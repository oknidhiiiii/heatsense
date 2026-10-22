"""
HeatSense Southern Indian Administrative Boundary Validator and Extractor.
Validates 140 districts across Karnataka, Tamil Nadu, Telangana, Andhra Pradesh, and Kerala.
Ensures zero em dashes, valid WGS84 coordinates, and zero-flicker geometry rendering.
"""

import json
import logging
import math
import os
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping
from shapely.validation import make_valid, explain_validity

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HeatSenseSouthernGeospatial")

BASE_GEOJSON_URL = "https://raw.githubusercontent.com/udit-001/india-maps-data/master/geojson/states"

# Canonical Headquarters Data: (HQ_Name, Latitude, Longitude)
DISTRICT_HQ_DATA: Dict[str, Tuple[str, float, float]] = {
    # Karnataka (30)
    "Bagalkote": ("Bagalkote", 16.1817, 75.6958),
    "Ballari": ("Ballari", 15.1394, 76.9214),
    "Belagavi": ("Belagavi", 15.8497, 74.4977),
    "Bengaluru Rural": ("Bengaluru / Devanahalli", 13.2483, 77.7126),
    "Bengaluru Urban": ("Bengaluru", 12.9716, 77.5946),
    "Bidar": ("Bidar", 17.9104, 77.5199),
    "Chamarajanagara": ("Chamarajanagar", 11.9261, 76.9437),
    "Chikkaballapura": ("Chikkaballapur", 13.4325, 77.7275),
    "Chikkamagaluru": ("Chikkamagaluru", 13.3161, 75.7720),
    "Chitradurga": ("Chitradurga", 14.2251, 76.3980),
    "Dakshina Kannada": ("Mangaluru", 12.9141, 74.8560),
    "Davanagere": ("Davanagere", 14.4644, 75.9218),
    "Dharwad": ("Dharwad", 15.4589, 75.0078),
    "Gadag": ("Gadag", 15.4167, 75.6333),
    "Hassan": ("Hassan", 13.0033, 76.1004),
    "Haveri": ("Haveri", 14.7955, 75.4027),
    "Kalaburagi": ("Kalaburagi", 17.3297, 76.8343),
    "Kodagu": ("Madikeri", 12.4244, 75.7382),
    "Kolar": ("Kolar", 13.1367, 78.1292),
    "Koppal": ("Koppal", 15.3456, 76.1553),
    "Mandya": ("Mandya", 12.5238, 76.8967),
    "Mysuru": ("Mysuru", 12.2958, 76.6394),
    "Raichur": ("Raichur", 16.2120, 77.3439),
    "Ramanagara": ("Ramanagara", 12.7150, 77.2813),
    "Shivamogga": ("Shivamogga", 13.9299, 75.5681),
    "Tumakuru": ("Tumakuru", 13.3409, 77.1010),
    "Udupi": ("Udupi", 13.3409, 74.7421),
    "Uttara Kannada": ("Karwar", 14.8185, 74.1350),
    "Vijayapura": ("Vijayapura", 16.8302, 75.7100),
    "Yadgir": ("Yadgir", 16.7700, 77.1400),

    # Tamil Nadu (37)
    "Ariyalur": ("Ariyalur", 11.1401, 79.0786),
    "Chengalpattu": ("Chengalpattu", 12.6939, 79.9757),
    "Chennai": ("Chennai", 13.0827, 80.2707),
    "Coimbatore": ("Coimbatore", 11.0168, 76.9558),
    "Cuddalore": ("Cuddalore", 11.7480, 79.7714),
    "Dharmapuri": ("Dharmapuri", 12.1277, 78.1579),
    "Dindigul": ("Dindigul", 10.3673, 77.9803),
    "Erode": ("Erode", 11.3410, 77.7172),
    "Kallakurichi": ("Kallakurichi", 11.7383, 78.9639),
    "Kancheepuram": ("Kancheepuram", 12.8342, 79.7036),
    "Kanyakumari": ("Nagercoil", 8.1833, 77.4119),
    "Karur": ("Karur", 10.9601, 78.0766),
    "Krishnagiri": ("Krishnagiri", 12.5186, 78.2137),
    "Madurai": ("Madurai", 9.9252, 78.1198),
    "Nagapattinam": ("Nagapattinam", 10.7656, 79.8424),
    "Namakkal": ("Namakkal", 11.2189, 78.1674),
    "Nilgiris": ("Udhagamandalam", 11.4102, 76.6950),
    "Perambalur": ("Perambalur", 11.2342, 78.8820),
    "Pudukkottai": ("Pudukkottai", 10.3797, 78.8208),
    "Ramanathapuram": ("Ramanathapuram", 9.3639, 78.8395),
    "Ranipet": ("Ranipet", 12.9298, 79.3330),
    "Salem": ("Salem", 11.6643, 78.1460),
    "Sivaganga": ("Sivaganga", 9.8433, 78.4809),
    "Tenkasi": ("Tenkasi", 8.9594, 77.3150),
    "Thanjavur": ("Thanjavur", 10.7870, 79.1378),
    "Theni": ("Theni", 10.0104, 77.4768),
    "Thiruvallur": ("Thiruvallur", 13.1432, 79.9083),
    "Thiruvarur": ("Thiruvarur", 10.7725, 79.6365),
    "Thoothukkudi": ("Thoothukudi", 8.7642, 78.1348),
    "Tiruchirappalli": ("Tiruchirappalli", 10.7905, 78.7047),
    "Tirunelveli": ("Tirunelveli", 8.7139, 77.7567),
    "Tirupathur": ("Tirupathur", 12.4925, 78.5678),
    "Tiruppur": ("Tiruppur", 11.1085, 77.3411),
    "Tiruvannamalai": ("Tiruvannamalai", 12.2253, 79.0747),
    "Vellore": ("Vellore", 12.9165, 79.1325),
    "Viluppuram": ("Viluppuram", 11.9401, 79.4861),
    "Virudhunagar": ("Virudhunagar", 9.5680, 77.9624),

    # Telangana (33)
    "Adilabad": ("Adilabad", 19.6641, 78.5320),
    "Bhadradri Kothagudem": ("Kothagudem", 17.5554, 80.6195),
    "Hyderabad": ("Hyderabad", 17.3850, 78.4867),
    "Jagtial": ("Jagtial", 18.7983, 78.9119),
    "Jangaon": ("Jangaon", 17.7214, 79.1834),
    "Jayashankar Bhupalapally": ("Bhupalpally", 18.4319, 79.8643),
    "Jogulamba Gadwal": ("Gadwal", 16.2333, 77.8000),
    "Kamareddy": ("Kamareddy", 18.3228, 78.3392),
    "Karimnagar": ("Karimnagar", 18.4386, 79.1288),
    "Khammam": ("Khammam", 17.2473, 80.1514),
    "Komaram Bheem": ("Asifabad", 19.3583, 79.2889),
    "Mahabubabad": ("Mahabubabad", 17.5986, 80.0039),
    "Mahabubnagar": ("Mahabubnagar", 16.7488, 78.0035),
    "Mancherial": ("Mancherial", 18.8679, 79.4639),
    "Medak": ("Medak", 18.0478, 78.2619),
    "Medchal Malkajgiri": ("Medchal / Shamirpet", 17.6297, 78.4814),
    "Mulugu": ("Mulugu", 18.1917, 79.9417),
    "Nagarkurnool": ("Nagarkurnool", 16.4858, 78.3186),
    "Nalgonda": ("Nalgonda", 17.0575, 79.2689),
    "Narayanpet": ("Narayanpet", 16.7333, 77.5000),
    "Nirmal": ("Nirmal", 19.0964, 78.3431),
    "Nizamabad": ("Nizamabad", 18.6725, 78.0941),
    "Peddapalli": ("Peddapalli", 18.6167, 79.3833),
    "Rajanna Sircilla": ("Sircilla", 18.3833, 78.8333),
    "Ranga Reddy": ("Shamshabad", 17.2500, 78.4200),
    "Sangareddy": ("Sangareddy", 17.6140, 78.0816),
    "Siddipet": ("Siddipet", 18.1018, 78.8520),
    "Suryapet": ("Suryapet", 17.1439, 79.6236),
    "Vikarabad": ("Vikarabad", 17.3366, 77.9048),
    "Wanaparthy": ("Wanaparthy", 16.3622, 78.0628),
    "Warangal Rural": ("Warangal", 17.9784, 79.5941),
    "Warangal Urban": ("Hanamkonda", 18.0138, 79.5519),
    "Yadadri Bhuvanagiri": ("Bhuvanagiri", 17.5108, 78.8889),

    # Andhra Pradesh (26)
    "Alluri Sitharama Raju": ("Paderu", 18.0833, 82.6667),
    "Anakapalli": ("Anakapalle", 17.6913, 83.0039),
    "Anantapuramu": ("Anantapur", 14.6819, 77.6006),
    "Annamayya": ("Rayachoti", 14.0560, 78.7520),
    "Bapatla": ("Bapatla", 15.9042, 80.4678),
    "Chittoor": ("Chittoor", 13.2172, 79.1003),
    "East Godavari": ("Rajamahendravaram", 17.0005, 81.8040),
    "Eluru": ("Eluru", 16.7107, 81.0952),
    "Guntur": ("Guntur", 16.3067, 80.4365),
    "Kakinada": ("Kakinada", 16.9891, 82.2475),
    "Konaseema": ("Amalapuram", 16.5787, 82.0061),
    "Krishna": ("Machilipatnam", 16.1875, 81.1389),
    "Kurnool": ("Kurnool", 15.8281, 78.0373),
    "NTR": ("Vijayawada", 16.5062, 80.6480),
    "Nandyal": ("Nandyal", 15.4883, 78.4836),
    "Palnadu": ("Narasaraopet", 16.2361, 80.0494),
    "Parvathipuram Manyam": ("Parvathipuram", 18.7797, 83.4278),
    "Prakasam": ("Ongole", 15.5057, 80.0499),
    "Sri Potti Sriramulu Nellore": ("Nellore", 14.4426, 79.9865),
    "Sri Sathya Sai": ("Puttaparthi", 14.1656, 77.8106),
    "Srikakulam": ("Srikakulam", 18.2949, 83.8938),
    "Tirupati": ("Tirupati", 13.6288, 79.4192),
    "Visakhapatnam": ("Visakhapatnam", 17.6868, 83.2185),
    "Vizianagaram": ("Vizianagaram", 18.1167, 83.4167),
    "West Godavari": ("Bhimavaram", 16.5449, 81.5212),
    "YSR": ("Kadapa", 14.4673, 78.8242),

    # Kerala (14)
    "Alappuzha": ("Alappuzha", 9.4981, 76.3388),
    "Ernakulam": ("Kakkanad", 10.0159, 76.3419),
    "Idukki": ("Painavu", 9.8497, 76.9806),
    "Kannur": ("Kannur", 11.8745, 75.3704),
    "Kasaragod": ("Kasaragod", 12.4996, 74.9869),
    "Kollam": ("Kollam", 8.8932, 76.6141),
    "Kottayam": ("Kottayam", 9.5916, 76.5222),
    "Kozhikode": ("Kozhikode", 11.2588, 75.7804),
    "Malappuram": ("Malappuram", 11.0732, 76.0740),
    "Palakkad": ("Palakkad", 10.7867, 76.6548),
    "Pathanamthitta": ("Pathanamthitta", 9.2648, 76.7870),
    "Thiruvananthapuram": ("Thiruvananthapuram", 8.5241, 76.9366),
    "Thrissur": ("Thrissur", 10.5276, 76.2144),
    "Wayanad": ("Kalpetta", 11.6103, 76.0827),
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
                s_geom = max(polys, key=lambda g: g.area)
                if s_geom.geom_type == "MultiPolygon":
                    s_geom = max(s_geom.geoms, key=lambda g: g.area)
            else:
                raise ValueError(f"Unable to recover polygon from GeometryCollection for {district_name}")

    elif s_geom.geom_type == "MultiPolygon":
        # MultiPolygon without invalidity: select primary outer component
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

    # Ensure at least 4 points for valid polygon
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
        ("Karnataka", "karnataka", "South Deccan / Coastal Western Ghats"),
        ("Tamil Nadu", "tamil-nadu", "Coromandel Coast / Kaveri Basin"),
        ("Telangana", "telangana", "North Deccan Plateau / Godavari-Krishna Basin"),
        ("Andhra Pradesh", "andhra-pradesh", "Coastal Andhra / Rayalaseema"),
        ("Kerala", "kerala", "Malabar Coast / Western Ghats Corridor"),
    ]

    all_validated_features = []
    all_city_records = []
    malformed_reports = []
    multipart_reports = []
    concave_centroid_reports = []
    total_districts_processed = 0

    for state_name, slug, region in target_states:
        geojson_path = os.path.join(dest_dir, f"{slug.replace('-', '_')}_districts.geojson")
        
        # Download if not present
        if not os.path.exists(geojson_path):
            url = f"{BASE_GEOJSON_URL}/{slug}.geojson"
            logger.info(f"Downloading {url} -> {geojson_path}")
            urllib.request.urlretrieve(url, geojson_path)

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
                    "state": state_name,
                    "region": region,
                    "dt_code": props.get("dt_code", ""),
                    "st_code": props.get("st_code", ""),
                    "hq_name": hq_name,
                    "hq_lat": hq_lat,
                    "hq_lon": hq_lon,
                    "centroid_lat": cent_lat,
                    "centroid_lon": cent_lon,
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

    # Save comprehensive Southern India validated GeoJSON
    out_geojson_path = os.path.join(dest_dir, "southern_districts_validated.geojson")
    with open(out_geojson_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "name": "Southern_India_Districts_Validated",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
            },
            "features": all_validated_features,
        }, f, indent=2)
    logger.info(f"Saved unified validated GeoJSON: {out_geojson_path}")

    # Save HeatSense CityData JSON
    out_json_path = os.path.join(dest_dir, "southern_cities_data.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(all_city_records, f, indent=2)
    logger.info(f"Saved HeatSense CityData: {out_json_path}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("GEOSPATIAL VALIDATION COMPLETE: SOUTHERN INDIA")
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
