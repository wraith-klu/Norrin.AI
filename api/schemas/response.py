from pydantic import BaseModel


class PredictionResponse(BaseModel):
    player_id: int
    sport: str
    predicted_performance: float
    confidence_interval: list[float]
    confidence_level: str
    risk_level: str
