from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"
REPORT_DIR = ROOT_DIR / "reports"

SPORTS = ("cricket", "football", "nba")

TARGET_BY_SPORT = {
    "cricket": "performance_metric",
    "football": "performance_metric",
    "nba": "performance_metric",
}

DEFAULT_FEATURE_COLUMNS = [
    "age",
    "is_home",
    "opposition_strength",
    "days_rest",
    "injury_risk",
    "minutes_or_overs",
    "usage_or_role",
    "career_avg",
    "career_std",
    "season_avg",
    "vs_opposition_avg",
    "rolling_avg_5",
    "rolling_std_5",
    "ewma_5",
    "rolling_avg_10",
    "rolling_std_10",
    "ewma_10",
    "lag_1",
    "lag_2",
    "lag_3",
    "momentum",
    "acceleration",
]


def ensure_directories() -> None:
    for path in (DATA_DIR, MODEL_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
