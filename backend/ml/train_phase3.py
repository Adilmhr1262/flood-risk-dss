"""Phase 3 research training: Random Forest, XGBoost and MLP on the Sindh
2010-2024 district-year dataset.

Trains the three models with identical data, split seed and CV protocol,
persists each under ml-models/models/<name>-v1/, renders confusion-matrix
PNGs, and prints a comparison table.

Usage:
    cd ~/workspace/flood-risk-dss
    backend/.venv/bin/python backend/ml/train_phase3.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from ml.pipeline import RESEARCH_FEATURES, run_training  # noqa: E402

DATASET = str(BACKEND.parent / "datasets" / "processed" / "sindh_training_2010_2024.csv")
IMG_DIR = BACKEND.parent / "docs" / "img"

# model key -> (train.py model name, registry entry name, description)
MODELS = {
    "randomforest": (
        "rf",
        "randomforest-v1",
        "Random Forest classifier (300 trees, class_weight=balanced) trained on "
        "the Sindh 2010-2024 district-year research dataset: 180 rows, 43 flood "
        "years, ERA5 monsoon weather + static district attributes.",
    ),
    "xgboost": (
        "xgb",
        "xgboost-v1",
        "XGBoost gradient-boosted trees (300 rounds, max_depth=6, lr=0.05) trained "
        "on the Sindh 2010-2024 district-year research dataset.",
    ),
    "mlp": (
        "mlp",
        "mlp-v1",
        "Multi-layer perceptron (64-32 hidden units, max_iter=800) trained on the "
        "Sindh 2010-2024 district-year research dataset. Feature importance via "
        "permutation importance (10 repeats) on the held-out test set.",
    ),
}

HYPERPARAMETERS = {
    "rf": {
        "n_estimators": 300,
        "max_depth": None,
        "min_samples_split": 2,
        "class_weight": "balanced",
    },
    "xgb": {
        "n_estimators": 300,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "eval_metric": "logloss",
    },
    "mlp": {"hidden_layer_sizes": [64, 32], "max_iter": 800},
}

TRAINING_CONFIG = {
    "test_size": 0.2,
    "stratified": True,
    "random_state": 42,
    "cv": "StratifiedKFold(n_splits=5, shuffle=True, random_state=42)",
    "cv_scoring": "f1",
    "scaler": "StandardScaler",
}


def plot_confusion_matrix(cm: list[list[int]], title: str, path: Path) -> None:
    """Render a labelled confusion-matrix heatmap to PNG."""
    labels = ["no flood (0)", "flood (1)"]
    arr = np.array(cm)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    im = ax.imshow(arr, cmap="Blues")
    ax.set_xticks([0, 1], labels)
    ax.set_yticks([0, 1], labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(arr[i, j]), ha="center", va="center", fontsize=14)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for key, (short, registry_name, description) in MODELS.items():
        out_dir = BACKEND.parent / "ml-models" / "models" / registry_name
        print(f"\n=== training {registry_name} ({short}) ===", flush=True)
        result = run_training(
            source=DATASET,
            model_name=short,
            out_dir=out_dir,
            feature_columns=RESEARCH_FEATURES,
        )
        m = result["metrics"]
        cm_path = IMG_DIR / f"confusion_matrix_{key}.png"
        plot_confusion_matrix(m["confusion_matrix"], f"Confusion matrix — {registry_name}", cm_path)
        import shutil

        shutil.copy(cm_path, out_dir / "confusion_matrix.png")
        print(f"confusion matrix -> {cm_path}")
        results[key] = {
            "registry_name": registry_name,
            "description": description,
            "hyperparameters": HYPERPARAMETERS[short],
            "training_config": TRAINING_CONFIG,
            "metrics": m,
            "feature_importance": result["feature_importance"],
        }

    print("\n=== model comparison (held-out test set, 36 rows) ===")
    header = f"{'model':<14}{'acc':<8}{'prec':<8}{'rec':<8}{'f1':<8}{'roc_auc':<9}{'cv_f1':<12}"
    print(header)
    print("-" * len(header))
    for key, r in results.items():
        m = r["metrics"]
        print(
            f"{r['registry_name']:<14}{m['accuracy']:<8.4f}{m['precision']:<8.4f}"
            f"{m['recall']:<8.4f}{m['f1']:<8.4f}{m['roc_auc']:<9.4f}"
            f"{m['cv_f1_mean']:.4f}±{m['cv_f1_std']:.4f}"
        )

    summary_path = BACKEND / "ml" / "models" / "phase3_summary.json"
    summary_path.write_text(json.dumps(results, indent=2))
    print(f"\nsummary -> {summary_path}")


if __name__ == "__main__":
    main()
