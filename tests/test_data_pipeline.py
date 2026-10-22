"""Unit tests for Stage 2 data engineering, units, and validation."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from heatsense_ml.data.manifest import DatasetManifest
from heatsense_ml.data.quality import DataValidationError, validate_weather_dataframe
from heatsense_ml.data.units import (
    ZERO_CELSIUS_KELVIN,
    accumulated_joules_to_wm2,
    celsius_to_kelvin,
    kelvin_to_celsius,
)


def test_temperature_unit_conversions():
    """Verify Kelvin to Celsius and inverse conversions."""
    assert kelvin_to_celsius(ZERO_CELSIUS_KELVIN) == 0.0
    assert kelvin_to_celsius(373.15) == 100.0
    assert kelvin_to_celsius(300.0) == 26.85
    assert celsius_to_kelvin(0.0) == ZERO_CELSIUS_KELVIN
    assert celsius_to_kelvin(25.0) == 298.15


def test_kelvin_to_celsius_absolute_zero_guard():
    """Verify conversion raises ValueError on temperatures below 0 Kelvin."""
    with pytest.raises(ValueError, match="below 0 Kelvin"):
        kelvin_to_celsius(-1.0)


def test_solar_flux_conversion():
    """Verify J/m^2 accumulation to W/m^2 conversion."""
    # 3600 J/m^2 over 3600 seconds = 1 W/m^2
    assert accumulated_joules_to_wm2(3600.0, 3600.0) == 1.0
    assert accumulated_joules_to_wm2(3.6e6, 3600.0) == 1000.0

    with pytest.raises(ValueError):
        accumulated_joules_to_wm2(100.0, -10.0)


def test_quality_validation_detects_nans():
    """Verify validator raises error if null values exist."""
    df = pd.DataFrame(
        {
            "grid_cell_id": ["cell_1", "cell_1"],
            "time": ["2024-01-01T00:00:00Z", "2024-01-01T01:00:00Z"],
            "latitude": [19.0, 19.0],
            "longitude": [72.8, 72.8],
            "temperature_c": [25.0, np.nan],
        }
    )
    with pytest.raises(DataValidationError, match="unexpected null"):
        validate_weather_dataframe(df)


def test_quality_validation_detects_out_of_bounds_temperature():
    """Verify validator catches unphysical temperatures."""
    df = pd.DataFrame(
        {
            "grid_cell_id": ["cell_1", "cell_1"],
            "time": ["2024-01-01T00:00:00Z", "2024-01-01T01:00:00Z"],
            "latitude": [19.0, 19.0],
            "longitude": [72.8, 72.8],
            "temperature_c": [25.0, 95.0],
        }
    )
    with pytest.raises(DataValidationError, match="out of bounds"):
        validate_weather_dataframe(df)


def test_dataset_manifest_integrity():
    """Verify generated dataset manifest can be loaded and validates."""
    manifest_path = Path("data/processed/DATASET_MANIFEST.json")
    assert manifest_path.exists(), "DATASET_MANIFEST.json must exist"

    manifest = DatasetManifest.load(manifest_path)
    assert manifest.dataset_id == "heatsense_india_pilot_era5_land_v1"
    assert len(manifest.variables) >= 5
    assert manifest.spatial_coverage.cell_count == 546
    assert "pilot_weather.parquet" in manifest.checksums
