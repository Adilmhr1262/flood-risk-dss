"""Model evaluation for the flood risk prediction models.

Reports the standard classification metrics used by this research:
accuracy, precision, recall, F1 score, ROC-AUC, plus the confusion matrix
and a text classification report.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Compute classification metrics on the held-out test set.

    Returns:
        dict with accuracy, precision, recall, f1, roc_auc (rounded to 4
        decimals) and confusion_matrix as [[tn, fp], [fn, tp]].
    """
    y_pred = model.predict(X_test)
    metrics: dict = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
    }
    try:
        proba = model.predict_proba(X_test)
        if proba.shape[1] == 2:
            metrics["roc_auc"] = roc_auc_score(y_test, proba[:, 1])
        else:  # single-class edge case
            metrics["roc_auc"] = float("nan")
    except Exception:
        metrics["roc_auc"] = float("nan")
    metrics["confusion_matrix"] = np.asarray(
        confusion_matrix(y_test, y_pred, labels=[0, 1])
    ).tolist()
    rounded = {k: (round(float(v), 4) if not isinstance(v, list) else v) for k, v in metrics.items()}
    return rounded


def classification_report_text(model, X_test: pd.DataFrame, y_test: pd.Series) -> str:
    """Sklearn classification report as plain text."""
    return classification_report(y_test, model.predict(X_test), digits=4, zero_division=0)
