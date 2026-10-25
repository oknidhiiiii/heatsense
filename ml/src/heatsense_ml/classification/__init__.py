"""Heatwave hazard classification and early warning module.

Provides target binarization, class-imbalance handling, supervised alert classification,
and confusion matrix visualization.
"""

from heatsense_ml.classification.models import (
    build_classifier_suite,
    evaluate_classification_model,
)
from heatsense_ml.classification.pipeline import run_heatwave_classification_pipeline
from heatsense_ml.classification.target import (
    analyze_class_distribution,
    binarize_heatwave_target,
    compute_heatwave_thresholds,
)
from heatsense_ml.classification.visualizer import (
    plot_bagging_estimator_curves,
    plot_confusion_matrices,
)

__all__ = [
    "compute_heatwave_thresholds",
    "binarize_heatwave_target",
    "analyze_class_distribution",
    "build_classifier_suite",
    "evaluate_classification_model",
    "plot_confusion_matrices",
    "plot_bagging_estimator_curves",
    "run_heatwave_classification_pipeline",
]
