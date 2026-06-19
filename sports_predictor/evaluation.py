from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

from .config import REPORT_DIR, ensure_directories


def evaluate_predictions(y_true: np.ndarray | pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = float(mean_absolute_percentage_error(y_true, np.maximum(y_pred, 1e-9)))
    r2 = float(r2_score(y_true, y_pred))
    avg = float(np.mean(y_true))
    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "r2": r2,
        "mae_pct_of_average": float(mae / avg) if avg else 0.0,
    }


def prediction_interval_coverage(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    return float(np.mean((y_true >= lower) & (y_true <= upper)))


def time_series_cross_validate(model_factory, X: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> dict[str, float]:
    splitter = TimeSeriesSplit(n_splits=n_splits)
    scores = []
    for train_idx, test_idx in splitter.split(X):
        model = model_factory()
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(X.iloc[test_idx])
        scores.append(r2_score(y.iloc[test_idx], pred))
    return {"cv_r2_mean": float(np.mean(scores)), "cv_r2_std": float(np.std(scores))}


def write_report(report: dict, path: Path | None = None) -> Path:
    ensure_directories()
    path = path or REPORT_DIR / "validation_results.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
