"""
Generate comprehensive national Indian locations catalog covering all states and 646+ cities.
"""

import glob
import json
import os

STATE_NAMES = {
    'andaman-and-nicobar-islands': 'Andaman and Nicobar Islands',
    'andhra-pradesh': 'Andhra Pradesh',
    'arunachal-pradesh': 'Arunachal Pradesh',
    'assam': 'Assam',
    'bihar': 'Bihar',
    'chandigarh': 'Chandigarh',
    'chhattisgarh': 'Chhattisgarh',
    'delhi': 'Delhi',
    'delhi_districts': 'Delhi',
    'dnh-and-dd': 'Dadra and Nagar Haveli and Daman and Diu',
    'goa': 'Goa',
    'gujarat': 'Gujarat',
    'haryana': 'Haryana',
    'himachal-pradesh': 'Himachal Pradesh',
    'jammu-and-kashmir': 'Jammu and Kashmir',
    'jharkhand': 'Jharkhand',
    'karnataka': 'Karnataka',
    'kerala': 'Kerala',
    'ladakh': 'Ladakh',
    'lakshadweep': 'Lakshadweep',
    'madhya-pradesh': 'Madhya Pradesh',
    'manipur': 'Manipur',
    'meghalaya': 'Meghalaya',
    'mizoram': 'Mizoram',
    'nagaland': 'Nagaland',
    'odisha': 'Odisha',
    'puducherry': 'Puducherry',
    'punjab': 'Punjab',
    'rajasthan': 'Rajasthan',
    'sikkim': 'Sikkim',
    'tamil-nadu': 'Tamil Nadu',
    'telangana': 'Telangana',
    'tripura': 'Tripura',
    'uttar-pradesh': 'Uttar Pradesh',
    'uttarakhand': 'Uttarakhand',
    'west-bengal': 'West Bengal'
}

ALIASES = {
    'bengaluru': 'Bangalore',
    'bengaluru urban': 'Bangalore',
    'bengaluru rural': 'Bangalore Rural',
    'chennai': 'Madras',
    'kolkata': 'Calcutta',
    'mumbai': 'Bombay',
    'pune': 'Poona',
    'vadodara': 'Baroda',
    'prayagraj': 'Allahabad',
    'ayodhya': 'Faizabad',
    'mysuru': 'Mysore',
    'hubballi-dharwad': 'Hubli',
    'dharwad': 'Hubli',
    'belagavi': 'Belgaum',
    'kalaburagi': 'Gulbarga',
    'vijayapura': 'Bijapur',
    'shivamogga': 'Shimoga',
    'chhatrapati sambhajinagar': 'Aurangabad',
    'dharashiv': 'Osmanabad',
    'ahilyanagar': 'Ahmednagar',
    'gurugram': 'Gurgaon',
    'noida': 'Gautam Buddha Nagar',
    'varanasi': 'Banaras / Kashi',
    'thiruvananthapuram': 'Trivandrum',
    'kochi': 'Cochin',
    'ernakulam': 'Kochi',
    'kozhikode': 'Calicut',
    'jalandhar': 'Jullundur',
    'visakhapatnam': 'Vizag',
    'shimla': 'Simla',
    'panaji': 'Panjim',
    'north goa': 'Panaji / Panjim',
    'south goa': 'Margao / Madgaon',
    'puducherry': 'Pondicherry',
    'tirunelveli': 'Tinnevelly',
    'tiruchirappalli': 'Trichy',
    'kanpur': 'Cawnpore',
    'kanpur nagar': 'Kanpur',
    'kanpur dehat': 'Akbarpur',
    'alappuzha': 'Alleppey',
    'kollam': 'Quilon',
    'palakkad': 'Palghat',
    'thrissur': 'Trichur',
    'kamrup metropolitan': 'Guwahati',
    'kamrup metro': 'Guwahati',
    'south andaman': 'Port Blair',
    'east sikkim': 'Gangtok',
    'west sikkim': 'Geyzing',
    'south sikkim': 'Namchi',
    'north sikkim': 'Mangan',
    'east khasi hills': 'Shillong',
    'west khasi hills': 'Nongstoin',
    'papum pare': 'Itanagar',
    'kangra': 'Dharamshala',
    'cachar': 'Silchar',
    'east singhbhum': 'Jamshedpur',
    'purbi singhbhum': 'Jamshedpur',
    'west singhbhum': 'Chaibasa',
    'pashchimi singhbhum': 'Chaibasa',
    'gautam buddha nagar': 'Noida / Greater Noida',
    'khordha': 'Bhubaneswar',
    'saran': 'Chhapra',
    'vaishali': 'Hajipur',
    'bhojpur': 'Arrah',
    'rohtas': 'Sasaram',
    'pashchim champaran': 'Bettiah',
    'purba champaran': 'Motihari',
    'kaimur (bhabua)': 'Bhabua',
    'kaimur': 'Bhabua',
    'dakshina kannada': 'Mangaluru / Mangalore',
    'uttara kannada': 'Karwar',
    'warangal urban': 'Warangal',
    'lahaul and spiti': 'Keylong',
    'kinnaur': 'Reckong Peo',
    'sirmaur': 'Nahan',
}

def generate():
    seen_ids = set()
    cities = []

    # 1. First add Maharashtra's canonical 35 districts + MMR hubs
    with open('data/interim/maharashtra_districts.geojson') as fp:
        mh_data = json.load(fp)

    for feat in mh_data['features']:
        dname = feat['properties']['district'].strip()
        geom = feat['geometry']
        ring = geom['coordinates'][0] if geom['type'] == 'Polygon' else max(geom['coordinates'], key=lambda p: len(p[0]))[0]
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        min_lat, max_lat = round(min(lats), 4), round(max(lats), 4)
        min_lon, max_lon = round(min(lons), 4), round(max(lons), 4)
        c_lat = round((min_lat + max_lat) / 2.0, 4)
        c_lon = round((min_lon + max_lon) / 2.0, 4)
        
        disp_name = dname
        admin2 = None
        if dname.lower() == 'aurangabad':
            disp_name = 'Chhatrapati Sambhajinagar'
            admin2 = 'Aurangabad'
        elif dname.lower() == 'osmanabad':
            disp_name = 'Dharashiv'
            admin2 = 'Osmanabad'
        elif dname.lower() == 'ahmednagar':
            disp_name = 'Ahilyanagar'
            admin2 = 'Ahmednagar'
        elif dname.lower() in ALIASES:
            admin2 = ALIASES[dname.lower()]

        cid = f"city_{disp_name.lower().replace(' ', '_').replace('-', '_')}"
        seen_ids.add(cid)
        cities.append({
            'id': cid,
            'name': disp_name,
            'state': 'Maharashtra',
            'admin2': admin2,
            'latitude': c_lat,
            'longitude': c_lon,
            'bbox': [min_lat, min_lon, max_lat, max_lon],
            'coverage_status': 'supported'
        })

    # Add MMR and Pune metropolitan extras
    cities.append({
        'id': 'city_navi_mumbai',
        'name': 'Navi Mumbai',
        'state': 'Maharashtra',
        'admin2': 'MMR',
        'latitude': 19.0330,
        'longitude': 73.0297,
        'bbox': [18.99, 72.97, 19.19, 73.05],
        'coverage_status': 'supported'
    })
    cities.append({
        'id': 'city_pcmc',
        'name': 'Pimpri-Chinchwad',
        'state': 'Maharashtra',
        'admin2': 'Pune Metropolitan',
        'latitude': 18.6298,
        'longitude': 73.7997,
        'bbox': [18.58, 73.72, 18.68, 73.88],
        'coverage_status': 'supported'
    })

    # 2. Add all other states from data/interim/states/*.geojson
    files = sorted(glob.glob('data/interim/states/*.geojson'))
    for f in files:
        slug = os.path.basename(f).replace('.geojson', '')
        sname = STATE_NAMES.get(slug, slug.replace('-', ' ').title())
        with open(f) as fp:
            d = json.load(fp)
        if slug == 'delhi' and os.path.exists('data/interim/states/delhi_districts.geojson'):
            continue
        for feat in d.get('features', []):
            props = feat.get('properties', {})
            dname = props.get('district') or props.get('dtname') or props.get('name') or props.get('Dist_Name')
            if not dname:
                continue
            dname = dname.strip()
            geom = feat.get('geometry', {})
            t = geom.get('type')
            c = geom.get('coordinates', [])
            if t == 'Polygon' and c:
                ring = c[0]
            elif t == 'MultiPolygon' and c:
                ring = max(c, key=lambda p: len(p[0]))[0]
            else:
                continue

            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            min_lat, max_lat = round(min(lats), 4), round(max(lats), 4)
            min_lon, max_lon = round(min(lons), 4), round(max(lons), 4)
            c_lat = round((min_lat + max_lat) / 2.0, 4)
            c_lon = round((min_lon + max_lon) / 2.0, 4)

            cid = f"city_{dname.lower().replace(' ', '_').replace('-', '_').replace('.', '')}"
            if cid in seen_ids:
                cid = f"{cid}_{slug}"
            seen_ids.add(cid)

            admin2 = ALIASES.get(dname.lower())
            status = 'supported' if sname == 'Maharashtra' else 'unsupported'
            cities.append({
                'id': cid,
                'name': dname,
                'state': sname,
                'admin2': admin2,
                'latitude': c_lat,
                'longitude': c_lon,
                'bbox': [min_lat, min_lon, max_lat, max_lon],
                'coverage_status': status
            })

    # Write Python locations.py
    out_lines = [
        '"""Location repository for India geographic administrative entities."""',
        '',
        'from typing import List, Optional',
        '',
        'from heatsense_api.schemas.locations import LocationItem',
        '',
        '# Canonical Indian national location database',
        'INDIAN_LOCATIONS: List[LocationItem] = [',
        '    LocationItem(',
        '        id="country_IN",',
        '        name="India",',
        '        type="country",',
        '        country_code="IN",',
        '        latitude=20.5937,',
        '        longitude=78.9629,',
        '        bbox=[8.0, 68.0, 37.0, 97.0],',
        '        coverage_status="partial",',
        '    ),',
        '    LocationItem(',
        '        id="city_delhi_unsupported_ref",',
        '        name="Delhi (Reference)",',
        '        type="city",',
        '        country_code="IN",',
        '        admin1="Delhi",',
        '        latitude=28.6139,',
        '        longitude=77.2090,',
        '        bbox=[28.40, 77.00, 28.90, 77.40],',
        '        coverage_status="unsupported",',
        '    ),',
    ]

    for c in cities:
        admin2_str = f'"{c["admin2"]}"' if c.get('admin2') else 'None'
        out_lines.extend([
            '    LocationItem(',
            f'        id="{c["id"]}",',
            f'        name={json.dumps(c["name"])},',
            '        type="city",',
            '        country_code="IN",',
            f'        admin1={json.dumps(c["state"])},',
            f'        admin2={admin2_str},',
            f'        latitude={c["latitude"]},',
            f'        longitude={c["longitude"]},',
            f'        bbox={c["bbox"]},',
            f'        coverage_status="{c["coverage_status"]}",',
            '    ),',
        ])

    out_lines.extend([
        ']',
        '',
        '',
        'class LocationRepository:',
        '    """Repository accessing location catalog and administrative boundaries."""',
        '',
        '    def __init__(self, locations: Optional[List[LocationItem]] = None):',
        '        self._locations = locations if locations is not None else INDIAN_LOCATIONS',
        '',
        '    def search(self, query: str, limit: int = 10) -> List[LocationItem]:',
        '        """Search locations by name or alias, case-insensitively, ranking prefix matches first."""',
        '        q = query.strip().lower()',
        '        if not q:',
        '            return self._locations[:limit]',
        '',
        '        exact_matches = []',
        '        prefix_matches = []',
        '        substring_matches = []',
        '',
        '        for loc in self._locations:',
        '            name_lower = loc.name.lower()',
        '            admin2_lower = loc.admin2.lower() if loc.admin2 else ""',
        '            if name_lower == q or admin2_lower == q:',
        '                exact_matches.append(loc)',
        '            elif name_lower.startswith(q) or (admin2_lower and admin2_lower.startswith(q)):',
        '                prefix_matches.append(loc)',
        '            elif q in name_lower or (loc.admin1 and q in loc.admin1.lower()) or (admin2_lower and q in admin2_lower):',
        '                substring_matches.append(loc)',
        '',
        '        combined = exact_matches + prefix_matches + substring_matches',
        '        return combined[:limit]',
        '',
        '    def get_by_id(self, location_id: str) -> Optional[LocationItem]:',
        '        """Retrieve location by unique ID."""',
        '        for loc in self._locations:',
        '            if loc.id == location_id:',
        '                return loc',
        '        return None',
        ''
    ])

    content = '\n'.join(out_lines)
    with open('backend/src/heatsense_api/repositories/locations.py', 'w') as fp:
        fp.write(content)

    print(f"Generated backend/src/heatsense_api/repositories/locations.py with {len(cities)} city locations!")
    print("Em dash check:", chr(8212) in content)

if __name__ == '__main__':
    generate()
