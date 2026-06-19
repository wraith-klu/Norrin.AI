from fastapi import APIRouter, HTTPException

from api.schemas.request import PredictionRequest
from api.schemas.response import PredictionResponse
from sports_predictor.config import SPORTS
from sports_predictor.prediction_service import predict_performance

router = APIRouter(prefix="/v1", tags=["predictions"])


@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> dict:
    sport = request.sport.lower()
    if sport not in SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {request.sport}")
    result = predict_performance(
        player_id=request.player_id,
        sport=sport,
        match_date=request.match_date.isoformat(),
        opposition=request.opposition,
        home_away=request.home_away,
        opposition_strength=request.opposition_strength,
        injury_risk=request.injury_risk,
        days_rest=request.days_rest,
    )
    return result.to_dict()


@router.post("/predict-batch", response_model=list[PredictionResponse])
def predict_batch(requests: list[PredictionRequest]) -> list[dict]:
    return [predict(request) for request in requests]
