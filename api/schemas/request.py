from datetime import date

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    player_id: int = Field(..., ge=1)
    sport: str = Field(..., examples=["cricket", "football", "nba"])
    match_date: date
    opposition: str = "Team 1"
    home_away: str = Field("home", pattern="^(home|away)$")
    opposition_strength: float = Field(0.5, ge=0.0, le=1.0)
    injury_risk: float = Field(0.05, ge=0.0, le=1.0)
    days_rest: int = Field(4, ge=0, le=30)
