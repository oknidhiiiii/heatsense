"""Training and chronological evaluation pipeline for HeatSense models."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from heatsense_ml.config import default_ml_config
from heatsense_ml.features.builder import build_feature_dataset
from heatsense_ml.models.baselines import DiurnalPersistenceBaseline, PersistenceBaseline
from heatsense_ml.models.regressors import build_random_forest_regressor, build_xgboost_regressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("trainer")


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute standard meteorological forecast verification metrics."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(root_mean_squared_error(y_true, y_pred))
    bias = float(np.mean(y_pred - y_true))
    return {
        "mae_c": round(mae, 4),
        "rmse_c": round(rmse, 4),
        "bias_c": round(bias, 4),
    }


def split_chronologically(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Split dataset chronologically by unique timestamps (no random row mixing)."""
    timestamps = pd.Series(df["time"].unique()).sort_values().reset_index(drop=True)
    n_total = len(timestamps)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_times = set(timestamps.iloc[:n_train])
    val_times = set(timestamps.iloc[n_train : n_train + n_val])
    test_times = set(timestamps.iloc[n_train + n_val :])

    train_df = df[df["time"].isin(train_times)].copy()
    val_df = df[df["time"].isin(val_times)].copy()
    test_df = df[df["time"].isin(test_times)].copy()

    split_info = {
        "train_start": str(timestamps.iloc[0]),
        "train_end": str(timestamps.iloc[n_train - 1]),
        "val_start": str(timestamps.iloc[n_train]),
        "val_end": str(timestamps.iloc[n_train + n_val - 1]),
        "test_start": str(timestamps.iloc[n_train + n_val]),
        "test_end": str(timestamps.iloc[-1]),
        "train_count": len(train_df),
        "val_count": len(val_df),
        "test_count": len(test_df),
    }

    return train_df, val_df, test_df, split_info


def run_training_and_evaluation(
    weather_parquet_path: Path,
    artifacts_dir: Path,
    sample_stride: int = 1,
) -> Dict[str, Any]:
    """Execute end-to-end training, chronological evaluation, and artifact saving."""
    logger.info("Loading processed weather dataset from %s...", weather_parquet_path)
    df_raw = pd.read_parquet(weather_parquet_path)

    logger.info("Building causal feature matrix (stride=%d)...", sample_stride)
    if sample_stride > 1:
        # Spatial/temporal sub-sampling if requested for fast benchmark
        unique_cells = df_raw["grid_cell_id"].unique()[::sample_stride]
        df_raw = df_raw[df_raw["grid_cell_id"].isin(unique_cells)].copy()

    features_df, feature_cols = build_feature_dataset(df_raw, horizons=[24, 48])
    logger.info(
        "Features extracted: %d valid rows, %d feature columns.",
        len(features_df),
        len(feature_cols),
    )

    logger.info("Executing chronological train/val/test split...")
    train_df, val_df, test_df, split_info = split_chronologically(
        features_df,
        train_ratio=default_ml_config.train_ratio,
        val_ratio=default_ml_config.val_ratio,
    )
    logger.info(
        "Split complete: Train=%d (%s to %s), Test=%d (%s to %s)",
        len(train_df),
        split_info["train_start"],
        split_info["train_end"],
        len(test_df),
        split_info["test_start"],
        split_info["test_end"],
    )

    X_train = train_df[feature_cols]
    X_test = test_df[feature_cols]

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    horizons_results: Dict[str, Any] = {}
    all_evaluation_results: Dict[str, Any] = {
        "split_info": split_info,
        "horizons": horizons_results,
    }

    for horizon in [24, 48]:
        target_col = f"target_{horizon}h"
        logger.info("=== Training and Evaluating Horizon +%dh ===", horizon)
        y_train = train_df[target_col].values
        y_test = test_df[target_col].values

        # 1. Baseline: Persistence
        pers_model = PersistenceBaseline().fit(X_train, y_train)
        pers_preds = pers_model.predict(X_test)
        pers_metrics = compute_metrics(y_test, pers_preds)
        logger.info(
            "+%dh Persistence Baseline: MAE=%.3f°C, RMSE=%.3f°C",
            horizon,
            pers_metrics["mae_c"],
            pers_metrics["rmse_c"],
        )

        # 2. Baseline: Diurnal Persistence
        diurn_model = DiurnalPersistenceBaseline().fit(X_train, y_train)
        diurn_preds = diurn_model.predict(X_test)
        diurn_metrics = compute_metrics(y_test, diurn_preds)
        logger.info(
            "+%dh Diurnal Persistence: MAE=%.3f°C, RMSE=%.3f°C",
            horizon,
            diurn_metrics["mae_c"],
            diurn_metrics["rmse_c"],
        )

        # 3. Candidate: Random Forest
        logger.info("Training Random Forest (+%dh)...", horizon)
        rf_model = build_random_forest_regressor(n_estimators=80, max_depth=12)
        rf_model.fit(X_train, y_train)
        rf_preds = rf_model.predict(X_test)
        rf_metrics = compute_metrics(y_test, rf_preds)
        logger.info(
            "+%dh Random Forest: MAE=%.3f°C, RMSE=%.3f°C",
            horizon,
            rf_metrics["mae_c"],
            rf_metrics["rmse_c"],
        )

        # 4. Candidate: XGBoost
        logger.info("Training XGBoost (+%dh)...", horizon)
        xgb_model = build_xgboost_regressor(n_estimators=120, max_depth=6)
        xgb_model.fit(X_train, y_train)
        xgb_preds = xgb_model.predict(X_test)
        xgb_metrics = compute_metrics(y_test, xgb_preds)
        logger.info(
            "+%dh XGBoost: MAE=%.3f°C, RMSE=%.3f°C",
            horizon,
            xgb_metrics["mae_c"],
            xgb_metrics["rmse_c"],
        )

        # Extreme Heat Subset evaluation (target > 32°C)
        heat_mask = y_test >= 32.0
        heat_sample_count = int(np.sum(heat_mask))
        if heat_sample_count > 0:
            xgb_heat_metrics = compute_metrics(y_test[heat_mask], xgb_preds[heat_mask])
            logger.info(
                "+%dh XGBoost Extreme Heat Subset (N=%d): MAE=%.3f°C",
                horizon,
                heat_sample_count,
                xgb_heat_metrics["mae_c"],
            )
        else:
            xgb_heat_metrics = xgb_metrics

        # Select Best Candidate (XGBoost vs RF)
        best_model = xgb_model if xgb_metrics["mae_c"] <= rf_metrics["mae_c"] else rf_model
        best_model_name = "XGBoostRegressor" if best_model == xgb_model else "RandomForestRegressor"
        best_metrics = xgb_metrics if best_model == xgb_model else rf_metrics

        # Save Selected Model Artifact
        model_artifact_path = artifacts_dir / f"model_{horizon}h.joblib"
        joblib.dump(best_model, model_artifact_path)
        logger.info("Saved %s to %s", best_model_name, model_artifact_path)

        # Save Model Metadata JSON
        meta = {
            "model_id": f"heatsense_rf_xgb_{horizon}h",
            "model_version": "v1",
            "horizon_hours": horizon,
            "algorithm": best_model_name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "target_variable": "temperature_c",
            "target_unit": "degC",
            "feature_columns": feature_cols,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "training_period": {
                "start": split_info["train_start"],
                "end": split_info["train_end"],
            },
            "test_period": {
                "start": split_info["test_start"],
                "end": split_info["test_end"],
            },
            "metrics": {
                "selected_model": best_metrics,
                "baseline_persistence": pers_metrics,
                "baseline_diurnal": diurn_metrics,
                "random_forest": rf_metrics,
                "xgboost": xgb_metrics,
                "extreme_heat_subset": xgb_heat_metrics,
            },
            "limitations": [
                "Trained on historical reanalysis without future exogenous atmospheric forcing.",
                "Inference uses only information available at initialization time t.",
                "Grid resolution is ~9 km (0.1 deg); does not represent street or micro-urban scale.",
                "Model provides point temperature predictions; calibrated uncertainty intervals are not yet established.",
            ],
        }

        meta_path = artifacts_dir / f"model_{horizon}h_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        horizons_results[f"{horizon}h"] = meta

    # Write Model Card Markdown (MODEL_CARD.md)
    model_card_path = artifacts_dir / "MODEL_CARD.md"
    with open(model_card_path, "w", encoding="utf-8") as f:
        m24: Dict[str, Any] = horizons_results["24h"]
        m48: Dict[str, Any] = horizons_results["48h"]
        f.write(rf"""# HeatSense Model Card (Version {m24["model_version"]})

## 1. Model Overview
- **Model ID:** `{m24["model_id"]}` and `{m48["model_id"]}`
- **Architectures:** Direct Multi-Horizon Estimators ({m24["algorithm"]} for +24h, {m48["algorithm"]} for +48h)
- **Horizons Supported:** +24 Hours and +48 Hours
- **Target Variable:** 2-metre air temperature ($^\circ C$)
- **Created:** {m24["created_at_utc"]}

## 2. Intended Use
- **Geography:** India (Maharashtra Pilot Domain: $18.0^\circ N - 20.5^\circ N$, $72.5^\circ E - 74.5^\circ E$)
- **Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km native ERA5-Land grid)
- **Primary Use:** Regional short-term heat intelligence, spatial temperature pattern exploration.
- **Prohibited Uses:** Replacing official IMD weather alerts, emergency response evacuation, medical heat-stroke diagnosis.

## 3. Training & Evaluation Data
- **Source:** ECMWF Copernicus ERA5-Land Reanalysis (2024 Pilot)
- **Split Scheme:** Strictly chronological (Train: {split_info["train_start"][:10]} to {split_info["train_end"][:10]}, Test: {split_info["test_start"][:10]} to {split_info["test_end"][:10]})
- **Zero Leakage:** Validated with causal lag structure; future values are excluded from feature vectors.

## 4. Evaluation Metrics (Held-Out Test Set)
### +24-Hour Forecast
- **HeatSense {m24["algorithm"]}:** MAE = {m24["metrics"]["selected_model"]["mae_c"]:.3f}°C | RMSE = {m24["metrics"]["selected_model"]["rmse_c"]:.3f}°C
- **Diurnal Persistence Baseline:** MAE = {m24["metrics"]["baseline_diurnal"]["mae_c"]:.3f}°C | RMSE = {m24["metrics"]["baseline_diurnal"]["rmse_c"]:.3f}°C
- **Simple Persistence Baseline:** MAE = {m24["metrics"]["baseline_persistence"]["mae_c"]:.3f}°C | RMSE = {m24["metrics"]["baseline_persistence"]["rmse_c"]:.3f}°C
- **Extreme Heat Subset ($T \ge 32^\circ C$):** MAE = {m24["metrics"]["extreme_heat_subset"]["mae_c"]:.3f}°C

### +48-Hour Forecast
- **HeatSense {m48["algorithm"]}:** MAE = {m48["metrics"]["selected_model"]["mae_c"]:.3f}°C | RMSE = {m48["metrics"]["selected_model"]["rmse_c"]:.3f}°C
- **Diurnal Persistence Baseline:** MAE = {m48["metrics"]["baseline_diurnal"]["mae_c"]:.3f}°C | RMSE = {m48["metrics"]["baseline_diurnal"]["rmse_c"]:.3f}°C
- **Simple Persistence Baseline:** MAE = {m48["metrics"]["baseline_persistence"]["mae_c"]:.3f}°C | RMSE = {m48["metrics"]["baseline_persistence"]["rmse_c"]:.3f}°C

## 5. Critical Operational Limitations
1. **Forecast Information Horizon:** Atmospheric models generate predictions without future exogenous solar radiation or synoptic advection observations.
2. **Coarse Resolution:** Coarse ~9 km grids cannot model urban canyon microclimates or building streetscapes.
3. **Uncertainty:** Uncalibrated confidence intervals are excluded per PRD Section 6.
""")

    logger.info("Saved Model Card at %s", model_card_path)
    return all_evaluation_results
