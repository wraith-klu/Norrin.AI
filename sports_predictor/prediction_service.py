from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .data_collection import clean_and_validate, load_or_create_dataset
from .feature_engineering import build_request_features
from .models import load_model


@dataclass
class PredictionResult:
    player_id: int
    sport: str
    predicted_performance: float
    confidence_interval: tuple[float, float]
    confidence_level: str
    risk_level: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["confidence_interval"] = list(self.confidence_interval)
        return data


def predict_performance(
    player_id: int,
    sport: str,
    match_date: str,
    opposition: str,
    home_away: str,
    opposition_strength: float = 0.5,
    injury_risk: float = 0.05,
    days_rest: int = 4,
) -> PredictionResult:
    sport = sport.lower()
    df = clean_and_validate(load_or_create_dataset())
    history = df[(df["sport"].eq(sport)) & (df["player_id"].eq(player_id))].sort_values("match_date")
    if history.empty:
        sport_pool = df[df["sport"].eq(sport)].sort_values("match_date")
        history = sport_pool.groupby("player_id").head(8).copy()
        history["player_id"] = player_id
        history["player_name"] = f"New {sport.title()} Player"

    request_values = {
        "player_id": player_id,
        "sport": sport,
        "match_date": pd.to_datetime(match_date),
        "opposition": opposition,
        "is_home": 1 if home_away.lower() == "home" else 0,
        "opposition_strength": opposition_strength,
        "injury_risk": injury_risk,
        "days_rest": days_rest,
    }
    X = build_request_features(history, request_values)
    model_bundle = load_model(sport)
    prediction = float(model_bundle.model.predict(X)[0])
    radius = getattr(model_bundle, "interval_radius", max(abs(prediction) * 0.15, 1.0))
    lower = min(float(model_bundle.lower_model.predict(X)[0]), prediction - radius)
    upper = max(float(model_bundle.upper_model.predict(X)[0]), prediction + radius)
    risk_level = "High" if injury_risk > 0.25 or (upper - lower) > max(prediction * 0.55, 5.0) else "Low"
    return PredictionResult(
        player_id=player_id,
        sport=sport,
        predicted_performance=prediction,
        confidence_interval=(min(lower, upper), max(lower, upper)),
        confidence_level="80%",
        risk_level=risk_level,
    )
