from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.security.input_guard import PredictionRequest
from app.security.output_filter import PredictionResponse
from app.config import SPORTS
from app.services.prediction_service import predict_performance
from app.models import train_all_models
from app.services.realtime_cricket import (
    parse_cricbuzz_squad,
    predict_real_player,
    predict_real_player_squad,
)
import os

# Load env variables from .env manually to ensure compatibility without python-dotenv
for env_dir in [os.getcwd(), os.path.dirname(os.path.dirname(__file__))]:
    _env_path = os.path.join(env_dir, ".env")
    if os.path.exists(_env_path):
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()


app = FastAPI(
    title="Player Performance API",
    description="Predicts player performance across cricket, football, and NBA.",
    version="0.1.0",
)

# CORS middleware config to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to React URL e.g. http://localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Predictions Router
predictions_router = APIRouter(prefix="/v1", tags=["predictions"])


@predictions_router.post("/predict", response_model=PredictionResponse)
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
        venue_id=request.venue_id,
        is_day_night=request.is_day_night,
    )
    return result.to_dict()


@predictions_router.post("/predict-batch", response_model=list[PredictionResponse])
def predict_batch(requests: list[PredictionRequest]) -> list[dict]:
    return [predict(request) for request in requests]


# Models Router
models_router = APIRouter(prefix="/v1/models", tags=["models"])


@models_router.post("/train")
def train() -> dict[str, dict[str, float]]:
    trained = train_all_models()
    return {sport: bundle.metrics for sport, bundle in trained.items()}


# Health & Root Router
health_router = APIRouter(tags=["health"])


@health_router.get("/")
def root() -> dict[str, str]:
    return {
        "status": "online",
        "message": "Black Bolt AI API is live",
        "docs": "/docs",
        "health": "/health"
    }


@health_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Admin Router
admin_router = APIRouter(prefix="/v1/admin", tags=["admin"])


@admin_router.get("/status")
def status() -> dict[str, str]:
    return {"status": "ready"}


# Cricket Router
cricket_router = APIRouter(prefix="/v1/cricket", tags=["cricket"])

class CricketManualRequest(BaseModel):
    player_name: str
    opposition: str
    venue: str
    match_format: str = "T20"
    model_name: str = "gemini-3.6-flash"
    match_date: Optional[str] = None
    is_day_night: Optional[bool] = None

class CricketSquadRequest(BaseModel):
    player_name: str
    player_role: str
    player_profile_url: str
    opposition_team: str
    opponent_squad: List[Dict[str, Any]]
    match_format: str = "T20"
    venue: str
    model_name: str = "gemini-3.6-flash"
    match_date: Optional[str] = None
    is_day_night: Optional[bool] = None

@cricket_router.get("/squad")
def get_squad(url: str) -> dict:
    result = parse_cricbuzz_squad(url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@cricket_router.post("/predict-manual")
def predict_cricket_manual(req: CricketManualRequest) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key and not gemini_key:
        raise HTTPException(
            status_code=400,
            detail="Neither OPENROUTER_API_KEY nor GEMINI_API_KEY is configured in backend environment."
        )
    
    steps = []
    def status_callback(msg: str):
        steps.append(msg)
        
    try:
        res = predict_real_player(
            player_name=req.player_name,
            opposition=req.opposition,
            venue=req.venue,
            api_key=api_key,
            match_format=req.match_format,
            model_name=req.model_name,
            status_callback=status_callback,
            match_date=req.match_date,
            is_day_night=req.is_day_night
        )
        res["steps"] = steps
        # Return rate-limit / quota errors with appropriate HTTP status
        if res.get("error_type") in ("rate_limit", "quota_exceeded", "payment_required", "auth_error"):
            status_map = {
                "rate_limit": 429,
                "quota_exceeded": 402,
                "payment_required": 402,
                "auth_error": 403,
            }
            raise HTTPException(
                status_code=status_map.get(res["error_type"], 429),
                detail={
                    "error_type": res["error_type"],
                    "message": res["error"],
                    "suggestions": [
                        "Switch to a different model (especially a free one marked with \u2705)",
                        "Wait and try again later \u2014 free-tier limits reset every 24 hours",
                        "Replace your API key with a new one from https://openrouter.ai/keys",
                        "Upgrade to a paid API key for unlimited usage",
                    ],
                },
            )
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cricket_router.post("/predict-squad")
def predict_cricket_squad(req: CricketSquadRequest) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key and not gemini_key:
        raise HTTPException(
            status_code=400,
            detail="Neither OPENROUTER_API_KEY nor GEMINI_API_KEY is configured in backend environment."
        )
    
    steps = []
    def status_callback(msg: str):
        steps.append(msg)
        
    try:
        res = predict_real_player_squad(
            player_name=req.player_name,
            player_role=req.player_role,
            player_profile_url=req.player_profile_url,
            opposition_team=req.opposition_team,
            opponent_squad=req.opponent_squad,
            match_format=req.match_format,
            venue=req.venue,
            api_key=api_key,
            model_name=req.model_name,
            status_callback=status_callback,
            match_date=req.match_date,
            is_day_night=req.is_day_night
        )
        res["steps"] = steps
        # Return rate-limit / quota errors with appropriate HTTP status
        if res.get("error_type") in ("rate_limit", "quota_exceeded", "payment_required", "auth_error"):
            status_map = {
                "rate_limit": 429,
                "quota_exceeded": 402,
                "payment_required": 402,
                "auth_error": 403,
            }
            raise HTTPException(
                status_code=status_map.get(res["error_type"], 429),
                detail={
                    "error_type": res["error_type"],
                    "message": res["error"],
                    "suggestions": [
                        "Switch to a different model (especially a free one marked with \u2705)",
                        "Wait and try again later \u2014 free-tier limits reset every 24 hours",
                        "Replace your API key with a new one from https://openrouter.ai/keys",
                        "Upgrade to a paid API key for unlimited usage",
                    ],
                },
            )
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Include Routers
app.include_router(health_router)
app.include_router(predictions_router)
app.include_router(models_router)
app.include_router(admin_router)
app.include_router(cricket_router)


# Legacy Endpoints
@app.post("/predict")
def legacy_predict(request: PredictionRequest) -> dict:
    return predict(request)


@app.post("/train")
def legacy_train() -> dict[str, dict[str, float]]:
    return train()

