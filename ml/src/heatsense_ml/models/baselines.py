"""Baseline forecasting models for meteorological benchmarks."""

import numpy as np
import pandas as pd


class PersistenceBaseline:
    """Predicts temperature at t + H equals the latest observation at initialization time t."""

    def __init__(self):
        self.name = "Persistence"

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "PersistenceBaseline":
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X["temp_lag_0"].values.astype(np.float32)


class DiurnalPersistenceBaseline:
    """Predicts temperature at t + H equals observation at same solar hour yesterday (t - 24h)."""

    def __init__(self):
        self.name = "DiurnalPersistence"

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "DiurnalPersistenceBaseline":
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X["temp_lag_24h"].values.astype(np.float32)
