"""End-to-end heatwave hazard classification pipeline runner."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
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
from heatsense_ml.features.builder import FEATURE_COLUMNS
from heatsense_ml.features.scaling import MeteorologicalScaler

logger = logging.getLogger("heatsense_ml.classification.pipeline")


def run_heatwave_classification_pipeline(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    target_col: str = "target_24h",
    threshold_c: float = 40.0,
    artifacts_dir: Optional[Path] = None,
    bagging_estimator_counts: Optional[List[int]] = None,
    sample_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute end-to-end heatwave hazard classification pipeline.

    Args:
        train_df: Chronologically split historical training DataFrame.
        test_df: Chronologically split held-out test DataFrame.
        feature_cols: Feature columns to use. Defaults to FEATURE_COLUMNS.
        target_col: Column name of continuous forward temperature target.
        threshold_c: Temperature threshold defining a Heatwave Warning event (default: 40.0 deg C).
        artifacts_dir: Destination directory for report JSON and visualization plots.
        bagging_estimator_counts: Estimator counts to evaluate for BaggingClassifier.
        sample_limit: Optional subsampling limit for rapid benchmarking.

    Returns:
        Structured dictionary containing class distribution, threshold metadata,
        model evaluation results, and artifact file paths.
    """
    if feature_cols is None:
        feature_cols = [c for c in FEATURE_COLUMNS if c in train_df.columns]

    if bagging_estimator_counts is None:
        bagging_estimator_counts = [5, 10, 50, 100]

    if artifacts_dir is None:
        artifacts_dir = Path("artifacts/classification")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = artifacts_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Subsample if requested for bounded execution time
    tr_df = train_df if sample_limit is None else train_df.tail(sample_limit).copy()
    te_df = test_df if sample_limit is None else test_df.head(sample_limit // 3).copy()

    logger.info(
        "Initializing Heatwave Classification Pipeline (Train: %d, Test: %d)...",
        len(tr_df),
        len(te_df),
    )

    # 1. Target Binarization and Class Distribution Analysis
    thresholds_meta = compute_heatwave_thresholds(
        tr_df[target_col],
        absolute_threshold_c=threshold_c,
        percentile_threshold=90.0,
    )
    logger.info("Computed heatwave thresholds: %s", thresholds_meta)

    y_train_binary = binarize_heatwave_target(
        tr_df[target_col],
        absolute_threshold_c=threshold_c,
        percentile_threshold=90.0,
        reference_distribution=tr_df[target_col],
    )
    y_test_binary = binarize_heatwave_target(
        te_df[target_col],
        absolute_threshold_c=threshold_c,
        percentile_threshold=90.0,
        reference_distribution=tr_df[target_col],
    )

    dist_train = analyze_class_distribution(y_train_binary)
    dist_test = analyze_class_distribution(y_test_binary)
    logger.info(
        "Train distribution: %d Normal (%.1f%%), %d Heatwave (%.1f%%) [Imbalance: %.1f:1]",
        dist_train["normal_samples"],
        dist_train["normal_percentage"],
        dist_train["heatwave_samples"],
        dist_train["heatwave_percentage"],
        dist_train["imbalance_ratio"],
    )
    logger.info(
        "Test distribution: %d Normal (%.1f%%), %d Heatwave (%.1f%%)",
        dist_test["normal_samples"],
        dist_test["normal_percentage"],
        dist_test["heatwave_samples"],
        dist_test["heatwave_percentage"],
    )

    # 2. Feature Standardization using MeteorologicalScaler (Strictly on Train split)
    logger.info("Fitting StandardScaler on %d training samples...", len(tr_df))
    scaler = MeteorologicalScaler(scaler_type="standard", feature_cols=feature_cols)
    X_train_scaled = scaler.fit_transform(tr_df[feature_cols])
    X_test_scaled = scaler.transform(te_df[feature_cols])

    # Convert to contiguous float32 arrays
    X_tr_arr = np.asarray(X_train_scaled[feature_cols], dtype=np.float32)
    X_te_arr = np.asarray(X_test_scaled[feature_cols], dtype=np.float32)

    # 3. Build and Train Classifier Suite
    logger.info("Instantiating classifier suite with balanced class weighting...")
    suite = build_classifier_suite(
        bagging_estimator_counts=bagging_estimator_counts,
        random_state=42,
    )

    evaluation_results: Dict[str, Dict[str, Any]] = {}
    bagging_results: Dict[int, Dict[str, Any]] = {}

    for name, model in suite.items():
        logger.info("Training %s...", name)
        model.fit(X_tr_arr, y_train_binary)
        metrics = evaluate_classification_model(model, X_te_arr, y_test_binary, model_name=name)
        evaluation_results[name] = metrics
        logger.info(
            "%s -> Acc: %.3f | Rec (Class 1): %.3f | F1 (Class 1): %.3f | Balanced Acc: %.3f",
            name,
            metrics["accuracy"],
            metrics["heatwave_recall"],
            metrics["heatwave_f1"],
            metrics["balanced_accuracy"],
        )

        if name.startswith("BaggingClassifier_"):
            n_est = int(name.split("_")[1])
            bagging_results[n_est] = metrics

    # 4. Generate Visualizations
    cm_plot_path = figures_dir / "heatwave_confusion_matrices.png"
    logger.info("Rendering confusion matrix multi-panel figure to %s...", cm_plot_path)
    plot_confusion_matrices(evaluation_results, output_path=cm_plot_path)

    bagging_plot_path = figures_dir / "bagging_estimator_curves.png"
    logger.info("Rendering BaggingClassifier curves to %s...", bagging_plot_path)
    plot_bagging_estimator_curves(bagging_results, output_path=bagging_plot_path)

    # 5. Compile and Save Full Audit Report JSON
    summary_report = {
        "status": "SUCCESS",
        "target_variable": target_col,
        "heatwave_threshold_c": threshold_c,
        "threshold_metadata": thresholds_meta,
        "class_distributions": {
            "training_set": dist_train,
            "test_set": dist_test,
        },
        "feature_count": len(feature_cols),
        "feature_columns": feature_cols,
        "scaling_applied": "StandardScaler",
        "model_evaluations": evaluation_results,
        "artifact_paths": {
            "confusion_matrices_plot": str(cm_plot_path),
            "bagging_curves_plot": str(bagging_plot_path),
        },
        "best_models": {
            "highest_heatwave_recall": max(
                evaluation_results.values(), key=lambda x: x["heatwave_recall"]
            )["model_name"],
            "highest_heatwave_f1": max(
                evaluation_results.values(), key=lambda x: x["heatwave_f1"]
            )["model_name"],
            "highest_balanced_accuracy": max(
                evaluation_results.values(), key=lambda x: x["balanced_accuracy"]
            )["model_name"],
        },
    }

    report_json_path = artifacts_dir / "heatwave_classification_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
    logger.info("Saved classification report JSON to %s", report_json_path)

    return summary_report
