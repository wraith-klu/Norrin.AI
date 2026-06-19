from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, VotingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor

from .config import MODEL_DIR, SPORTS, ensure_directories
from .data_collection import clean_and_validate, load_or_create_dataset
from .evaluation import evaluate_predictions, prediction_interval_coverage, write_report
from .feature_engineering import get_model_matrix


class TorchLSTMRegressor:
    """Small PyTorch LSTM regressor with sklearn-style fit/predict."""

    def __init__(self, epochs: int = 20, learning_rate: float = 0.01, hidden_size: int = 32, seed: int = 42):
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.hidden_size = hidden_size
        self.seed = seed
        self.model_: torch.nn.Sequential | None = None
        self.x_mean_: np.ndarray | None = None
        self.x_std_: np.ndarray | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "TorchLSTMRegressor":
        torch.manual_seed(self.seed)
        x = X.to_numpy(dtype=np.float32)
        self.x_mean_ = x.mean(axis=0, keepdims=True)
        self.x_std_ = x.std(axis=0, keepdims=True) + 1e-6
        x = (x - self.x_mean_) / self.x_std_
        x_tensor = torch.tensor(x[:, None, :], dtype=torch.float32)
        y_tensor = torch.tensor(y.to_numpy(dtype=np.float32)[:, None], dtype=torch.float32)

        self.model_ = torch.nn.Sequential(
            torch.nn.LSTM(input_size=x.shape[1], hidden_size=self.hidden_size, batch_first=True),
        )
        head = torch.nn.Sequential(torch.nn.Linear(self.hidden_size, 16), torch.nn.ReLU(), torch.nn.Linear(16, 1))
        params = list(self.model_.parameters()) + list(head.parameters())
        optimizer = torch.optim.Adam(params, lr=self.learning_rate)
        loss_fn = torch.nn.MSELoss()
        for _ in range(self.epochs):
            optimizer.zero_grad()
            lstm_out, _ = self.model_[0](x_tensor)
            pred = head(lstm_out[:, -1, :])
            loss = loss_fn(pred, y_tensor)
            loss.backward()
            optimizer.step()
        self.head_ = head
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model_ is None or self.x_mean_ is None or self.x_std_ is None:
            raise RuntimeError("TorchLSTMRegressor must be fitted before prediction.")
        x = X.to_numpy(dtype=np.float32)
        x = (x - self.x_mean_) / self.x_std_
        with torch.no_grad():
            lstm_out, _ = self.model_[0](torch.tensor(x[:, None, :], dtype=torch.float32))
            pred = self.head_(lstm_out[:, -1, :]).numpy().ravel()
        return pred


def create_xgboost_like_model() -> GradientBoostingRegressor:
    return GradientBoostingRegressor(n_estimators=180, learning_rate=0.06, max_depth=3, random_state=42)


def create_ensemble_model() -> VotingRegressor:
    return VotingRegressor(
        estimators=[
            ("gradient_boosting", create_xgboost_like_model()),
            ("random_forest", RandomForestRegressor(n_estimators=120, random_state=42, n_jobs=1)),
            ("mlp", Pipeline([("scale", StandardScaler()), ("mlp", MLPRegressor(hidden_layer_sizes=(48, 24), max_iter=500, random_state=42))])),
        ]
    )


def create_interval_models() -> tuple[GradientBoostingRegressor, GradientBoostingRegressor]:
    lower = GradientBoostingRegressor(loss="quantile", alpha=0.1, random_state=42)
    upper = GradientBoostingRegressor(loss="quantile", alpha=0.9, random_state=42)
    return lower, upper


@dataclass
class TrainedSportModel:
    sport: str
    model: VotingRegressor
    lower_model: GradientBoostingRegressor
    upper_model: GradientBoostingRegressor
    feature_columns: list[str]
    metrics: dict[str, float]
    feature_importance: pd.DataFrame
    interval_radius: float


def train_sport_model(df: pd.DataFrame, sport: str) -> TrainedSportModel:
    X, y, _ = get_model_matrix(df, sport=sport)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = create_ensemble_model()
    model.fit(X_train, y_train)
    lower_model, upper_model = create_interval_models()
    lower_model.fit(X_train, y_train)
    upper_model.fit(X_train, y_train)

    pred = model.predict(X_test)
    residual_radius = float(np.quantile(np.abs(y_test.to_numpy() - pred), 0.8))
    lower = np.minimum(lower_model.predict(X_test), pred - residual_radius)
    upper = np.maximum(upper_model.predict(X_test), pred + residual_radius)
    metrics = evaluate_predictions(y_test, pred)
    metrics["interval_coverage_80"] = prediction_interval_coverage(y_test.to_numpy(), lower, upper)

    importance = permutation_importance(model, X_test, y_test, n_repeats=5, random_state=42)
    feature_importance = pd.DataFrame(
        {"feature": X.columns, "importance": importance["importances_mean"]}
    ).sort_values("importance", ascending=False)

    return TrainedSportModel(
        sport=sport,
        model=model,
        lower_model=lower_model,
        upper_model=upper_model,
        feature_columns=list(X.columns),
        metrics=metrics,
        feature_importance=feature_importance,
        interval_radius=residual_radius,
    )


def train_all_models() -> dict[str, TrainedSportModel]:
    ensure_directories()
    df = clean_and_validate(load_or_create_dataset())
    trained: dict[str, TrainedSportModel] = {}
    report = {}
    for sport in SPORTS:
        sport_model = train_sport_model(df, sport)
        trained[sport] = sport_model
        report[sport] = sport_model.metrics
        sport_dir = MODEL_DIR / sport
        sport_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(sport_model, sport_dir / "xgboost_model.pkl")
        joblib.dump(sport_model.model, sport_dir / "ensemble_model.pkl")
        joblib.dump(sport_model.feature_columns, sport_dir / "feature_names.pkl")
        sport_model.feature_importance.to_csv(sport_dir / "feature_importance.csv", index=False)
        (sport_dir / "metadata.json").write_text(
            __import__("json").dumps({"sport": sport, "metrics": sport_model.metrics}, indent=2),
            encoding="utf-8",
        )
        joblib.dump(sport_model, MODEL_DIR / f"{sport}_model.joblib")
        sport_model.feature_importance.to_csv(MODEL_DIR / f"{sport}_feature_importance.csv", index=False)
    write_report(report)
    return trained


def load_model(sport: str) -> TrainedSportModel:
    model_path = MODEL_DIR / sport / "xgboost_model.pkl"
    if not model_path.exists():
        model_path = MODEL_DIR / f"{sport}_model.joblib"
    if not model_path.exists():
        train_all_models()
        model_path = MODEL_DIR / sport / "xgboost_model.pkl"
    return joblib.load(model_path)
