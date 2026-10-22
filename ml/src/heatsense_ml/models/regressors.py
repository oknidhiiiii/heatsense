"""Candidate machine learning forecasting estimators."""

from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor


def build_random_forest_regressor(
    random_seed: int = 42,
    n_estimators: int = 100,
    max_depth: int = 12,
    n_jobs: int = -1,
) -> RandomForestRegressor:
    """Build a reproducible RandomForestRegressor candidate."""
    return RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=10,
        min_samples_leaf=4,
        random_state=random_seed,
        n_jobs=n_jobs,
    )


def build_xgboost_regressor(
    random_seed: int = 42,
    n_estimators: int = 150,
    max_depth: int = 6,
    learning_rate: float = 0.08,
    n_jobs: int = -1,
) -> XGBRegressor:
    """Build a reproducible XGBoost regressor candidate."""
    return XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=random_seed,
        n_jobs=n_jobs,
        tree_method="hist",
    )
