"""Unit and integration tests for feature scaling and heatwave classification modules."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from heatsense_ml.classification.models import (
    build_classifier_suite,
    evaluate_classification_model,
)
from heatsense_ml.classification.target import (
    analyze_class_distribution,
    binarize_heatwave_target,
    compute_heatwave_thresholds,
)
from heatsense_ml.classification.visualizer import (
    plot_bagging_estimator_curves,
    plot_confusion_matrices,
)
from heatsense_ml.features.scaling import (
    MeteorologicalScaler,
    compare_scaling_effects,
)


@pytest.fixture
def sample_weather_features():
    """Create synthetic weather feature dataframe for testing."""
    np.random.seed(42)
    n = 200
    df = pd.DataFrame(
        {
            "temperature_c": np.random.uniform(20.0, 44.0, size=n),
            "dewpoint_c": np.random.uniform(10.0, 25.0, size=n),
            "ssrd": np.random.uniform(0.0, 950.0, size=n),
            "10u": np.random.normal(2.0, 1.5, size=n),
            "10v": np.random.normal(-1.0, 1.5, size=n),
            "temp_lag_0": np.random.uniform(20.0, 44.0, size=n),
            "temp_lag_24h": np.random.uniform(20.0, 44.0, size=n),
            "temp_rolling_mean_24h": np.random.uniform(22.0, 42.0, size=n),
            "solar_lag_0": np.random.uniform(0.0, 950.0, size=n),
            "wind_speed_lag_0": np.random.uniform(0.5, 8.0, size=n),
            "target_24h": np.random.uniform(20.0, 45.0, size=n),
        }
    )
    return df


def test_scaler_invalid_type():
    """Verify ValueError is raised on unsupported scaler type."""
    with pytest.raises(ValueError, match="Invalid scaler_type"):
        MeteorologicalScaler(scaler_type="quantile_unsupported")


def test_standard_scaler_mean_and_variance(sample_weather_features):
    """Verify StandardScaler normalizes features to approximately zero mean and unit variance."""
    cols = ["temperature_c", "dewpoint_c", "ssrd"]
    scaler = MeteorologicalScaler(scaler_type="standard", feature_cols=cols)

    scaled_df = scaler.fit_transform(sample_weather_features)

    for col in cols:
        assert np.isclose(scaled_df[col].mean(), 0.0, atol=1e-5)
        assert np.isclose(scaled_df[col].std(ddof=0), 1.0, atol=1e-5)


def test_minmax_scaler_bounds(sample_weather_features):
    """Verify MinMaxScaler transforms features strictly within [0, 1] range."""
    cols = ["temperature_c", "ssrd"]
    scaler = MeteorologicalScaler(scaler_type="minmax", feature_cols=cols)

    scaled_df = scaler.fit_transform(sample_weather_features)

    for col in cols:
        assert np.isclose(scaled_df[col].min(), 0.0, atol=1e-5)
        assert np.isclose(scaled_df[col].max(), 1.0, atol=1e-5)


def test_scaler_inverse_transform(sample_weather_features):
    """Verify inverse_transform restores exact original physical values."""
    cols = ["temperature_c", "ssrd"]
    scaler = MeteorologicalScaler(scaler_type="standard", feature_cols=cols)

    scaled_df = scaler.fit_transform(sample_weather_features)
    unscaled_df = scaler.inverse_transform(scaled_df)

    for col in cols:
        np.testing.assert_allclose(
            unscaled_df[col].values,
            sample_weather_features[col].values,
            rtol=1e-4,
            err_msg=f"Inverse transform failed to restore original values for {col}",
        )


def test_compare_scaling_effects(sample_weather_features):
    """Verify compare_scaling_effects benchmarks LinearRegression and KNNRegressor across scaling regimes."""
    train_df = sample_weather_features.iloc[:140]
    test_df = sample_weather_features.iloc[140:]

    feature_cols = ["temp_lag_0", "temp_lag_24h", "solar_lag_0", "wind_speed_lag_0"]
    y_tr = train_df["target_24h"].values
    y_te = test_df["target_24h"].values

    results = compare_scaling_effects(
        train_df[feature_cols],
        y_tr,
        test_df[feature_cols],
        y_te,
        feature_cols=feature_cols,
    )

    assert results["status"] == "SUCCESS"
    assert "LinearRegression" in results["benchmark_results"]
    assert "KNNRegressor" in results["benchmark_results"]

    # Verify all 3 configurations exist
    for model_name in ["LinearRegression", "RidgeRegression", "KNNRegressor"]:
        for cfg in ["unscaled_raw", "standard_scaled", "minmax_scaled"]:
            res = results["benchmark_results"][model_name][cfg]
            assert "mae_c" in res
            assert "rmse_c" in res
            assert "r2_score" in res


def test_target_binarization_and_thresholds():
    """Verify binarize_heatwave_target marks values >= 40 deg C as 1 and below as 0."""
    temps = np.array([32.0, 39.9, 40.0, 42.5, 38.0])
    labels = binarize_heatwave_target(temps, threshold_c=40.0)

    np.testing.assert_array_equal(labels, np.array([0, 0, 1, 1, 0]))

    meta = compute_heatwave_thresholds(temps, absolute_threshold_c=40.0, percentile_threshold=90.0)
    assert meta["absolute_threshold_c"] == 40.0
    assert meta["max_temp_c"] == 42.5
    assert meta["min_temp_c"] == 32.0


def test_analyze_class_distribution():
    """Verify analyze_class_distribution accurately computes counts and ratios."""
    y = np.array([0] * 90 + [1] * 10)
    dist = analyze_class_distribution(y)

    assert dist["total_samples"] == 100
    assert dist["normal_samples"] == 90
    assert dist["heatwave_samples"] == 10
    assert dist["heatwave_percentage"] == 10.0
    assert dist["imbalance_ratio"] == 9.0
    assert dist["is_imbalanced"] is True


def test_classifier_suite_construction_and_evaluation():
    """Verify all requested classifiers build, fit, and produce complete metrics."""
    np.random.seed(42)
    X = np.random.randn(120, 6)
    # Rare class imbalance (~12.5% positives)
    y = np.array([0] * 105 + [1] * 15)

    suite = build_classifier_suite(bagging_estimator_counts=[5, 10], random_state=42)

    expected_models = [
        "LogisticRegression",
        "KNNClassifier",
        "GaussianNaiveBayes",
        "DecisionTreeClassifier",
        "RandomForestClassifier",
        "BaggingClassifier_5",
        "BaggingClassifier_10",
    ]

    for model_name in expected_models:
        assert model_name in suite
        clf = suite[model_name]
        clf.fit(X, y)
        metrics = evaluate_classification_model(clf, X, y, model_name=model_name)

        assert "accuracy" in metrics
        assert "balanced_accuracy" in metrics
        assert "heatwave_precision" in metrics
        assert "heatwave_recall" in metrics
        assert "heatwave_f1" in metrics
        assert "confusion_matrix" in metrics
        cm = metrics["confusion_matrix"]
        assert cm["true_negatives"] + cm["false_positives"] + cm["false_negatives"] + cm["true_positives"] == 120


def test_visualizations_file_generation(tmp_path):
    """Verify plot_confusion_matrices and plot_bagging_estimator_curves write PNG files."""
    results = {
        "LogisticRegression": {
            "accuracy": 0.88,
            "heatwave_recall": 0.80,
            "heatwave_f1": 0.75,
            "confusion_matrix": {
                "true_negatives": 80,
                "false_positives": 10,
                "false_negatives": 2,
                "true_positives": 8,
                "raw_matrix": [[80, 10], [2, 8]],
            },
        },
        "RandomForestClassifier": {
            "accuracy": 0.92,
            "heatwave_recall": 0.85,
            "heatwave_f1": 0.82,
            "confusion_matrix": {
                "true_negatives": 84,
                "false_positives": 6,
                "false_negatives": 2,
                "true_positives": 8,
                "raw_matrix": [[84, 6], [2, 8]],
            },
        },
    }

    cm_path = tmp_path / "test_cm.png"
    plot_confusion_matrices(results, cm_path)
    assert cm_path.exists()
    assert cm_path.stat().st_size > 1000

    bagging_results = {
        5: {"accuracy": 0.85, "heatwave_recall": 0.70, "heatwave_f1": 0.72},
        10: {"accuracy": 0.88, "heatwave_recall": 0.75, "heatwave_f1": 0.76},
        50: {"accuracy": 0.90, "heatwave_recall": 0.80, "heatwave_f1": 0.81},
        100: {"accuracy": 0.91, "heatwave_recall": 0.82, "heatwave_f1": 0.83},
    }

    bagging_path = tmp_path / "test_bagging.png"
    plot_bagging_estimator_curves(bagging_results, bagging_path)
    assert bagging_path.exists()
    assert bagging_path.stat().st_size > 1000
