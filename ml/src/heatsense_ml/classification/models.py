"""Classifier model factories, evaluation metrics, and benchmarking suites."""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import BaggingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

logger = logging.getLogger("heatsense_ml.classification.models")


def build_classifier_suite(
    random_state: int = 42,
    bagging_estimator_counts: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Construct classifier suite incorporating balanced class weighting.

    Args:
        random_state: Random seed for reproducible initialization.
        bagging_estimator_counts: Estimator counts to evaluate for BaggingClassifier.
            Defaults to [5, 10, 50, 100].

    Returns:
        Dictionary mapping model names to un-fitted scikit-learn estimator instances.
    """
    if bagging_estimator_counts is None:
        bagging_estimator_counts = [5, 10, 50, 100]

    suite: Dict[str, Any] = {
        # 1. Linear classification baseline with balanced penalty
        "LogisticRegression": LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            solver="lbfgs",
            random_state=random_state,
        ),
        # 2. Non-parametric distance-based classifier
        "KNNClassifier": KNeighborsClassifier(
            n_neighbors=5,
            weights="distance",
        ),
        # 3. Probabilistic Bayesian classifier
        "GaussianNaiveBayes": GaussianNB(),
        # 4. Single Decision Tree with balanced class weights
        "DecisionTreeClassifier": DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=8,
            min_samples_split=20,
            random_state=random_state,
        ),
        # 5. Random Forest ensemble with balanced bootstrap trees
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            n_jobs=-1,
            random_state=random_state,
        ),
    }

    # 6. BaggingClassifier family with varying base estimator counts
    for n_est in bagging_estimator_counts:
        base_tree = DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=8,
            random_state=random_state,
        )
        suite[f"BaggingClassifier_{n_est}"] = BaggingClassifier(
            estimator=base_tree,
            n_estimators=n_est,
            max_samples=0.8,
            bootstrap=True,
            n_jobs=-1,
            random_state=random_state,
        )

    return suite


def evaluate_classification_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_name: str = "Classifier",
) -> Dict[str, Any]:
    """Evaluate classifier performance focusing on rare-event heatwave detection.

    Args:
        model: Fitted scikit-learn classifier.
        X_test: Test feature matrix.
        y_test: Ground-truth binary test labels (0=Normal, 1=Heatwave).
        model_name: Identifier name for reporting.

    Returns:
        Structured evaluation metrics including minority-class precision, recall,
        f1-score, and confusion matrix components.
    """
    y_pred = model.predict(X_test)
    y_test_arr = np.asarray(y_test, dtype=np.int32)

    acc = float(accuracy_score(y_test_arr, y_pred))

    # Minority class (1 = Heatwave Warning) metrics
    prec_heatwave = float(precision_score(y_test_arr, y_pred, pos_label=1, zero_division=0))
    rec_heatwave = float(recall_score(y_test_arr, y_pred, pos_label=1, zero_division=0))
    f1_heatwave = float(f1_score(y_test_arr, y_pred, pos_label=1, zero_division=0))

    # Macro & weighted averages
    f1_macro = float(f1_score(y_test_arr, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_test_arr, y_pred, average="weighted", zero_division=0))

    # Confusion matrix
    cm = confusion_matrix(y_test_arr, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # Derived rates
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    balanced_acc = float((rec_heatwave + specificity) / 2.0)
    false_alarm_rate = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    return {
        "model_name": model_name,
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(balanced_acc, 4),
        "heatwave_precision": round(prec_heatwave, 4),
        "heatwave_recall": round(rec_heatwave, 4),
        "heatwave_f1": round(f1_heatwave, 4),
        "macro_f1": round(f1_macro, 4),
        "weighted_f1": round(f1_weighted, 4),
        "specificity": round(specificity, 4),
        "false_alarm_rate": round(false_alarm_rate, 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
            "raw_matrix": cm.tolist(),
        },
    }
