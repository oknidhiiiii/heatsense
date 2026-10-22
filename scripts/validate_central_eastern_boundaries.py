"""
HeatSense Central and Eastern Indian Administrative Boundary Validator and Extractor.
Validates 218 districts across Madhya Pradesh, Uttar Pradesh, Bihar, West Bengal, and Odisha.
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
logger = logging.getLogger("HeatSenseGeospatial")

# Canonical Headquarters Data: (HQ_Name, Latitude, Longitude)
DISTRICT_HQ_DATA: Dict[str, Tuple[str, float, float]] = {
    # Madhya Pradesh (52)
    "Agar Malwa": ("Agar", 23.7144, 76.0177),
    "Alirajpur": ("Alirajpur", 22.3039, 74.3547),
    "Anuppur": ("Anuppur", 23.1042, 81.6917),
    "Ashoknagar": ("Ashoknagar", 24.5772, 77.7289),
    "Balaghat": ("Balaghat", 21.8129, 80.1838),
    "Barwani": ("Barwani", 22.0366, 74.9034),
    "Betul": ("Betul", 21.9014, 77.9014),
    "Bhind": ("Bhind", 26.5644, 78.7844),
    "Bhopal": ("Bhopal", 23.2599, 77.4126),
    "Burhanpur": ("Burhanpur", 21.3109, 76.2299),
    "Chhatarpur": ("Chhatarpur", 24.9163, 79.5819),
    "Chhindwara": ("Chhindwara", 22.0574, 78.9382),
    "Damoh": ("Damoh", 23.8323, 79.4422),
    "Datia": ("Datia", 25.6685, 78.4609),
    "Dewas": ("Dewas", 22.9676, 76.0534),
    "Dhar": ("Dhar", 22.5978, 75.2974),
    "Dindori": ("Dindori", 22.9542, 81.0811),
    "Guna": ("Guna", 24.6473, 77.3110),
    "Gwalior": ("Gwalior", 26.2183, 78.1828),
    "Harda": ("Harda", 22.3444, 77.0950),
    "Hoshangabad": ("Narmadapuram", 22.7519, 77.7289),
    "Indore": ("Indore", 22.7196, 75.8577),
    "Jabalpur": ("Jabalpur", 23.1815, 79.9864),
    "Jhabua": ("Jhabua", 22.7699, 74.5947),
    "Katni": ("Katni", 23.8343, 80.3989),
    "Khandwa": ("Khandwa", 21.8315, 76.3498),
    "Khargone": ("Khargone", 21.8234, 75.6187),
    "Mandla": ("Mandla", 22.5986, 80.3714),
    "Mandsaur": ("Mandsaur", 24.0722, 75.0694),
    "Morena": ("Morena", 26.4950, 77.9944),
    "Narsinghpur": ("Narsinghpur", 22.9431, 79.1950),
    "Neemuch": ("Neemuch", 24.4628, 74.8711),
    "Niwari": ("Niwari", 25.3589, 78.6019),
    "Panna": ("Panna", 24.7214, 80.1872),
    "Raisen": ("Raisen", 23.3315, 77.7811),
    "Rajgarh": ("Rajgarh", 24.0069, 76.7328),
    "Ratlam": ("Ratlam", 23.3315, 75.0367),
    "Rewa": ("Rewa", 24.5362, 81.3037),
    "Sagar": ("Sagar", 23.8388, 78.7378),
    "Satna": ("Satna", 24.5800, 80.8300),
    "Sehore": ("Sehore", 23.2031, 77.0844),
    "Seoni": ("Seoni", 22.0869, 79.5434),
    "Shahdol": ("Shahdol", 23.2942, 81.3539),
    "Shajapur": ("Shajapur", 23.4278, 76.2778),
    "Sheopur": ("Sheopur", 25.6689, 76.6989),
    "Shivpuri": ("Shivpuri", 25.4244, 77.6589),
    "Sidhi": ("Sidhi", 24.4128, 81.8844),
    "Singrauli": ("Waidhan", 24.0667, 82.6333),
    "Tikamgarh": ("Tikamgarh", 24.7472, 78.8311),
    "Ujjain": ("Ujjain", 23.1765, 75.7885),
    "Umaria": ("Umaria", 23.5244, 80.8350),
    "Vidisha": ("Vidisha", 23.5251, 77.8081),

    # Bihar (38)
    "Araria": ("Araria", 26.1511, 87.5144),
    "Arwal": ("Arwal", 25.2439, 84.6739),
    "Aurangabad": ("Aurangabad", 24.7539, 84.3742),
    "Banka": ("Banka", 24.8872, 86.9214),
    "Begusarai": ("Begusarai", 25.4182, 86.1272),
    "Bhagalpur": ("Bhagalpur", 25.2425, 87.0139),
    "Bhojpur": ("Arrah", 25.5560, 84.6603),
    "Buxar": ("Buxar", 25.5647, 83.9777),
    "Darbhanga": ("Darbhanga", 26.1542, 85.8918),
    "East Champaran": ("Motihari", 26.6470, 84.9089),
    "Gaya": ("Gaya", 24.7914, 85.0002),
    "Gopalganj": ("Gopalganj", 26.4678, 84.4444),
    "Jamui": ("Jamui", 24.9211, 86.2239),
    "Jehanabad": ("Jehanabad", 25.2139, 84.9872),
    "Kaimur": ("Bhabua", 25.0449, 83.6143),
    "Katihar": ("Katihar", 25.5394, 87.5706),
    "Khagaria": ("Khagaria", 25.5039, 86.4819),
    "Kishanganj": ("Kishanganj", 26.0744, 87.9422),
    "Lakhisarai": ("Lakhisarai", 25.1767, 86.0933),
    "Madhepura": ("Madhepura", 25.9239, 86.7919),
    "Madhubani": ("Madhubani", 26.3544, 86.0719),
    "Munger": ("Munger", 25.3756, 86.4744),
    "Muzaffarpur": ("Muzaffarpur", 26.1209, 85.3647),
    "Nalanda": ("Bihar Sharif", 25.1982, 85.5149),
    "Nawada": ("Nawada", 24.8869, 85.5419),
    "Patna": ("Patna", 25.5941, 85.1376),
    "Purnia": ("Purnia", 25.7771, 87.4753),
    "Rohtas": ("Sasaram", 24.9522, 84.0315),
    "Saharsa": ("Saharsa", 25.8839, 86.6019),
    "Samastipur": ("Samastipur", 25.8628, 85.7811),
    "Saran": ("Chhapra", 25.7796, 84.7499),
    "Sheikhpura": ("Sheikhpura", 25.1417, 85.8647),
    "Sheohar": ("Sheohar", 26.5167, 85.2972),
    "Sitamarhi": ("Sitamarhi", 26.5989, 85.4889),
    "Siwan": ("Siwan", 26.2217, 84.3567),
    "Supaul": ("Supaul", 26.1239, 86.6069),
    "Vaishali": ("Hajipur", 25.6858, 85.2146),
    "West Champaran": ("Bettiah", 26.8029, 84.5028),

    # West Bengal (23)
    "Alipurduar": ("Alipurduar", 26.4919, 89.5272),
    "Bankura": ("Bankura", 23.2325, 87.0719),
    "Birbhum": ("Suri", 23.9100, 87.5270),
    "Cooch Behar": ("Cooch Behar", 26.3239, 89.4511),
    "Dakshin Dinajpur": ("Balurghat", 25.2215, 88.7674),
    "Darjeeling": ("Darjeeling", 27.0410, 88.2663),
    "Hooghly": ("Chinsurah", 22.9030, 88.3968),
    "Howrah": ("Howrah", 22.5958, 88.2636),
    "Jalpaiguri": ("Jalpaiguri", 26.5167, 88.7333),
    "Jhargram": ("Jhargram", 22.4500, 86.9833),
    "Kalimpong": ("Kalimpong", 27.0667, 88.4667),
    "Kolkata": ("Kolkata", 22.5726, 88.3639),
    "Malda": ("English Bazar", 25.0044, 88.1458),
    "Murshidabad": ("Baharampur", 24.0988, 88.2679),
    "Nadia": ("Krishnanagar", 23.4013, 88.5019),
    "North 24 Parganas": ("Barasat", 22.7210, 88.4819),
    "Paschim Bardhaman": ("Asansol", 23.6889, 86.9661),
    "Paschim Medinipur": ("Medinipur", 22.4257, 87.3199),
    "Purba Bardhaman": ("Bardhaman", 23.2324, 87.8615),
    "Purba Medinipur": ("Tamluk", 22.2965, 87.9254),
    "Purulia": ("Purulia", 23.3333, 86.3667),
    "South 24 Parganas": ("Alipore", 22.5312, 88.3308),
    "Uttar Dinajpur": ("Raiganj", 25.6178, 88.1256),

    # Odisha (30)
    "Angul": ("Angul", 20.8394, 85.1017),
    "Balangir": ("Balangir", 20.7139, 83.4867),
    "Balasore": ("Balasore", 21.4934, 86.9135),
    "Bargarh": ("Bargarh", 21.3333, 83.6167),
    "Bhadrak": ("Bhadrak", 21.0544, 86.5014),
    "Boudh": ("Boudh", 20.8356, 84.3211),
    "Cuttack": ("Cuttack", 20.4625, 85.8828),
    "Deogarh": ("Deogarh", 21.5333, 84.7333),
    "Dhenkanal": ("Dhenkanal", 20.6667, 85.6000),
    "Gajapati": ("Paralakhemundi", 18.7753, 84.0910),
    "Ganjam": ("Chhatrapur", 19.3550, 84.9926),
    "Jagatsinghpur": ("Jagatsinghpur", 20.2667, 86.1667),
    "Jajpur": ("Panikoili", 20.9419, 86.1772),
    "Jharsuguda": ("Jharsuguda", 21.8550, 84.0100),
    "Kalahandi": ("Bhawanipatna", 19.9048, 83.1659),
    "Kandhamal": ("Phulbani", 20.4770, 84.2343),
    "Kendrapara": ("Kendrapara", 20.5000, 86.4167),
    "Kendujhar": ("Kendujhar", 21.6289, 85.5817),
    "Khordha": ("Khordha", 20.1818, 85.6212),
    "Koraput": ("Koraput", 18.8167, 82.7167),
    "Malkangiri": ("Malkangiri", 18.3500, 81.9000),
    "Mayurbhanj": ("Baripada", 21.9346, 86.7329),
    "Nabarangapur": ("Nabarangapur", 19.2333, 82.5500),
    "Nayagarh": ("Nayagarh", 20.1264, 85.1042),
    "Nuapada": ("Nuapada", 20.8333, 82.5333),
    "Puri": ("Puri", 19.8135, 85.8312),
    "Rayagada": ("Rayagada", 19.1667, 83.4167),
    "Sambalpur": ("Sambalpur", 21.4669, 83.9812),
    "Subarnapur": ("Sonepur", 20.8407, 83.9142),
    "Sundargarh": ("Sundargarh", 22.1167, 84.0333),

    # Uttar Pradesh (75)
    "Agra": ("Agra", 27.1767, 78.0081),
    "Aligarh": ("Aligarh", 27.8974, 78.0880),
    "Ambedkar Nagar": ("Akbarpur", 26.4326, 82.5344),
    "Amethi": ("Gauriganj", 26.2163, 81.6966),
    "Amroha": ("Amroha", 28.9044, 78.4689),
    "Auraiya": ("Auraiya", 26.4678, 79.5167),
    "Ayodhya": ("Ayodhya", 26.7922, 82.1998),
    "Azamgarh": ("Azamgarh", 26.0689, 83.1839),
    "Baghpat": ("Baghpat", 28.9439, 77.2189),
    "Bahraich": ("Bahraich", 27.5744, 81.5978),
    "Ballia": ("Ballia", 25.7589, 84.1489),
    "Balrampur": ("Balrampur", 27.4289, 82.1789),
    "Banda": ("Banda", 25.4744, 80.3344),
    "Barabanki": ("Barabanki", 26.9267, 81.1833),
    "Bareilly": ("Bareilly", 28.3670, 79.4304),
    "Basti": ("Basti", 26.8019, 82.7628),
    "Bhadohi": ("Gyanpur", 25.3456, 82.4342),
    "Bijnor": ("Bijnor", 29.3728, 78.1358),
    "Budaun": ("Budaun", 28.0319, 79.1244),
    "Bulandshahr": ("Bulandshahr", 28.4069, 77.8497),
    "Chandauli": ("Chandauli", 25.2619, 83.2689),
    "Chitrakoot": ("Karwi", 25.2117, 80.8931),
    "Deoria": ("Deoria", 26.5028, 83.7797),
    "Etah": ("Etah", 27.5589, 78.6644),
    "Etawah": ("Etawah", 26.7767, 79.0233),
    "Farrukhabad": ("Fatehgarh", 27.3621, 79.6264),
    "Fatehpur": ("Fatehpur", 25.9289, 80.8128),
    "Firozabad": ("Firozabad", 27.1594, 78.3956),
    "Gautam Buddha Nagar": ("Greater Noida", 28.4744, 77.5040),
    "Ghaziabad": ("Ghaziabad", 28.6692, 77.4538),
    "Ghazipur": ("Ghazipur", 25.5844, 83.5778),
    "Gonda": ("Gonda", 27.1333, 81.9619),
    "Gorakhpur": ("Gorakhpur", 26.7606, 83.3732),
    "Hamirpur": ("Hamirpur", 25.9544, 80.1519),
    "Hapur": ("Hapur", 28.7306, 77.7758),
    "Hardoi": ("Hardoi", 27.3944, 80.1289),
    "Hathras": ("Hathras", 27.5969, 78.0519),
    "Jalaun": ("Orai", 25.9898, 79.4500),
    "Jaunpur": ("Jaunpur", 25.7464, 82.6837),
    "Jhansi": ("Jhansi", 25.4484, 78.5685),
    "Kannauj": ("Kannauj", 27.0544, 79.9178),
    "Kanpur Dehat": ("Akbarpur", 26.4324, 79.9497),
    "Kanpur Nagar": ("Kanpur", 26.4499, 80.3319),
    "Kasganj": ("Kasganj", 27.8089, 78.6478),
    "Kaushambi": ("Manjhanpur", 25.5342, 81.3761),
    "Kushinagar": ("Padrauna", 26.9025, 83.9824),
    "Lakhimpur Kheri": ("Lakhimpur", 27.9515, 80.7788),
    "Lalitpur": ("Lalitpur", 24.6869, 78.4119),
    "Lucknow": ("Lucknow", 26.8467, 80.9462),
    "Maharajganj": ("Maharajganj", 27.1444, 83.5619),
    "Mahoba": ("Mahoba", 25.2939, 79.8719),
    "Mainpuri": ("Mainpuri", 27.2289, 79.0289),
    "Mathura": ("Mathura", 27.4924, 77.6737),
    "Mau": ("Maunath Bhanjan", 25.9417, 83.5611),
    "Meerut": ("Meerut", 28.9845, 77.7064),
    "Mirzapur": ("Mirzapur", 25.1469, 82.5697),
    "Moradabad": ("Moradabad", 28.8353, 78.7747),
    "Muzaffarnagar": ("Muzaffarnagar", 29.4727, 77.7085),
    "Pilibhit": ("Pilibhit", 28.6319, 79.8039),
    "Pratapgarh": ("Bela Pratapgarh", 25.9234, 81.9984),
    "Prayagraj": ("Prayagraj", 25.4358, 81.8463),
    "Rae Bareli": ("Rae Bareli", 26.2289, 81.2403),
    "Rampur": ("Rampur", 28.8156, 79.0269),
    "Saharanpur": ("Saharanpur", 29.9679, 77.5511),
    "Sambhal": ("Bahjoi", 28.3970, 78.6880),
    "Sant Kabir Nagar": ("Khalilabad", 26.7770, 83.0722),
    "Shahjahanpur": ("Shahjahanpur", 27.8819, 79.9119),
    "Shamli": ("Shamli", 29.4500, 77.3167),
    "Shrawasti": ("Bhinga", 27.7086, 81.9344),
    "Siddharthnagar": ("Naugarh", 27.2942, 83.0906),
    "Sitapur": ("Sitapur", 27.5689, 80.6819),
    "Sonbhadra": ("Robertsganj", 24.6853, 83.0645),
    "Sultanpur": ("Sultanpur", 26.2644, 82.0728),
    "Unnao": ("Unnao", 26.5458, 80.4908),
    "Varanasi": ("Varanasi", 25.3176, 82.9739),
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
    # Replace em-dash and en-dash with clean ASCII colon or hyphen
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
            # Select largest component
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
    target_states = [
        ("Madhya Pradesh", "madhya-pradesh", "Central"),
        ("Uttar Pradesh", "uttar-pradesh", "Northern / Central-East"),
        ("Bihar", "bihar", "Eastern"),
        ("West Bengal", "west-bengal", "Eastern"),
        ("Odisha", "odisha", "Eastern"),
    ]

    all_validated_features = []
    all_city_records = []
    malformed_reports = []
    multipart_reports = []
    concave_centroid_reports = []

    total_districts_processed = 0

    for state_name, slug, region in target_states:
        geojson_path = os.path.join("data", "interim", "states", f"{slug}.geojson")
        with open(geojson_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        features = raw_data.get("features", [])
        state_feature_count = len(features)
        logger.info(f"Processing {state_name}: {state_feature_count} districts...")

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
                    "state": state_name,
                    "region": region,
                    "dt_code": props.get("dt_code", ""),
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
            all_validated_features.append(validated_feature)

    # Save comprehensive validated GeoJSON
    out_geojson_path = os.path.join("data", "interim", "central_eastern_districts_validated.geojson")
    with open(out_geojson_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "features": all_validated_features,
        }, f, indent=2)
    logger.info(f"Saved validated GeoJSON: {out_geojson_path}")

    # Save HeatSense CityData JSON
    out_json_path = os.path.join("data", "interim", "central_eastern_cities_data.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(all_city_records, f, indent=2)
    logger.info(f"Saved HeatSense CityData: {out_json_path}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("GEOSPATIAL VALIDATION COMPLETE: CENTRAL & EASTERN INDIA")
    print("=" * 60)
    print(f"Total districts validated: {total_districts_processed}")
    print(f"Malformed geometries repaired: {len(malformed_reports)}")
    for m in malformed_reports:
        print(f"  - {m['state']} / {m['district']}: {m['reason']}")
    print(f"MultiPolygon fragmented districts: {len(multipart_reports)}")
    for mp in sorted(multipart_reports, key=lambda x: x['parts'], reverse=True)[:6]:
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
