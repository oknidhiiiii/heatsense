"""Visualization utilities for classification confusion matrices and ensemble curves."""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")  # Headless non-interactive rendering backend
import matplotlib.pyplot as plt
import numpy as np


def plot_confusion_matrices(
    evaluation_results: Dict[str, Dict[str, Any]],
    output_path: Path,
    title: str = "Heatwave Hazard Warning: Confusion Matrix Comparison",
) -> Path:
    """Generate multi-panel figure displaying confusion matrices for all evaluated classifiers.

    Args:
        evaluation_results: Dictionary mapping model names to their evaluation dicts.
        output_path: Destination PNG image path.
        title: Overall super-title for the figure.

    Returns:
        output_path: Path to saved figure image.
    """
    model_names = list(evaluation_results.keys())
    n_models = len(model_names)

    cols = min(4, n_models)
    rows = math.ceil(n_models / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.2, rows * 3.8), dpi=150)
    if n_models == 1:
        axes = np.array([axes])
    axes_flat = axes.flatten() if hasattr(axes, "flatten") else [axes]

    class_names = ["Normal (0)", "Heatwave (1)"]

    for idx, name in enumerate(model_names):
        ax = axes_flat[idx]
        res = evaluation_results[name]
        cm = np.array(res["confusion_matrix"]["raw_matrix"])

        # Display matrix with heat colormap
        cax = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)

        # Annotations
        total = np.sum(cm)
        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                val = cm[i, j]
                pct = (val / total) * 100.0 if total > 0 else 0.0
                ax.text(
                    j,
                    i,
                    f"{val:,}\n({pct:.1f}%)",
                    ha="center",
                    va="center",
                    color="white" if val > thresh else "black",
                    fontsize=8.5,
                    fontweight="bold",
                )

        ax.set_title(
            f"{name}\nRec: {res['heatwave_recall']:.2f} | F1: {res['heatwave_f1']:.2f} | Acc: {res['accuracy']:.2f}",
            fontsize=9,
            fontweight="bold",
            pad=8,
        )
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(class_names, fontsize=8)
        ax.set_yticklabels(class_names, fontsize=8)
        ax.set_xlabel("Predicted Label", fontsize=8, labelpad=4)
        ax.set_ylabel("True Label", fontsize=8, labelpad=4)

    # Hide any unused subplots
    for idx in range(n_models, len(axes_flat)):
        axes_flat[idx].axis("off")

    fig.suptitle(title, fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_bagging_estimator_curves(
    bagging_results: Dict[int, Dict[str, Any]],
    output_path: Path,
    title: str = "BaggingClassifier: Estimator Count vs Performance Metrics",
) -> Path:
    """Plot performance curves across varying number of bootstrap estimators.

    Args:
        bagging_results: Dictionary mapping estimator count (int) to evaluation dict.
        output_path: Destination PNG image path.
        title: Title for the plot.

    Returns:
        output_path: Path to saved figure image.
    """
    estimator_counts = sorted(bagging_results.keys())
    accuracies = [bagging_results[n]["accuracy"] for n in estimator_counts]
    recalls = [bagging_results[n]["heatwave_recall"] for n in estimator_counts]
    f1_scores = [bagging_results[n]["heatwave_f1"] for n in estimator_counts]

    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=150)

    ax.plot(
        estimator_counts,
        accuracies,
        marker="o",
        linewidth=2,
        color="#0284c7",
        label="Accuracy",
    )
    ax.plot(
        estimator_counts,
        recalls,
        marker="s",
        linewidth=2,
        color="#dc2626",
        label="Heatwave Recall (Class 1)",
    )
    ax.plot(
        estimator_counts,
        f1_scores,
        marker="^",
        linewidth=2,
        color="#16a34a",
        label="Heatwave F1-Score (Class 1)",
    )

    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel("Number of Estimators in Bagging Ensemble", fontsize=9, labelpad=6)
    ax.set_ylabel("Metric Value (0.0 to 1.0)", fontsize=9, labelpad=6)
    ax.set_xticks(estimator_counts)
    ax.set_ylim([0.0, 1.05])
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower right", frameon=True, fontsize=8.5)

    for n in estimator_counts:
        f1_val = bagging_results[n]["heatwave_f1"]
        ax.annotate(
            f"{f1_val:.3f}",
            (n, f1_val),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
            fontsize=8,
            fontweight="bold",
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path
