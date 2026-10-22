"""Configuration constants and pilot parameters for HeatSense ML."""

from pathlib import Path
from typing import List, Tuple

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Geographic bounding box in EPSG:4326."""

    min_lat: float = 18.0
    min_lon: float = 72.5
    max_lat: float = 20.5
    max_lon: float = 74.5

    @property
    def tuple_bounds(self) -> Tuple[float, float, float, float]:
        """Return (min_lat, min_lon, max_lat, max_lon)."""
        return (self.min_lat, self.min_lon, self.max_lat, self.max_lon)


class MLConfig(BaseModel):
    """Configuration for data engineering, feature generation, and training."""

    # Storage paths
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    interim_dir: Path = Path("data/interim")
    processed_dir: Path = Path("data/processed")
    artifacts_dir: Path = Path("artifacts/models")

    # Pilot spatial domain (Western India / Maharashtra - ADR 0004)
    pilot_bbox: BoundingBox = Field(default_factory=BoundingBox)
    grid_resolution_deg: float = 0.1

    # Target horizons in hours
    target_horizons: List[int] = Field(default=[24, 48])

    # Variables
    primary_temperature_var: str = "air_temperature_2m"
    temperature_unit_source: str = "K"
    temperature_unit_canonical: str = "degC"

    # Reproducibility
    random_seed: int = 42

    # Chronological Split
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15


default_ml_config = MLConfig()
