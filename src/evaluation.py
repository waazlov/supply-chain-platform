"""Model evaluation helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(y_true: pd.Series, y_prob: np.ndarray, threshold: float = 0.5) -> dict[str, Any]:
    """Compute classification metrics for a probability forecast."""
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "threshold": threshold,
        "confusion_matrix": cm.tolist(),
    }


def regression_metrics(actual: pd.Series, forecast: pd.Series) -> dict[str, float]:
    """Compute common forecast accuracy metrics."""
    actual = actual.astype(float)
    forecast = forecast.astype(float)
    error = forecast - actual
    denom = actual.abs().replace(0, np.nan)
    return {
        "mae": float(error.abs().mean()),
        "rmse": float(np.sqrt((error**2).mean())),
        "wmape": float(error.abs().sum() / actual.abs().sum()) if actual.abs().sum() else float("nan"),
        "mape": float((error.abs() / denom).mean()),
        "forecast_bias": float(error.sum() / actual.sum()) if actual.sum() else float("nan"),
    }

