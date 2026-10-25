"""Target binarization and class distribution analysis for heatwave classification."""

from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd


def compute_heatwave_thresholds(
    y_train: Union[np.ndarray, pd.Series],
    absolute_threshold_c: float = 40.0,
    percentile_threshold: float = 90.0,
) -> Dict[str, float]:
    """Compute absolute and relative percentile heatwave thresholds on training data.

    Args:
        y_train: Array or Series of continuous historical temperatures.
        absolute_threshold_c: Standard IMD plain-region heatwave threshold (e.g. 40.0 deg C).
        percentile_threshold: Historical regional percentile for heatwave anomaly (e.g. 90.0).

    Returns:
        Dictionary with absolute, percentile-based, and effective operational thresholds.
    """
    arr = np.asarray(y_train, dtype=np.float64)
    pct_val = float(np.percentile(arr, percentile_threshold))

    return {
        "absolute_threshold_c": float(absolute_threshold_c),
        "percentile": float(percentile_threshold),
        "percentile_value_c": round(pct_val, 2),
        "min_temp_c": round(float(np.min(arr)), 2),
        "max_temp_c": round(float(np.max(arr)), 2),
        "mean_temp_c": round(float(np.mean(arr)), 2),
    }


def binarize_heatwave_target(
    y: Union[np.ndarray, pd.Series],
    absolute_threshold_c: float = 40.0,
    percentile_threshold: Optional[float] = 90.0,
    reference_distribution: Optional[Union[np.ndarray, pd.Series]] = None,
    threshold_c: Optional[float] = None,
) -> np.ndarray:
    """Convert continuous temperature array into binary Heatwave Warning indicator.

    Follows the criterion:
    1 = Heatwave where (T >= 40 deg C) OR (T >= 90th percentile); 0 = Normal.

    Args:
        y: Continuous temperature values to binarize.
        absolute_threshold_c: Absolute threshold defining heatwave (default: 40.0 deg C).
        percentile_threshold: Optional percentile threshold (default: 90.0).
        reference_distribution: Optional baseline distribution to compute percentile from
            (typically the training set, preventing test lookahead).
        threshold_c: Alias for absolute_threshold_c for backwards compatibility.

    Returns:
        Binary NumPy integer array: 1 = Heatwave Warning, 0 = Normal.
    """
    if threshold_c is not None:
        absolute_threshold_c = threshold_c
    arr = np.asarray(y, dtype=np.float64)
    condition = arr >= absolute_threshold_c

    if percentile_threshold is not None:
        ref = np.asarray(
            reference_distribution if reference_distribution is not None else arr,
            dtype=np.float64,
        )
        pct_val = float(np.percentile(ref, percentile_threshold))
        condition = condition | (arr >= pct_val)

    return condition.astype(np.int32)


def analyze_class_distribution(
    y_binary: Union[np.ndarray, pd.Series],
    class_labels: Optional[Dict[int, str]] = None,
) -> Dict[str, Any]:
    """Analyze class frequency and imbalance characteristics.

    Args:
        y_binary: Binary target array.
        class_labels: Human-readable mapping for classes (defaults to 0: Normal, 1: Heatwave).

    Returns:
        Dictionary detailing class counts, percentages, and imbalance ratio.
    """
    if class_labels is None:
        class_labels = {0: "Normal", 1: "Heatwave"}

    arr = np.asarray(y_binary, dtype=np.int32)
    total_samples = len(arr)
    unique_vals, counts = np.unique(arr, return_counts=True)
    count_map = dict(zip(unique_vals.tolist(), counts.tolist()))

    normal_count = int(count_map.get(0, 0))
    heatwave_count = int(count_map.get(1, 0))

    heatwave_ratio = float(heatwave_count / total_samples) if total_samples > 0 else 0.0
    normal_ratio = float(normal_count / total_samples) if total_samples > 0 else 0.0

    imbalance_ratio = float(normal_count / heatwave_count) if heatwave_count > 0 else float("inf")

    return {
        "total_samples": total_samples,
        "normal_samples": normal_count,
        "heatwave_samples": heatwave_count,
        "normal_percentage": round(normal_ratio * 100.0, 2),
        "heatwave_percentage": round(heatwave_ratio * 100.0, 2),
        "imbalance_ratio": round(imbalance_ratio, 2),
        "is_imbalanced": heatwave_ratio < 0.20,
        "class_labels": class_labels,
    }
