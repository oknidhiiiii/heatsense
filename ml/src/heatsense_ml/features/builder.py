"""Causal feature engineering pipeline for HeatSense temperature forecasting.

Strictly enforces causal ordering: features at initialization timestamp t
only use observations <= t. Future observations are NEVER accessed.
"""

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# Explicit canonical feature column list
FEATURE_COLUMNS = [
    "latitude",
    "longitude",
    "hour_sin",
    "hour_cos",
    "doy_sin",
    "doy_cos",
    "temp_lag_0",
    "temp_lag_1h",
    "temp_lag_3h",
    "temp_lag_6h",
    "temp_lag_12h",
    "temp_lag_24h",
    "temp_rolling_mean_24h",
    "temp_rolling_max_24h",
    "temp_rolling_min_24h",
    "dewpoint_lag_0",
    "dewpoint_lag_6h",
    "dewpoint_lag_24h",
    "solar_lag_0",
    "solar_lag_24h",
    "wind_speed_lag_0",
]


def extract_causal_features_for_cell(cell_df: pd.DataFrame) -> pd.DataFrame:
    """Extract causal features for a single contiguous grid cell sorted by time."""
    df = cell_df.sort_values("time").reset_index(drop=True)

    times = pd.to_datetime(df["time"])
    hours = times.dt.hour.values
    doy = getattr(times.dt, "day_of_year", times.dt.dayofyear).values

    # Cyclic astronomical & calendar encodings
    df["hour_sin"] = np.sin(2 * np.pi * hours / 24.0).astype(np.float32)
    df["hour_cos"] = np.cos(2 * np.pi * hours / 24.0).astype(np.float32)
    df["doy_sin"] = np.sin(2 * np.pi * (doy - 1) / 365.25).astype(np.float32)
    df["doy_cos"] = np.cos(2 * np.pi * (doy - 1) / 365.25).astype(np.float32)

    # Temperature lags (lag 0 is current observation at initialization time t)
    t = df["temperature_c"]
    df["temp_lag_0"] = t.astype(np.float32)
    df["temp_lag_1h"] = t.shift(1).astype(np.float32)
    df["temp_lag_3h"] = t.shift(3).astype(np.float32)
    df["temp_lag_6h"] = t.shift(6).astype(np.float32)
    df["temp_lag_12h"] = t.shift(12).astype(np.float32)
    df["temp_lag_24h"] = t.shift(24).astype(np.float32)

    # Rolling statistics over past 24 hours (inclusive of t, strictly past <= t)
    # pandas rolling(24) computes over window [t-23, t]
    df["temp_rolling_mean_24h"] = t.rolling(24).mean().astype(np.float32)
    df["temp_rolling_max_24h"] = t.rolling(24).max().astype(np.float32)
    df["temp_rolling_min_24h"] = t.rolling(24).min().astype(np.float32)

    # Dewpoint lags
    d = df["dewpoint_c"]
    df["dewpoint_lag_0"] = d.astype(np.float32)
    df["dewpoint_lag_6h"] = d.shift(6).astype(np.float32)
    df["dewpoint_lag_24h"] = d.shift(24).astype(np.float32)

    # Solar radiation lags
    s = df["ssrd"] if "ssrd" in df.columns else pd.Series(0.0, index=df.index)
    df["solar_lag_0"] = s.astype(np.float32)
    df["solar_lag_24h"] = s.shift(24).astype(np.float32)

    # Wind speed magnitude at t
    if "10u" in df.columns and "10v" in df.columns:
        df["wind_speed_lag_0"] = np.sqrt(df["10u"] ** 2 + df["10v"] ** 2).astype(np.float32)
    else:
        df["wind_speed_lag_0"] = np.float32(0.0)

    # Multi-horizon forecast targets (future observations to predict)
    df["target_24h"] = t.shift(-24).astype(np.float32)
    df["target_48h"] = t.shift(-48).astype(np.float32)

    return df


def build_feature_dataset(
    weather_df: pd.DataFrame,
    horizons: Optional[List[int]] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """Build causal feature matrix from weather dataframe across all grid cells.

    Drops initial warm-up rows (24h lag window) and tail rows lacking target labels.
    Returns: (cleaned_features_df, feature_column_names)
    """
    if horizons is None:
        horizons = [24, 48]
    max_horizon = max(horizons)

    # Apply causal feature extraction per grid cell
    feature_dfs = []
    for _, cell_group in weather_df.groupby("grid_cell_id", as_index=False):
        cell_features = extract_causal_features_for_cell(cell_group)
        # Drop warm-up lag rows (first 24 hours have NaN for lag_24h)
        # and tail rows (last max_horizon hours have NaN for future targets)
        valid_mask = (
            cell_features["temp_lag_24h"].notnull()
            & cell_features[f"target_{max_horizon}h"].notnull()
        )
        feature_dfs.append(cell_features[valid_mask])

    full_features_df = pd.concat(feature_dfs, ignore_index=True)
    full_features_df = full_features_df.sort_values(["time", "grid_cell_id"]).reset_index(drop=True)

    return full_features_df, FEATURE_COLUMNS
