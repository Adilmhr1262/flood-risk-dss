"""CLI entrypoint for training the flood risk prediction models.

Usage:
    python -m ml.train --data db --model rf --out ../ml-models/models/rf-v1
    python -m ml.train --data ml/sample_training_data.csv --model mlp --out ../ml-models/models/mlp-v1

``--data`` accepts ``db`` (live PostgreSQL via DATABASE_URL) or a CSV path.
``--model`` chooses rf (Random Forest), xgb (XGBoost) or mlp (multi-layer
perceptron).
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.pipeline import run_training  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train flood risk prediction models.")
    parser.add_argument(
        "--data",
        required=True,
        help="'db' for the live database, or a path to a training CSV file.",
    )
    parser.add_argument(
        "--model",
        default="rf",
        choices=["rf", "xgb", "mlp"],
        help="Which model to train.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for model artifacts (model.joblib, metrics.json, ...).",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="Database URL (defaults to DATABASE_URL env var when --data=db).",
    )
    parser.add_argument(
        "--features",
        default=None,
        help="Comma-separated base feature columns to train on "
        "(default: the nine base features).",
    )
    args = parser.parse_args()

    database_url = args.db_url or os.environ.get("DATABASE_URL")
    feature_columns = (
        [c.strip() for c in args.features.split(",")] if args.features else None
    )
    result = run_training(
        source=args.data,
        model_name=args.model,
        out_dir=args.out,
        database_url=database_url,
        feature_columns=feature_columns,
    )
    m = result["metrics"]
    print(f"Trained '{args.model}' on {result['n_rows']} rows -> {result['model_dir']}")
    print(f"{'accuracy':<10}{'precision':<11}{'recall':<9}{'f1':<8}{'roc_auc':<10}{'cv_f1':<10}")
    print("-" * 68)
    print(
        f"{m['accuracy']:<10.4f}{m['precision']:<11.4f}{m['recall']:<9.4f}"
        f"{m['f1']:<8.4f}{m['roc_auc']:<10.4f}{m['cv_f1_mean']:<10.4f}"
    )
    if result["feature_importance"]:
        print("\nTop features:")
        for name, imp in list(result["feature_importance"].items())[:5]:
            print(f"  {name:<22}{imp:.4f}")


if __name__ == "__main__":
    main()
