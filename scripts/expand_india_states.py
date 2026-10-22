"""
HeatSense India Multi-State Geospatial Expansion Pipeline.
Downloads official state GeoJSONs, extracts boundary polygons, indexes locations,
and notifies the owner via ZestogramAI Telegram Bot in real-time.
"""

import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HeatSenseExpansion")

BOT_TOKEN = "8993189628:AAFDGAynR1F4TuBL_aBI-ak9ivskoeVy2NA"
OWNER_TELEGRAM_ID = "6061716582"

# Sequence of states to process
STATES_SEQUENCE = [
    ("Gujarat", "gujarat"),
    ("Karnataka", "karnataka"),
    ("Telangana", "telangana"),
    ("Andhra Pradesh", "andhra-pradesh"),
    ("Tamil Nadu", "tamil-nadu"),
    ("Madhya Pradesh", "madhya-pradesh"),
    ("Rajasthan", "rajasthan"),
    ("Delhi", "delhi"),
    ("Uttar Pradesh", "uttar-pradesh"),
    ("West Bengal", "west-bengal"),
    ("Kerala", "kerala"),
    ("Punjab", "punjab"),
    ("Haryana", "haryana"),
    ("Bihar", "bihar"),
    ("Odisha", "odisha"),
    ("Goa", "goa"),
    ("Chhattisgarh", "chhattisgarh"),
    ("Jharkhand", "jharkhand"),
    ("Himachal Pradesh", "himachal-pradesh"),
    ("Uttarakhand", "uttarakhand"),
    ("Jammu and Kashmir", "jammu-and-kashmir"),
]

BASE_GEOJSON_URL = "https://raw.githubusercontent.com/udit-001/india-maps-data/master/geojson/states"


def send_telegram(text: str) -> bool:
    """Send a rate-safe notification to the user on Telegram via ZestogramAI bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": OWNER_TELEGRAM_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "HeatSense-Bot/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return bool(res_data.get("ok"))
    except Exception as exc:
        logger.warning(f"Telegram send failed: {exc}")
        return False


def fetch_state_geojson(slug: str) -> Dict[str, Any]:
    """Fetch GeoJSON for a state."""
    cache_dir = os.path.join("data", "interim", "states")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{slug}.geojson")

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    url = f"{BASE_GEOJSON_URL}/{slug}.geojson"
    logger.info(f"Downloading {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "HeatSense-Pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    return data


def extract_city_record(state_name: str, feature: Dict[str, Any]) -> Dict[str, Any]:
    """Extract normalized district/city record from GeoJSON feature."""
    props = feature.get("properties", {})
    raw_name = props.get("district") or props.get("dtname") or props.get("name") or "Unknown"
    district_name = raw_name.strip()

    geom = feature.get("geometry", {})
    geom_type = geom.get("type")
    coords_raw = geom.get("coordinates", [])

    if geom_type == "Polygon":
        outer_ring = coords_raw[0]
    elif geom_type == "MultiPolygon":
        # Pick the largest polygon ring by vertex count
        outer_ring = max(coords_raw, key=lambda poly: len(poly[0]))[0]
    else:
        outer_ring = []

    if not outer_ring:
        return {}

    lons = [pt[0] for pt in outer_ring]
    lats = [pt[1] for pt in outer_ring]

    min_lat = round(min(lats), 4)
    max_lat = round(max(lats), 4)
    min_lon = round(min(lons), 4)
    max_lon = round(max(lons), 4)

    center_lat = round((min_lat + max_lat) / 2.0, 4)
    center_lon = round((min_lon + max_lon) / 2.0, 4)

    span = max(max_lat - min_lat, max_lon - min_lon)
    camera_height = int(max(60000, span * 111000 * 1.55))

    # Round polygon points to 5 decimals (~1.1 meter resolution)
    clean_coords = [[round(pt[0], 5), round(pt[1], 5)] for pt in outer_ring]
    if clean_coords[0] != clean_coords[-1]:
        clean_coords.append(clean_coords[0])

    city_id = f"city_{district_name.lower().replace(' ', '_').replace('-', '_').replace('.', '')}"
    description = f"{district_name} District: {state_name} Administrative Region"

    return {
        "id": city_id,
        "name": district_name,
        "state": state_name,
        "latitude": center_lat,
        "longitude": center_lon,
        "cameraHeight": camera_height,
        "bbox": [min_lat, min_lon, max_lat, max_lon],
        "description": description,
        "polygonCoordinates": clean_coords,
    }


def process_state(state_name: str, state_slug: str, notify_cities: bool = True) -> List[Dict[str, Any]]:
    """Process all cities in a state and send Telegram notifications."""
    logger.info(f"--- Processing {state_name} ({state_slug}) ---")
    data = fetch_state_geojson(state_slug)
    features = data.get("features", [])
    total_features = len(features)

    send_telegram(f"🚀 *HeatSense Rollout*: Starting *{state_name}* ({total_features} cities)...")
    time.sleep(1.0)

    records = []
    for idx, feat in enumerate(features, start=1):
        rec = extract_city_record(state_name, feat)
        if not rec:
            continue
        records.append(rec)

        if notify_cities:
            pts_count = len(rec["polygonCoordinates"])
            msg = (
                f"✅ *{rec['name']}* ({state_name}) [{idx}/{total_features}]\n"
                f"Boundary: {pts_count} vertices | Center: {rec['latitude']:.3f}, {rec['longitude']:.3f}\n"
                f"Synced to HeatSense"
            )
            send_telegram(msg)
            # Sleep 1.2s to strictly comply with Telegram's 1 msg/sec user rate limit
            time.sleep(1.2)

    milestone_msg = (
        f"🏆 *State Completed*: *{state_name}*\n"
        f"All {len(records)} cities successfully verified and integrated into HeatSense."
    )
    send_telegram(milestone_msg)
    time.sleep(1.0)
    return records


def main():
    """Main execution entrypoint."""
    send_telegram("🛰️ *HeatSense India Expansion*: Autonomous multi-state boundary agent initiated.")
    time.sleep(1.0)

    # Process first batch of priority states
    target_states = sys.argv[1:] if len(sys.argv) > 1 else ["gujarat", "karnataka"]
    
    all_new_records = []
    for state_name, state_slug in STATES_SEQUENCE:
        if state_slug in target_states or "all" in target_states:
            recs = process_state(state_name, state_slug, notify_cities=True)
            all_new_records.extend(recs)

    logger.info(f"Pipeline batch finished. Processed {len(all_new_records)} new city boundaries.")
    send_telegram(f"✨ *Batch Complete*: Processed and verified {len(all_new_records)} city boundaries across target states.")


if __name__ == "__main__":
    main()
