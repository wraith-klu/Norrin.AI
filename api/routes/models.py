from fastapi import APIRouter

from sports_predictor.models import train_all_models

router = APIRouter(prefix="/v1/models", tags=["models"])


@router.post("/train")
def train() -> dict[str, dict[str, float]]:
    trained = train_all_models()
    return {sport: bundle.metrics for sport, bundle in trained.items()}
