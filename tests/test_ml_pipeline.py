"""Tests for Stage 3 ML pipeline, causal feature leakage, and inference."""

import numpy as np
import pandas as pd
import pytest
from heatsense_ml.features.builder import (
    FEATURE_COLUMNS,
    extract_causal_features_for_cell,
)
from heatsense_ml.inference.predictor import ModelPredictor, SchemaValidationError
from heatsense_ml.training.trainer import split_chronologically


def test_causal_leakage_guard():
    """Verify modifying future observations does NOT alter past feature values."""
    times = pd.date_range("2024-01-01", periods=100, freq="1h")
    df1 = pd.DataFrame(
        {
            "grid_cell_id": ["cell_0"] * 100,
            "time": times,
            "latitude": [19.0] * 100,
            "longitude": [72.8] * 100,
            "temperature_c": np.sin(np.linspace(0, 10, 100)) + 25.0,
            "dewpoint_c": [18.0] * 100,
            "ssrd": [500.0] * 100,
            "10u": [2.0] * 100,
            "10v": [1.0] * 100,
        }
    )

    # Create modified dataset where values after index 50 are drastically changed
    df2 = df1.copy()
    df2.loc[50:, "temperature_c"] += 20.0
    df2.loc[50:, "dewpoint_c"] += 15.0

    feat1 = extract_causal_features_for_cell(df1)
    feat2 = extract_causal_features_for_cell(df2)

    # For all rows t < 50, all feature values MUST be identical
    for col in FEATURE_COLUMNS:
        np.testing.assert_allclose(
            feat1.loc[:49, col].values,
            feat2.loc[:49, col].values,
            err_msg=f"Causal leakage detected in feature '{col}' before time index 50!",
        )


def test_chronological_split_strictness():
    """Verify split is strictly ordered by time with zero overlap."""
    times = pd.date_range("2024-01-01", periods=100, freq="1h")
    df = pd.DataFrame(
        {
            "time": times,
            "grid_cell_id": ["c1"] * 100,
            "feature_1": range(100),
        }
    )

    train, val, test, split_info = split_chronologically(df, train_ratio=0.7, val_ratio=0.15)

    assert train["time"].max() < val["time"].min()
    assert val["time"].max() < test["time"].min()
    assert len(train) + len(val) + len(test) == len(df)


def test_predictor_schema_validation_with_real_artifacts():
    """Verify ModelPredictor loads real model artifact and validates schema."""
    from pathlib import Path

    model_file = Path("artifacts/models/v1/model_24h.joblib")
    meta_file = Path("artifacts/models/v1/model_24h_metadata.json")

    assert model_file.exists()
    assert meta_file.exists()

    predictor = ModelPredictor(model_file, meta_file)
    assert predictor.horizon_hours == 24
    assert len(predictor.feature_columns) == 21

    # Test failure on missing column
    bad_df = pd.DataFrame({"latitude": [19.0], "longitude": [72.8]})
    with pytest.raises(SchemaValidationError, match="missing required columns"):
        predictor.predict(bad_df)

