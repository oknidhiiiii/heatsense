"""Dataset manifest generator and validator."""

import hashlib
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class VariableMeta(BaseModel):
    """Metadata for a weather variable."""

    source_name: str
    canonical_name: str
    source_units: str
    canonical_units: str
    description: str


class TemporalCoverage(BaseModel):
    """Temporal range and resolution."""

    start_utc: str
    end_utc: str
    resolution: str = "hourly"
    total_timesteps: int


class SpatialCoverage(BaseModel):
    """Spatial bounds and grid description."""

    region: str
    crs: str = "EPSG:4326"
    bbox: List[float] = Field(..., description="[min_lat, min_lon, max_lat, max_lon]")
    native_grid_spacing_deg: float = 0.1
    cell_count: int


class DatasetManifest(BaseModel):
    """Complete metadata manifest for weather and reanalysis datasets."""

    dataset_id: str
    provider: str
    dataset_name: str
    source_reference: str
    retrieved_at_utc: str
    license_and_attribution: str
    variables: List[VariableMeta]
    temporal_coverage: TemporalCoverage
    spatial_coverage: SpatialCoverage
    transformations: List[str]
    missingness_summary: Dict[str, Any]
    checksums: Dict[str, str]
    notes: List[str]

    def save(self, filepath: Path) -> None:
        """Save manifest to JSON file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, filepath: Path) -> "DatasetManifest":
        """Load manifest from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()
