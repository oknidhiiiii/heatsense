"""Location repository for India geographic administrative entities."""

from typing import List, Optional

from heatsense_api.schemas.locations import LocationItem

# Canonical Indian location database for initial pilot release (expandable)
INDIAN_LOCATIONS: List[LocationItem] = [
    LocationItem(
        id="country_IN",
        name="India",
        type="country",
        country_code="IN",
        latitude=20.5937,
        longitude=78.9629,
        bbox=[8.0, 68.0, 37.0, 97.0],
        coverage_status="partial",
    ),
    LocationItem(
        id="state_IN_MH",
        name="Maharashtra",
        type="state",
        country_code="IN",
        admin1="Maharashtra",
        latitude=19.7515,
        longitude=75.7139,
        bbox=[15.6, 72.6, 22.0, 80.9],
        coverage_status="supported",
    ),
    LocationItem(
        id="city_mumbai",
        name="Mumbai",
        type="city",
        country_code="IN",
        admin1="Maharashtra",
        admin2="Mumbai City",
        latitude=18.9388,
        longitude=72.8354,
        bbox=[18.88, 72.75, 19.30, 72.98],
        coverage_status="supported",
    ),
    LocationItem(
        id="city_pune",
        name="Pune",
        type="city",
        country_code="IN",
        admin1="Maharashtra",
        admin2="Pune",
        latitude=18.5204,
        longitude=73.8567,
        bbox=[18.42, 73.75, 18.62, 73.98],
        coverage_status="supported",
    ),
    LocationItem(
        id="city_thane",
        name="Thane",
        type="city",
        country_code="IN",
        admin1="Maharashtra",
        admin2="Thane",
        latitude=19.2183,
        longitude=72.9781,
        bbox=[19.12, 72.90, 19.30, 73.08],
        coverage_status="supported",
    ),
    LocationItem(
        id="city_nashik",
        name="Nashik",
        type="city",
        country_code="IN",
        admin1="Maharashtra",
        admin2="Nashik",
        latitude=19.9975,
        longitude=73.7898,
        bbox=[19.90, 73.70, 20.10, 73.90],
        coverage_status="supported",
    ),
    LocationItem(
        id="city_delhi",
        name="New Delhi",
        type="city",
        country_code="IN",
        admin1="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        bbox=[28.40, 77.00, 28.90, 77.40],
        coverage_status="unsupported",
    ),
    LocationItem(
        id="city_bengaluru",
        name="Bengaluru",
        type="city",
        country_code="IN",
        admin1="Karnataka",
        latitude=12.9716,
        longitude=77.5946,
        bbox=[12.80, 77.45, 13.15, 77.75],
        coverage_status="unsupported",
    ),
]


class LocationRepository:
    """Repository accessing location catalog and administrative boundaries."""

    def __init__(self, locations: Optional[List[LocationItem]] = None):
        self._locations = locations if locations is not None else INDIAN_LOCATIONS

    def search(self, query: str, limit: int = 10) -> List[LocationItem]:
        """Search locations by name, case-insensitively, ranking prefix matches first."""
        q = query.strip().lower()
        if not q:
            return self._locations[:limit]

        exact_matches = []
        prefix_matches = []
        substring_matches = []

        for loc in self._locations:
            name_lower = loc.name.lower()
            if name_lower == q:
                exact_matches.append(loc)
            elif name_lower.startswith(q):
                prefix_matches.append(loc)
            elif q in name_lower or (loc.admin1 and q in loc.admin1.lower()):
                substring_matches.append(loc)

        combined = exact_matches + prefix_matches + substring_matches
        return combined[:limit]

    def get_by_id(self, location_id: str) -> Optional[LocationItem]:
        """Retrieve location by unique ID."""
        for loc in self._locations:
            if loc.id == location_id:
                return loc
        return None
