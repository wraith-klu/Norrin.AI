from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

from .config import DATA_DIR, SPORTS, ensure_directories


@dataclass(frozen=True)
class DataCollector:
    """Collects sports data from files/APIs; generates deterministic demo data offline."""

    sport: str
    seed: int = 42

    def fetch_player_stats(self, player_id: int, date_range: tuple[date, date]) -> pd.DataFrame:
        start, end = date_range
        dates = pd.date_range(start, end, freq="7D")
        rng = np.random.default_rng(self.seed + player_id)
        return pd.DataFrame(
            {
                "player_id": player_id,
                "match_date": dates,
                "raw_score": rng.normal(50, 12, len(dates)).clip(0),
            }
        )

    def fetch_match_context(self, match_id: int) -> dict[str, float | str | int]:
        rng = np.random.default_rng(self.seed + match_id)
        return {
            "match_id": match_id,
            "opposition_strength": float(rng.uniform(0.2, 1.0)),
            "is_home": int(rng.integers(0, 2)),
            "weather_index": float(rng.uniform(0.0, 1.0)),
        }

    def fetch_injuries(self, when: date) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "player_id": [1001, 2002, 3003],
                "sport": ["cricket", "football", "nba"],
                "injury_date": [when - timedelta(days=15)] * 3,
                "recovery_date": [when + timedelta(days=10)] * 3,
                "status": ["questionable", "out", "available"],
            }
        )


def generate_sample_data(rows_per_sport: int = 900, seed: int = 42, persist: bool = True) -> pd.DataFrame:
    """Create realistic, learnable sample data for all sports without external API keys."""

    ensure_directories()
    rng = np.random.default_rng(seed)
    frames: list[pd.DataFrame] = []
    start = pd.Timestamp("2023-01-01")

    sport_offsets = {"cricket": 18.0, "football": 3.5, "nba": 24.0}
    for sport in SPORTS:
        player_ids = np.arange(1, 31)
        dates = pd.date_range(start, periods=rows_per_sport // len(player_ids) + 1, freq="7D")
        records = []
        for player_id in player_ids:
            base_skill = rng.normal(sport_offsets[sport], sport_offsets[sport] * 0.18)
            age = int(rng.integers(19, 37))
            player_dates = dates[: rows_per_sport // len(player_ids)]
            trend = rng.normal(0.02, 0.03)
            for idx, match_date in enumerate(player_dates):
                opposition_strength = rng.uniform(0.15, 1.0)
                days_rest = int(rng.integers(1, 8))
                injury_risk = rng.beta(1.5, 8.0)
                is_home = int(rng.integers(0, 2))
                usage_or_role = rng.uniform(0.4, 1.0)
                minutes_or_overs = rng.uniform(12, 38) if sport != "cricket" else rng.uniform(2, 20)
                seasonal_wave = np.sin(idx / 4.0) * sport_offsets[sport] * 0.06
                noise = rng.normal(0, sport_offsets[sport] * 0.08)
                performance = (
                    base_skill
                    + trend * idx
                    + is_home * sport_offsets[sport] * 0.05
                    + usage_or_role * sport_offsets[sport] * 0.35
                    + days_rest * sport_offsets[sport] * 0.015
                    - opposition_strength * sport_offsets[sport] * 0.18
                    - injury_risk * sport_offsets[sport] * 0.45
                    + seasonal_wave
                    + noise
                )
                records.append(
                    {
                        "sport": sport,
                        "player_id": int(player_id),
                        "player_name": f"{sport.title()} Player {player_id:02d}",
                        "match_id": f"{sport[:3]}-{player_id}-{idx}",
                        "match_date": match_date,
                        "season": match_date.year,
                        "opposition": f"Team {int(rng.integers(1, 11))}",
                        "age": age,
                        "is_home": is_home,
                        "opposition_strength": opposition_strength,
                        "days_rest": days_rest,
                        "injury_risk": injury_risk,
                        "minutes_or_overs": minutes_or_overs,
                        "usage_or_role": usage_or_role,
                        "performance_metric": max(0.0, performance),
                    }
                )
        frames.append(pd.DataFrame(records))

    df = pd.concat(frames, ignore_index=True).sort_values(["sport", "player_id", "match_date"])
    if persist:
        output = DATA_DIR / "sample_player_stats.csv"
        df.to_csv(output, index=False)
    return df


def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["match_date"] = pd.to_datetime(cleaned["match_date"])
    numeric_cols = cleaned.select_dtypes(include=["number"]).columns
    cleaned[numeric_cols] = cleaned[numeric_cols].ffill().bfill()

    for sport, sport_df in cleaned.groupby("sport"):
        q1 = sport_df["performance_metric"].quantile(0.25)
        q3 = sport_df["performance_metric"].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = cleaned["sport"].eq(sport)
        cleaned.loc[mask, "is_outlier"] = ~cleaned.loc[mask, "performance_metric"].between(lower, upper)
        cleaned.loc[mask, "performance_metric"] = cleaned.loc[mask, "performance_metric"].clip(lower, upper)

    cleaned["is_outlier"] = cleaned["is_outlier"].astype(bool)
    return cleaned


def initialize_sqlite_database(db_path: Path | None = None) -> Path:
    ensure_directories()
    db_path = db_path or DATA_DIR / "sports_prediction.sqlite"
    schema = """
    CREATE TABLE IF NOT EXISTS player_matches (
        match_id TEXT PRIMARY KEY,
        player_id INTEGER,
        sport TEXT,
        match_date TEXT,
        opposition TEXT,
        performance_metric REAL
    );

    CREATE TABLE IF NOT EXISTS player_injuries (
        player_id INTEGER,
        sport TEXT,
        injury_date TEXT,
        recovery_date TEXT,
        status TEXT
    );
    """
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA journal_mode=MEMORY;")
            conn.execute("PRAGMA synchronous=OFF;")
            conn.executescript(schema)
    except sqlite3.OperationalError:
        schema_path = DATA_DIR / "schema.sql"
        schema_path.write_text(schema.strip() + "\n", encoding="utf-8")
        return schema_path
    return db_path


def load_or_create_dataset(path: Path | None = None) -> pd.DataFrame:
    path = path or DATA_DIR / "sample_player_stats.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["match_date"])
    return generate_sample_data()
