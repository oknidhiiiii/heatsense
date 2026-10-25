"""Meteorological feature scaling transformers and benchmark comparison utilities.

Provides StandardScaler and MinMaxScaler transformers for continuous weather variables,
strictly ensuring scaler parameters are fitted only on training splits to prevent
temporal lookahead leakage.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import MinMaxScaler, StandardScaler

logger = logging.getLogger("heatsense_ml.scaling")

# Continuous raw meteorological observation fields
RAW_METEOROLOGICAL_COLUMNS: List[str] = [
    "temperature_c",
    "dewpoint_c",
    "ssrd",
    "10u",
    "10v",
]

# Continuous causal lag features (excluding bounded sinusoidal calendar features)
CONTINUOUS_CAUSAL_FEATURE_COLUMNS: List[str] = [
    "latitude",
    "longitude",
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


class MeteorologicalScaler:
    """Preprocesses continuous meteorological features using StandardScaler or MinMaxScaler.

    Ensures zero temporal lookahead leakage by fitting statistical distribution
    parameters strictly on historical training datasets.
    """

    def __init__(
        self,
        scaler_type: str = "standard",
        feature_cols: Optional[List[str]] = None,
        copy: bool = True,
    ):
        """Initialize the meteorological scaler.

        Args:
            scaler_type: Either 'standard' (StandardScaler) or 'minmax' (MinMaxScaler).
            feature_cols: Specific columns to scale. If None, all numeric columns are scaled.
            copy: Whether to create a copy of inputs during transformations.
        """
        valid_types = {"standard", "minmax"}
        normalized_type = scaler_type.lower().strip()
        if normalized_type not in valid_types:
            raise ValueError(
                f"Invalid scaler_type '{scaler_type}'. Supported types: {sorted(valid_types)}"
            )

        self.scaler_type = normalized_type
        self.feature_cols = feature_cols
        self.copy = copy

        if self.scaler_type == "standard":
            self.transformer = StandardScaler(copy=self.copy)
        else:
            self.transformer = MinMaxScaler(copy=self.copy)

        self.is_fitted = False
        self._fitted_columns: Optional[List[str]] = None

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Optional[Any] = None,
    ) -> "MeteorologicalScaler":
        """Fit scaler parameters on training data only.

        Args:
            X: Training DataFrame or 2D NumPy array.
            y: Ignored (present for scikit-learn API compatibility).

        Returns:
            self: Fitted scaler instance.
        """
        if isinstance(X, pd.DataFrame):
            cols_to_fit = self._resolve_columns(X)
            self._fitted_columns = cols_to_fit
            self.transformer.fit(X[cols_to_fit])
        else:
            self._fitted_columns = None
            self.transformer.fit(X)

        self.is_fitted = True
        return self

    def transform(
        self,
        X: Union[pd.DataFrame, np.ndarray],
    ) -> Union[pd.DataFrame, np.ndarray]:
        """Transform data using fitted parameters.

        Args:
            X: DataFrame or array to transform.

        Returns:
            Transformed DataFrame or array matching original input structure.
        """
        if not self.is_fitted:
            raise RuntimeError("MeteorologicalScaler must be fitted before calling transform().")

        if isinstance(X, pd.DataFrame):
            out_df = X.copy() if self.copy else X
            cols = self._fitted_columns if self._fitted_columns is not None else self._resolve_columns(X)
            scaled_values = self.transformer.transform(out_df[cols])
            out_df[cols] = scaled_values
            return out_df

        return self.transformer.transform(X)

    def fit_transform(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Optional[Any] = None,
    ) -> Union[pd.DataFrame, np.ndarray]:
        """Fit scaler on X and return transformed dataset."""
        return self.fit(X, y).transform(X)

    def inverse_transform(
        self,
        X: Union[pd.DataFrame, np.ndarray],
    ) -> Union[pd.DataFrame, np.ndarray]:
        """Invert scaled values back to their original physical units."""
        if not self.is_fitted:
            raise RuntimeError("MeteorologicalScaler must be fitted before calling inverse_transform().")

        if isinstance(X, pd.DataFrame):
            out_df = X.copy() if self.copy else X
            cols = self._fitted_columns if self._fitted_columns is not None else self._resolve_columns(X)
            unscaled_values = self.transformer.inverse_transform(out_df[cols])
            out_df[cols] = unscaled_values
            return out_df

        return self.transformer.inverse_transform(X)

    def get_feature_statistics(self) -> Dict[str, Dict[str, float]]:
        """Return summary dictionary of fitted scaling parameters per feature."""
        if not self.is_fitted:
            raise RuntimeError("Scaler is not fitted yet.")

        stats: Dict[str, Dict[str, float]] = {}
        cols = self._fitted_columns or [f"feature_{i}" for i in range(self.transformer.n_features_in_)]

        if self.scaler_type == "standard":
            means = self.transformer.mean_
            scales = self.transformer.scale_
            for idx, col in enumerate(cols):
                stats[col] = {
                    "mean": float(means[idx]),
                    "scale_std": float(scales[idx]),
                }
        else:
            mins = self.transformer.data_min_
            maxs = self.transformer.data_max_
            for idx, col in enumerate(cols):
                stats[col] = {
                    "data_min": float(mins[idx]),
                    "data_max": float(maxs[idx]),
                }

        return stats

    def _resolve_columns(self, df: pd.DataFrame) -> List[str]:
        if self.feature_cols is not None:
            missing = [c for c in self.feature_cols if c not in df.columns]
            if missing:
                raise KeyError(f"Specified feature columns not found in DataFrame: {missing}")
            return list(self.feature_cols)

        # Default to continuous meteorological columns if present, otherwise all numeric
        found_continuous = [c for c in CONTINUOUS_CAUSAL_FEATURE_COLUMNS if c in df.columns]
        if found_continuous:
            return found_continuous

        found_raw = [c for c in RAW_METEOROLOGICAL_COLUMNS if c in df.columns]
        if found_raw:
            return found_raw

        return list(df.select_dtypes(include=[np.number]).columns)


def compare_scaling_effects(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    feature_cols: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Benchmark regression models across Unscaled, StandardScaler, and MinMaxScaler.

    Evaluates Linear Regression, Ridge, and K-Nearest Neighbors to empirically
    demonstrate the critical importance of feature scaling for distance- and
    gradient-based estimators.

    Args:
        X_train: Historical training feature DataFrame.
        y_train: Historical training target values.
        X_test: Held-out test feature DataFrame.
        y_test: Held-out test target values.
        feature_cols: Continuous columns to scale.

    Returns:
        Structured dictionary containing metrics, comparison table, and insights.
    """
    cols_to_scale = (
        feature_cols
        if feature_cols is not None
        else [c for c in CONTINUOUS_CAUSAL_FEATURE_COLUMNS if c in X_train.columns]
    )

    # 1. Prepare three feature configurations
    # A. Unscaled (Raw)
    X_tr_raw = X_train.copy()
    X_te_raw = X_test.copy()

    # B. StandardScaler
    std_scaler = MeteorologicalScaler(scaler_type="standard", feature_cols=cols_to_scale)
    X_tr_std = std_scaler.fit_transform(X_train)
    X_te_std = std_scaler.transform(X_test)

    # C. MinMaxScaler
    mm_scaler = MeteorologicalScaler(scaler_type="minmax", feature_cols=cols_to_scale)
    X_tr_mm = mm_scaler.fit_transform(X_train)
    X_te_mm = mm_scaler.transform(X_test)

    configurations = {
        "unscaled_raw": (X_tr_raw, X_te_raw),
        "standard_scaled": (X_tr_std, X_te_std),
        "minmax_scaled": (X_tr_mm, X_te_mm),
    }

    # Models to benchmark
    model_factories = {
        "LinearRegression": lambda: LinearRegression(),
        "RidgeRegression": lambda: Ridge(alpha=10.0),
        "KNNRegressor": lambda: KNeighborsRegressor(n_neighbors=5, weights="distance"),
    }

    benchmark_results: Dict[str, Dict[str, Dict[str, float]]] = {}
    table_rows: List[Dict[str, Any]] = []

    for model_name, factory in model_factories.items():
        benchmark_results[model_name] = {}
        for config_name, (X_tr, X_te) in configurations.items():
            model = factory()
            model.fit(X_tr, y_train)
            preds = model.predict(X_te)

            mae = float(mean_absolute_error(y_test, preds))
            rmse = float(root_mean_squared_error(y_test, preds))
            r2 = float(r2_score(y_test, preds))

            metrics = {
                "mae_c": round(mae, 4),
                "rmse_c": round(rmse, 4),
                "r2_score": round(r2, 4),
            }
            benchmark_results[model_name][config_name] = metrics

            table_rows.append(
                {
                    "model": model_name,
                    "scaling_technique": config_name,
                    "mae_c": metrics["mae_c"],
                    "rmse_c": metrics["rmse_c"],
                    "r2_score": metrics["r2_score"],
                }
            )

    # Calculate error reduction for KNN (which is most sensitive to distance scaling)
    knn_raw_mae = benchmark_results["KNNRegressor"]["unscaled_raw"]["mae_c"]
    knn_std_mae = benchmark_results["KNNRegressor"]["standard_scaled"]["mae_c"]
    knn_improvement_pct = round(((knn_raw_mae - knn_std_mae) / knn_raw_mae) * 100.0, 2)

    return {
        "status": "SUCCESS",
        "scaled_feature_count": len(cols_to_scale),
        "scaled_columns": cols_to_scale,
        "sample_counts": {"train": len(X_train), "test": len(y_test)},
        "benchmark_results": benchmark_results,
        "comparison_table": table_rows,
        "key_findings": [
            f"Distance-based models (KNN) achieve {knn_improvement_pct}% MAE reduction under StandardScaler.",
            "Solar radiation (0 to 1000 W/m2) dominates unscaled Euclidean distance without feature normalization.",
            "Tree models remain invariant to monotonic scaling, while linear and distance estimators require standardization.",
        ],
    }
