"""Script to execute the Feature Scaling Pipeline and Heatwave Hazard Classification Module."""

import json
import logging
from pathlib import Path

import pandas as pd
from heatsense_ml.classification.pipeline import run_heatwave_classification_pipeline
from heatsense_ml.features.builder import build_feature_dataset
from heatsense_ml.features.scaling import compare_scaling_effects
from heatsense_ml.training.trainer import split_chronologically

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scaling_and_classification_script")


def main():
    logger.info("=== HeatSense ML Enhancement: Scaling & Classification Suites ===")
    weather_path = Path("data/processed/pilot_weather.parquet")
    if not weather_path.exists():
        raise FileNotFoundError(f"Missing weather dataset at {weather_path}")

    logger.info("Loading weather dataset and building causal feature matrix...")
    df_raw = pd.read_parquet(weather_path)

    # Use sample_stride=3 (182 grid cells across Western India, ~780k rows) for rapid, robust evaluation
    sample_stride = 3
    unique_cells = df_raw["grid_cell_id"].unique()[::sample_stride]
    df_sampled = df_raw[df_raw["grid_cell_id"].isin(unique_cells)].copy()

    features_df, feature_cols = build_feature_dataset(df_sampled, horizons=[24, 48])
    logger.info("Features ready: %d rows, %d feature columns", len(features_df), len(feature_cols))

    logger.info("Splitting chronologically into Train (70%), Val (15%), Test (15%)...")
    train_df, val_df, test_df, split_info = split_chronologically(features_df)
    logger.info(
        "Split: Train=%d (%s to %s), Test=%d (%s to %s)",
        len(train_df),
        split_info["train_start"][:10],
        split_info["train_end"][:10],
        len(test_df),
        split_info["test_start"][:10],
        split_info["test_end"][:10],
    )

    # Subsample across full temporal spans for well-conditioned regressions and bounded execution time
    tr_subset = train_df.iloc[::15].copy().reset_index(drop=True)
    te_subset = test_df.iloc[::8].copy().reset_index(drop=True)

    # =========================================================================
    # PART 1: FEATURE SCALING PIPELINE (Covers Practicals 1B, 2, 7)
    # =========================================================================
    logger.info("--- PART 1: FEATURE SCALING BENCHMARK ---")
    y_tr = tr_subset["target_24h"].values
    y_te = te_subset["target_24h"].values
    X_tr = tr_subset[feature_cols]
    X_te = te_subset[feature_cols]

    scaling_results = compare_scaling_effects(X_tr, y_tr, X_te, y_te)

    print("\n" + "=" * 78)
    print("FEATURE SCALING COMPARISON TABLE (Target: +24h Temperature in deg C)")
    print("=" * 78)
    print(f"{'Model':<20} | {'Scaling Regime':<18} | {'MAE (deg C)':<12} | {'RMSE (deg C)':<12} | {'R2 Score':<8}")
    print("-" * 78)
    for row in scaling_results["comparison_table"]:
        print(
            f"{row['model']:<20} | {row['scaling_technique']:<18} | "
            f"{row['mae_c']:<12.4f} | {row['rmse_c']:<12.4f} | {row['r2_score']:<8.4f}"
        )
    print("=" * 78)
    print("Key Insights:")
    for finding in scaling_results["key_findings"]:
        print(f"  * {finding}")
    print("=" * 78 + "\n")

    # Save scaling benchmark JSON
    artifacts_dir = Path("artifacts/classification")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    scaling_json_path = artifacts_dir / "feature_scaling_comparison.json"
    with open(scaling_json_path, "w", encoding="utf-8") as f:
        json.dump(scaling_results, f, indent=2)
    logger.info("Saved feature scaling comparison to %s", scaling_json_path)

    # =========================================================================
    # PART 2: HEATWAVE HAZARD CLASSIFICATION (Covers Practicals 1B, 3, 6A, 8)
    # =========================================================================
    logger.info("--- PART 2: HEATWAVE HAZARD CLASSIFICATION PIPELINE ---")
    classification_report = run_heatwave_classification_pipeline(
        train_df=tr_subset,
        test_df=te_subset,
        feature_cols=feature_cols,
        target_col="target_24h",
        threshold_c=40.0,
        artifacts_dir=artifacts_dir,
        bagging_estimator_counts=[5, 10, 50, 100],
    )

    print("\n" + "=" * 94)
    print("HEATWAVE HAZARD CLASSIFICATION BENCHMARK (Binary Target: T >= 40 deg C)")
    print("=" * 94)
    print(
        f"{'Classifier Architecture':<26} | {'Accuracy':<9} | {'Bal Acc':<9} | "
        f"{'Recall (1)':<11} | {'Prec (1)':<10} | {'F1 (1)':<8} | {'TN / FP / FN / TP':<16}"
    )
    print("-" * 94)
    for name, res in classification_report["model_evaluations"].items():
        cm = res["confusion_matrix"]
        cm_str = f"{cm['true_negatives']}/{cm['false_positives']}/{cm['false_negatives']}/{cm['true_positives']}"
        print(
            f"{name:<26} | {res['accuracy']:<9.4f} | {res['balanced_accuracy']:<9.4f} | "
            f"{res['heatwave_recall']:<11.4f} | {res['heatwave_precision']:<10.4f} | "
            f"{res['heatwave_f1']:<8.4f} | {cm_str:<16}"
        )
    print("=" * 94)
    print("Best Performing Models:")
    for metric, best_name in classification_report["best_models"].items():
        print(f"  * {metric.replace('_', ' ').title()}: {best_name}")
    print(f"  * Confusion Matrices Plot: {classification_report['artifact_paths']['confusion_matrices_plot']}")
    print(f"  * Bagging Curves Plot:     {classification_report['artifact_paths']['bagging_curves_plot']}")
    print("=" * 94 + "\n")

    logger.info("All pipeline stages executed successfully!")


if __name__ == "__main__":
    main()
