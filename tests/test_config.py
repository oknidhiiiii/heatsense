"""Tests for backend configuration."""

from heatsense_api.config import settings


def test_settings_defaults():
    """Verify backend settings have safe, valid defaults."""
    assert settings.version == "0.1.0"
    assert settings.api_prefix == "/api/v1"
    assert settings.supported_regions == ["IN"]
    assert settings.max_search_limit > 0
    assert settings.max_grid_area_deg2 > 0
