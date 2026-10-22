"""Inference engine and model predictor interface."""

import json
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd


class SchemaValidationError(Exception):
    """Raised when inference features do not conform to trained model schema."""

    pass


class ModelPredictor:
    """Predictor for a single forecast horizon with strict schema validation."""

    def __init__(self, model_path: Path, metadata_path: Path):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model artifact not found: {self.model_path}")
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")

        self.model = joblib.load(self.model_path)
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata: Dict[str, Any] = json.load(f)

        self.model_id: str = self.metadata["model_id"]
        self.model_version: str = self.metadata["model_version"]
        self.horizon_hours: int = self.metadata["horizon_hours"]
        self.feature_columns: List[str] = self.metadata["feature_columns"]

    def validate_features(self, df: pd.DataFrame) -> None:
        """Validate input features match model's expected columns and types."""
        missing = [c for c in self.feature_columns if c not in df.columns]
        if missing:
            raise SchemaValidationError(
                f"Input features missing required columns for {self.model_id}: {missing}"
            )
        # Check for NaNs
        null_counts = df[self.feature_columns].isnull().sum()
        if null_counts.sum() > 0:
            bad_cols = null_counts[null_counts > 0].to_dict()
            raise SchemaValidationError(f"Input features contain unexpected nulls: {bad_cols}")

    def predict(self, features_df: pd.DataFrame) -> np.ndarray:
        """Generate point temperature predictions in °C."""
        self.validate_features(features_df)
        X = features_df[self.feature_columns]
        preds = self.model.predict(X)
        return np.round(preds.astype(np.float64), 2)


class HeatSensePredictorBundle:
    """Multi-horizon bundle loading both 24h and 48h models."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.predictors: Dict[int, ModelPredictor] = {}
        self._load_bundle()

    def _load_bundle(self) -> None:
        for horizon in [24, 48]:
            m_path = self.artifacts_dir / f"model_{horizon}h.joblib"
            meta_path = self.artifacts_dir / f"model_{horizon}h_metadata.json"
            if m_path.exists() and meta_path.exists():
                self.predictors[horizon] = ModelPredictor(m_path, meta_path)

    @property
    def is_loaded(self) -> bool:
        return 24 in self.predictors and 48 in self.predictors

    def get_predictor(self, horizon: int) -> ModelPredictor:
        if horizon not in self.predictors:
            raise ValueError(
                f"Horizon {horizon}h is not loaded. Supported: {list(self.predictors.keys())}"
            )
        return self.predictors[horizon]

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Return metrics items for all loaded models matching API contract."""
        items = []
        for horizon, p in self.predictors.items():
            metrics_dict = p.metadata.get("metrics", {})
            sel_metrics = metrics_dict.get("selected_model", {})
            for m_name, m_val in sel_metrics.items():
                items.append(
                    {
                        "model_id": p.model_id,
                        "model_version": p.model_version,
                        "horizon_hours": horizon,
                        "metric_name": m_name,
                        "metric_value": float(m_val),
                        "unit": "degC" if "c" in m_name else "",
                        "baseline_value": metrics_dict.get("baseline_diurnal", {}).get(m_name),
                        "test_start": p.metadata.get("test_period", {}).get("start", ""),
                        "test_end": p.metadata.get("test_period", {}).get("end", ""),
                        "sample_count": p.metadata.get("test_samples", 0),
                        "evaluation_run_id": f"run_{p.model_version}_{horizon}h",
                    }
                )
        return items
