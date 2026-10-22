"""Data quality validation and reporting utilities."""

from typing import Any, Dict, List

import numpy as np
import pandas as pd


class DataValidationError(Exception):
    """Raised when weather dataset violates meteorological or integrity constraints."""

    pass


def validate_weather_dataframe(
    df: pd.DataFrame,
    min_temp_c: float = -10.0,
    max_temp_c: float = 65.0,
    required_cols: List[str] = None,
) -> Dict[str, Any]:
    """Validate tabular weather dataset for completeness, monotonicity, and bounds.

    Returns a summary report dict if valid; raises DataValidationError on breach.
    """
    if required_cols is None:
        required_cols = ["grid_cell_id", "time", "latitude", "longitude", "temperature_c"]

    # 1. Required columns
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns in dataset: {missing_cols}")

    # 2. Null values
    null_counts = df[required_cols].isnull().sum().to_dict()
    total_nulls = sum(null_counts.values())
    if total_nulls > 0:
        raise DataValidationError(f"Dataset contains unexpected null values: {null_counts}")

    # 3. Coordinate bounds
    if not df["latitude"].between(-90.0, 90.0).all():
        raise DataValidationError("Latitudes out of valid range [-90, 90]")
    if not df["longitude"].between(-180.0, 360.0).all():
        raise DataValidationError("Longitudes out of valid range [-180, 360]")

    # 4. Temperature range sanity
    actual_min = float(df["temperature_c"].min())
    actual_max = float(df["temperature_c"].max())
    if actual_min < min_temp_c or actual_max > max_temp_c:
        raise DataValidationError(
            f"Temperature value out of bounds: min={actual_min}°C, max={actual_max}°C "
            f"(expected [{min_temp_c}, {max_temp_c}])"
        )

    # 5. Monotonic timestamps per cell
    sample_cell = df["grid_cell_id"].iloc[0]
    cell_times = pd.to_datetime(df[df["grid_cell_id"] == sample_cell]["time"])
    if not cell_times.is_monotonic_increasing:
        raise DataValidationError(
            f"Timestamps for {sample_cell} are not strictly monotonic increasing"
        )

    # Time step delta check
    time_diffs = cell_times.diff().dropna()
    expected_step = pd.Timedelta(hours=1)
    if not (time_diffs == expected_step).all():
        bad_steps = time_diffs[time_diffs != expected_step]
        raise DataValidationError(
            f"Non-hourly timestamp steps detected in sample cell: {bad_steps.head()}"
        )

    unique_cells = df["grid_cell_id"].nunique()
    total_rows = len(df)

    return {
        "status": "VALID",
        "total_rows": total_rows,
        "unique_cells": unique_cells,
        "timesteps_per_cell": total_rows // unique_cells if unique_cells > 0 else 0,
        "temp_min_c": actual_min,
        "temp_max_c": actual_max,
        "temp_mean_c": float(np.round(df["temperature_c"].mean(), 2)),
        "null_counts": null_counts,
    }
