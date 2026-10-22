"""Tests verifying heatsense_ml package imports and configuration."""

import heatsense_ml
from heatsense_ml.config import BoundingBox, default_ml_config


def test_ml_package_version():
    """Verify package version is defined."""
    assert heatsense_ml.__version__ == "0.1.0"


def test_ml_config_pilot_bounds():
    """Verify pilot domain matches Western India ADR 0004 specifications."""
    bbox = default_ml_config.pilot_bbox
    assert isinstance(bbox, BoundingBox)
    assert bbox.min_lat == 18.0
    assert bbox.max_lat == 20.5
    assert bbox.min_lon == 72.5
    assert bbox.max_lon == 74.5
    assert default_ml_config.target_horizons == [24, 48]
