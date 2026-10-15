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

SPORT_CONFIGS = {
    "cricket": {
        "metrics_to_predict": ["runs", "wickets", "strike_rate", "dot_ball_pct", "boundary_count"],
        "feature_count": 85,
        "lookback_window": 20,
    },
    "football": {
        "metrics_to_predict": ["goals", "assists", "shots_on_target", "pass_completion_pct", "xg", "xa"],
        "feature_count": 90,
        "lookback_window": 10,
    },
    "nba": {
        "metrics_to_predict": ["points", "rebounds", "assists", "three_pointers", "blocks", "steals"],
        "feature_count": 75,
        "lookback_window": 10,
    },
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
    # Phase 3: environment features
    "day_temp_c",
    "night_temp_c",
    "humidity_pct",
    "wind_speed_kmh",
    "dew_factor",
    "is_day_night",
    "pitch_batting_friendliness",
    "venue_avg_score",
    "straight_boundary_m",
    "square_boundary_m",
]

DEFAULT_VENUE_ID = "unknown_venue"
DEFAULT_IS_DAY_NIGHT = 0


def ensure_directories() -> None:
    for path in (DATA_DIR, MODEL_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
