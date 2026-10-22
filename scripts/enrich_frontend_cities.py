"""
Enrich frontend/src/utils/cityBoundaries.ts with Maharashtra districts + top national metropolitan hubs.
"""

import json
import os

MH_PATH = 'data/interim/maharashtra_districts.geojson'
STATES_DIR = 'data/interim/states'

MH_DISPLAY_NAMES = {
    'Aurangabad': 'Chhatrapati Sambhajinagar',
    'Osmanabad': 'Dharashiv',
    'Ahmednagar': 'Ahilyanagar',
}

MH_DESCRIPTIONS = {
    'Mumbai': 'Mumbai Metropolitan Region: Coastal Urban Heat Island',
    'Pune': 'Pune Metropolitan Area: Deccan Plateau Heat Corridor',
    'Nagpur': 'Central India Commercial Capital: Vidarbha Continental Heat Basin',
    'Thane': 'Metropolitan Creek Corridor: Urban Density and Wetlands Belt',
    'Nashik': 'Northern Maharashtra Agricultural and Industrial Plateau',
    'Aurangabad': 'Marathwada Heritage Capital: Semi-Arid Plateau Heat Core',
    'Solapur': 'Southern Maharashtra Textile Hub: Semi-Arid Heat Basin',
    'Kolhapur': 'Western Ghats Foothills: Panchaganga Basin Agricultural Corridor',
    'Amravati': 'Cotton Capital of Vidarbha: Northern Plateau Heat Belt',
    'Nanded': 'Godavari River Valley: Southeastern Agrarian Heat Corridor',
    'Ahmednagar': 'Central Maharashtra Plateau: Semi-Arid Drought Belt',
    'Jalgaon': 'Khandesh Banana Capital: Tapi Valley Dry Heat Zone',
    'Akola': 'Central Vidarbha Commercial Center: High Thermal Amplitude Belt',
    'Dhule': 'Northwestern Transport Hub: Khandesh Plateau Zone',
    'Chandrapur': 'Eastern Mineral and Thermal Hub: Intensive Heat Corridor',
    'Latur': 'Marathwada Agricultural Trading Hub: Drought-Prone Plateau',
    'Satara': 'Sahyadri Foothills: Krishna Valley Agriculture and Hill Corridors',
    'Sangli': 'Southern Krishna River Basin: Turmeric and Sugar Heartland',
    'Ratnagiri': 'Konkan Coastline: Western Ghats Maritime Heat Corridor',
    'Raigad': 'Northern Konkan Maritime Belt: Coastal Industrial Corridor',
    'Palghar': 'North Konkan Coastal Industrial and Forested Belt',
    'Sindhudurg': 'Southern Konkan Maritime Strip: High-Humidity Coastal Valley',
    'Jalna': 'Central Marathwada Seed Capital: Kundalika Basin',
    'Beed': 'Balaghat Hill Range: Central Dry Agriculture Zone',
    'Parbhani': 'Lower Godavari Basin: Agricultural Heartland',
    'Osmanabad': 'Balaghat Highland: Southern Semi-Arid Plateau',
    'Yavatmal': 'Vidarbha Cotton Heartland: Undulating Tribal Plateau',
    'Wardha': 'Historic Vidarbha Agricultural Basin: Cotton Belt',
    'Bhandara': 'Brass City: Wainganga River Basin and Lake District',
    'Gondia': 'Eastern Rice Bowl: Forested Wainganga Basin',
    'Buldhana': 'Western Vidarbha Plateau: Lonar Basin Region',
    'Washim': 'Penganga River Basin: Vidarbha Agrarian Corridor',
    'Hingoli': 'Marathwada Borderland: Kayadhu River Valley',
    'Nandurbar': 'Satpura Mountain Range: Northern Border Valley',
    'Gadchiroli': 'Eastern Forested Frontier: Godavari and Pranhita River Basin'
}

MH_HQ = {
    'mumbai': (18.9388, 72.8354, 75000),
    'pune': (18.5204, 73.8567, 180000),
    'nagpur': (21.1458, 79.0882, 190000),
    'thane': (19.2183, 72.9781, 150000),
    'nashik': (19.9975, 73.7898, 200000),
    'aurangabad': (19.8762, 75.3433, 190000),
    'solapur': (17.6599, 75.9064, 210000),
    'kolhapur': (16.7050, 74.2433, 180000),
    'amravati': (20.9374, 77.7523, 210000),
    'nanded': (19.1383, 77.3178, 210000),
    'ahmednagar': (19.0942, 74.7460, 230000),
    'jalgaon': (21.0077, 75.5626, 210000),
    'akola': (20.7002, 77.0082, 180000),
    'dhule': (20.9042, 74.7749, 190000),
    'chandrapur': (19.9615, 79.2961, 200000),
    'latur': (18.4088, 76.5656, 180000),
    'satara': (17.6805, 73.9903, 190000),
    'sangli': (16.8524, 74.5815, 210000),
    'ratnagiri': (16.9902, 73.3120, 210000),
    'raigad': (18.6471, 72.8708, 190000),
    'palghar': (19.6967, 72.7667, 170000),
    'sindhudurg': (16.1132, 73.7024, 180000),
    'jalna': (19.8410, 75.8830, 190000),
    'beed': (18.9892, 75.7555, 220000),
    'parbhani': (19.2612, 76.7749, 180000),
    'osmanabad': (18.1856, 76.0440, 200000),
    'yavatmal': (20.3888, 78.1307, 220000),
    'wardha': (20.7453, 78.6022, 170000),
    'bhandara': (21.1717, 79.6545, 170000),
    'gondia': (21.4574, 80.1965, 180000),
    'buldhana': (20.5329, 76.1807, 210000),
    'washim': (20.1097, 77.1410, 170000),
    'hingoli': (19.7160, 77.1379, 170000),
    'nandurbar': (21.3740, 74.2401, 190000),
    'gadchiroli': (20.1809, 80.0035, 250000),
}

# Premier National Metropolitan Hubs covering all 36 States and Union Territories
NATIONAL_METROS = [
    # Karnataka
    ("karnataka", "Bengaluru Urban", "Bengaluru: Silicon Valley of India", 12.9716, 77.5946, 110000),
    ("karnataka", "Mysuru", "Mysuru: Heritage Capital of Karnataka", 12.2958, 76.6394, 140000),
    ("karnataka", "Dharwad", "Hubballi-Dharwad: Commercial Center of North Karnataka", 15.4589, 75.0078, 140000),
    ("karnataka", "Dakshina Kannada", "Mangaluru: Port City of Coastal Karnataka", 12.9141, 74.8560, 130000),
    ("karnataka", "Belagavi", "Belagavi: Northern Border Industrial Center", 15.8497, 74.4977, 150000),
    # Gujarat
    ("gujarat", "Ahmedabad", "Ahmedabad: Commercial Metropolis of Gujarat", 23.0225, 72.5714, 150000),
    ("gujarat", "Surat", "Surat: Diamond and Textile Hub of India", 21.1702, 72.8311, 140000),
    ("gujarat", "Vadodara", "Vadodara: Cultural Capital of Gujarat", 22.3072, 73.1812, 130000),
    ("gujarat", "Rajkot", "Rajkot: Saurashtra Industrial Center", 22.3039, 70.8022, 140000),
    ("gujarat", "Gandhinagar", "Gandhinagar: Green Capital City of Gujarat", 23.2156, 72.6369, 120000),
    # Telangana
    ("telangana", "Hyderabad", "Hyderabad: Cyberabad and Deccan Capital", 17.3850, 78.4867, 120000),
    ("telangana", "Warangal Urban", "Warangal: Historic Kakatiya Capital", 17.9689, 79.5941, 130000),
    # Tamil Nadu
    ("tamil-nadu", "Chennai", "Chennai: Gateway to South India", 13.0827, 80.2707, 110000),
    ("tamil-nadu", "Coimbatore", "Coimbatore: Manchester of South India", 11.0168, 76.9558, 140000),
    ("tamil-nadu", "Madurai", "Madurai: Cultural Capital on Vaigai River", 9.9252, 78.1198, 130000),
    ("tamil-nadu", "Tiruchirappalli", "Tiruchirappalli: Central Kaveri Basin Hub", 10.7905, 78.7047, 140000),
    # Andhra Pradesh
    ("andhra-pradesh", "Visakhapatnam", "Visakhapatnam: Port City of Eastern Ghats", 17.6868, 83.2185, 150000),
    ("andhra-pradesh", "Guntur", "Amaravati-Guntur: Krishna River Capital Region", 16.3067, 80.4365, 140000),
    ("andhra-pradesh", "Tirupati", "Tirupati: Spiritual Capital of Andhra Pradesh", 13.6288, 79.4192, 130000),
    # Kerala
    ("kerala", "Thiruvananthapuram", "Thiruvananthapuram: Coastal Capital of Kerala", 8.5241, 76.9366, 120000),
    ("kerala", "Ernakulam", "Ernakulam / Kochi: Queen of the Arabian Sea", 9.9816, 76.2999, 130000),
    ("kerala", "Kozhikode", "Kozhikode: Historic Malabar Spice Coast", 11.2588, 75.7804, 130000),
    # Rajasthan
    ("rajasthan", "Jaipur", "Jaipur: Pink City Capital of Rajasthan", 26.9124, 75.7873, 160000),
    ("rajasthan", "Jodhpur", "Jodhpur: Sun City of Marwar", 26.2389, 73.0243, 180000),
    ("rajasthan", "Udaipur", "Udaipur: City of Lakes in Mewar", 24.5854, 73.7125, 150000),
    ("rajasthan", "Kota", "Kota: Chambal River Industrial and Education Hub", 25.2138, 75.8648, 150000),
    # Uttar Pradesh
    ("uttar-pradesh", "Lucknow", "Lucknow: City of Nawabs and State Capital", 26.8467, 80.9462, 150000),
    ("uttar-pradesh", "Kanpur Nagar", "Kanpur: Industrial Hub on the Ganges", 26.4499, 80.3319, 140000),
    ("uttar-pradesh", "Varanasi", "Varanasi: Sacred Spiritual Capital on the Ganges", 25.3176, 82.9739, 130000),
    ("uttar-pradesh", "Agra", "Agra: Historic Yamuna River Heritage Hub", 27.1767, 78.0081, 140000),
    ("uttar-pradesh", "Prayagraj", "Prayagraj: Triveni Sangam Sacred Confluence", 25.4358, 81.8463, 150000),
    ("uttar-pradesh", "Gautam Buddha Nagar", "Noida / Greater Noida: Delhi NCR Tech Corridor", 28.5355, 77.3910, 120000),
    # Madhya Pradesh
    ("madhya-pradesh", "Bhopal", "Bhopal: City of Lakes Capital of MP", 23.2599, 77.4126, 160000),
    ("madhya-pradesh", "Indore", "Indore: Commercial Center of Central India", 22.7196, 75.8577, 150000),
    ("madhya-pradesh", "Gwalior", "Gwalior: Historic Fort City of Northern MP", 26.2183, 78.1828, 150000),
    ("madhya-pradesh", "Jabalpur", "Jabalpur: Narmada River Valley Marble Rocks", 23.1815, 79.9864, 150000),
    # West Bengal
    ("west-bengal", "Kolkata", "Kolkata: Cultural Capital of India", 22.5726, 88.3639, 100000),
    ("west-bengal", "Howrah", "Howrah: Industrial Twin City on Hooghly River", 22.5958, 88.2636, 110000),
    ("west-bengal", "Darjeeling", "Darjeeling: Queen of the Himalayas", 27.0410, 88.2663, 130000),
    # Bihar
    ("bihar", "Patna", "Patna: Ancient Pataliputra Capital of Bihar", 25.5941, 85.1376, 140000),
    ("bihar", "Gaya", "Gaya / Bodh Gaya: Spiritual Sanctuary on Phalgu River", 24.7955, 85.0002, 130000),
    # Odisha
    ("odisha", "Khordha", "Bhubaneswar: Temple City Capital of Odisha", 20.2961, 85.8245, 140000),
    ("odisha", "Cuttack", "Cuttack: Silver City on Mahanadi Delta", 20.4625, 85.8828, 130000),
    ("odisha", "Puri", "Puri: Coastal Temple City of Jagannath", 19.8135, 85.8312, 130000),
    # Punjab & Haryana
    ("punjab", "Ludhiana", "Ludhiana: Industrial Capital of Punjab", 30.9010, 75.8573, 140000),
    ("punjab", "Amritsar", "Amritsar: Holy City of the Golden Temple", 31.6340, 74.8723, 130000),
    ("haryana", "Gurugram", "Gurugram: Millennium City and Global Tech Hub", 28.4595, 77.0266, 120000),
    ("haryana", "Faridabad", "Faridabad: Major Industrial Center of Haryana", 28.4089, 77.3178, 120000),
    ("chandigarh", "Chandigarh", "Chandigarh: Planned City Capital of Punjab and Haryana", 30.7333, 76.7794, 90000),
    # Delhi
    ("delhi", "Delhi", "National Capital Territory of Delhi", 28.6139, 77.2090, 110000),
    # Goa
    ("goa", "North Goa", "Panaji / North Goa: Mandovi Estuary Capital", 15.4909, 73.8278, 110000),
    # Chhattisgarh & Jharkhand
    ("chhattisgarh", "Raipur", "Raipur: Capital of Mineral-Rich Chhattisgarh", 21.2514, 81.6296, 140000),
    ("jharkhand", "Ranchi", "Ranchi: City of Waterfalls Capital of Jharkhand", 23.3441, 85.3096, 140000),
    ("jharkhand", "East Singhbhum", "Jamshedpur / East Singhbhum: Steel City of India", 22.8046, 86.2029, 130000),
    # Assam & Northeast
    ("assam", "Kamrup Metropolitan", "Guwahati: Gateway to Northeast India", 26.1445, 91.7362, 120000),
    ("meghalaya", "East Khasi Hills", "Shillong: Scotland of the East", 25.5788, 91.8933, 120000),
    ("tripura", "West Tripura", "Agartala: Capital City of Tripura", 23.8315, 91.2868, 110000),
    ("manipur", "Imphal West", "Imphal: Historical Capital Valley of Manipur", 24.8170, 93.9368, 110000),
    ("mizoram", "Aizawl", "Aizawl: Ridge Capital of Mizoram", 23.7271, 92.7176, 110000),
    ("nagaland", "Kohima", "Kohima: Mountain Capital of Nagaland", 25.6751, 94.1086, 110000),
    ("arunachal-pradesh", "Papum Pare", "Itanagar: Foothill Capital of Arunachal Pradesh", 27.0844, 93.6053, 120000),
    ("sikkim", "East Sikkim", "Gangtok: Himalayan Capital of Sikkim", 27.3389, 88.6065, 110000),
    # Himalayan & UTs
    ("himachal-pradesh", "Shimla", "Shimla: Summer Capital of the Himalayas", 31.1048, 77.1734, 120000),
    ("himachal-pradesh", "Kangra", "Dharamshala / Kangra: Dhauladhar Valley", 32.2190, 76.3234, 130000),
    ("uttarakhand", "Dehradun", "Dehradun: Doon Valley Capital of Uttarakhand", 30.3165, 78.0322, 130000),
    ("uttarakhand", "Haridwar", "Haridwar: Gateway to the Gods on the Ganges", 29.9457, 78.1642, 120000),
    ("jammu-and-kashmir", "Srinagar", "Srinagar: Summer Capital on Dal Lake", 34.0837, 74.7973, 110000),
    ("jammu-and-kashmir", "Jammu", "Jammu: Winter Capital on Tawi River", 32.7266, 74.8570, 120000),
    ("ladakh", "Leh", "Leh: High Altitude Himalayan Capital of Ladakh", 34.1526, 77.5771, 160000),
    ("puducherry", "Puducherry", "Puducherry: French Heritage Coastal Territory", 11.9416, 79.8083, 90000),
    ("andaman-and-nicobar-islands", "South Andaman", "Port Blair: Capital of Andaman and Nicobar Islands", 11.6234, 92.7265, 110000),
]

def build():
    # Load MH GeoJSON
    with open(MH_PATH) as f:
        mh_data = json.load(f)

    mh_features = {f['properties']['district'].strip().lower(): f for f in mh_data['features']}

    ORDER = [
        'Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik', 'Aurangabad',
        'Solapur', 'Kolhapur', 'Amravati', 'Nanded', 'Ahmednagar', 'Jalgaon',
        'Akola', 'Dhule', 'Chandrapur', 'Latur', 'Satara', 'Sangli',
        'Ratnagiri', 'Raigad', 'Palghar', 'Sindhudurg', 'Jalna', 'Beed',
        'Parbhani', 'Osmanabad', 'Yavatmal', 'Wardha', 'Bhandara', 'Gondia',
        'Buldhana', 'Washim', 'Hingoli', 'Nandurbar', 'Gadchiroli'
    ]

    entries = []

    # 1. Add all 35 Maharashtra districts
    for name in ORDER:
        feat = mh_features[name.lower()]
        disp_name = MH_DISPLAY_NAMES.get(name, name)
        hq_lat, hq_lon, cam_h = MH_HQ[name.lower()]
        desc = MH_DESCRIPTIONS[name]

        geom = feat['geometry']
        ring = geom['coordinates'][0] if geom['type'] == 'Polygon' else max(geom['coordinates'], key=lambda p: len(p[0]))[0]
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        min_lat, max_lat = round(min(lats), 4), round(max(lats), 4)
        min_lon, max_lon = round(min(lons), 4), round(max(lons), 4)
        clean_coords = [[round(p[0], 5), round(p[1], 5)] for p in ring]
        if clean_coords[0] != clean_coords[-1]:
            clean_coords.append(clean_coords[0])

        city_id = f"city_{name.lower().replace(' ', '_')}"
        entries.append({
            'id': city_id,
            'name': disp_name,
            'state': 'Maharashtra',
            'latitude': hq_lat,
            'longitude': hq_lon,
            'cameraHeight': cam_h,
            'bbox': [min_lat, min_lon, max_lat, max_lon],
            'description': desc,
            'polygonCoordinates': clean_coords
        })

    # 2. Add Premier National Metros
    for state_slug, dist_name, desc, hq_lat, hq_lon, cam_h in NATIONAL_METROS:
        fpath = os.path.join(STATES_DIR, f"{state_slug}.geojson")
        if not os.path.exists(fpath):
            continue
        with open(fpath) as f:
            sdata = json.load(f)
        
        target_feat = None
        for feat in sdata.get('features', []):
            fn = (feat.get('properties', {}).get('district') or feat.get('properties', {}).get('name') or '').strip()
            if fn.lower() == dist_name.lower():
                target_feat = feat
                break
        
        if not target_feat:
            continue

        geom = target_feat['geometry']
        ring = geom['coordinates'][0] if geom['type'] == 'Polygon' else max(geom['coordinates'], key=lambda p: len(p[0]))[0]
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        min_lat, max_lat = round(min(lats), 4), round(max(lats), 4)
        min_lon, max_lon = round(min(lons), 4), round(max(lons), 4)
        clean_coords = [[round(p[0], 5), round(p[1], 5)] for p in ring]
        if clean_coords[0] != clean_coords[-1]:
            clean_coords.append(clean_coords[0])

        state_display = state_slug.replace('-', ' ').title()
        city_id = f"city_{dist_name.lower().replace(' ', '_').replace('/', '_')}"
        entries.append({
            'id': city_id,
            'name': dist_name,
            'state': state_display,
            'latitude': hq_lat,
            'longitude': hq_lon,
            'cameraHeight': cam_h,
            'bbox': [min_lat, min_lon, max_lat, max_lon],
            'description': desc,
            'polygonCoordinates': clean_coords
        })

    # Format TS file
    out_lines = [
        '/**',
        ' * City boundaries and administrative polygon coordinates for India.',
        ' * Encompasses Maharashtra state plus premier metropolitan centers nationwide.',
        ' * Supports interactive hovering, outline highlights, and city-focused thermal intelligence.',
        ' */',
        '',
        'export interface CityData {',
        '  id: string;',
        '  name: string;',
        '  state: string;',
        '  latitude: number;',
        '  longitude: number;',
        '  cameraHeight: number;',
        '  bbox: [number, number, number, number]; // [minLat, minLon, maxLat, maxLon]',
        '  polygonCoordinates: [number, number][]; // Array of [lon, lat] points tracing boundary',
        '  description: string;',
        '}',
        '',
        'export const CITIES_DATA: CityData[] = ['
    ]

    for item in entries:
        out_lines.append('  {')
        out_lines.append(f'    id: {json.dumps(item["id"])},')
        out_lines.append(f'    name: {json.dumps(item["name"])},')
        out_lines.append(f'    state: {json.dumps(item["state"])},')
        out_lines.append(f'    latitude: {item["latitude"]},')
        out_lines.append(f'    longitude: {item["longitude"]},')
        out_lines.append(f'    cameraHeight: {item["cameraHeight"]},')
        out_lines.append(f'    bbox: {json.dumps(item["bbox"])},')
        out_lines.append(f'    description: {json.dumps(item["description"])},')
        coords_str = json.dumps(item["polygonCoordinates"])
        out_lines.append(f'    polygonCoordinates: {coords_str},')
        out_lines.append('  },')

    out_lines.extend([
        '];',
        '',
        'export function findCityById(id: string): CityData | undefined {',
        '  return CITIES_DATA.find((c) => c.id === id);',
        '}',
        '',
        'export function isCoordInBBox(lat: number, lon: number, bbox: [number, number, number, number]): boolean {',
        '  const [minLat, minLon, maxLat, maxLon] = bbox;',
        '  return lat >= minLat && lat <= maxLat && lon >= minLon && lon <= maxLon;',
        '}',
        '',
        'export function getNearestCity(lat: number, lon: number): CityData | null {',
        '  for (const city of CITIES_DATA) {',
        '    if (isCoordInBBox(lat, lon, city.bbox)) {',
        '      return city;',
        '    }',
        '  }',
        '  return null;',
        '}',
        ''
    ])

    text = '\n'.join(out_lines)
    with open('frontend/src/utils/cityBoundaries.ts', 'w') as f:
        f.write(text)

    print(f"Generated frontend/src/utils/cityBoundaries.ts with {len(entries)} cities!")
    print("Em dash check:", chr(8212) in text)

if __name__ == '__main__':
    build()
