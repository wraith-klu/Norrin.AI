from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from app.config import DEFAULT_FEATURE_COLUMNS, DEFAULT_VENUE_ID, DEFAULT_IS_DAY_NIGHT
from app.services.weather_service import (
    dew_factor as compute_dew_factor,
    fetch_match_weather,
    get_venue,
    pitch_batting_friendliness_score,
)

logger = logging.getLogger(__name__)


def engineer_time_series_features(
    df: pd.DataFrame, window_sizes: list[int] | None = None
) -> pd.DataFrame:
    window_sizes = window_sizes or [5, 10, 20]
    engineered = df.sort_values(["sport", "player_id", "match_date"]).copy()
    grouped = engineered.groupby(["sport", "player_id"], group_keys=False)

    for window in window_sizes:
        shifted = grouped["performance_metric"].shift(1)
        engineered[f"rolling_avg_{window}"] = shifted.groupby(
            [engineered["sport"], engineered["player_id"]]
        ).transform(lambda s: s.rolling(window, min_periods=1).mean())
        engineered[f"rolling_std_{window}"] = shifted.groupby(
            [engineered["sport"], engineered["player_id"]]
        ).transform(lambda s: s.rolling(window, min_periods=2).std())
        engineered[f"ewma_{window}"] = shifted.groupby(
            [engineered["sport"], engineered["player_id"]]
        ).transform(lambda s: s.ewm(span=window, adjust=False, min_periods=1).mean())

    engineered["momentum"] = grouped["performance_metric"].diff()
    engineered["acceleration"] = grouped["performance_metric"].diff().groupby(
        [engineered["sport"], engineered["player_id"]]
    ).diff()
    return engineered


def add_lag_features(df: pd.DataFrame, lags: list[int] | None = None) -> pd.DataFrame:
    lags = lags or [1, 2, 3, 5, 10]
    engineered = df.sort_values(["sport", "player_id", "match_date"]).copy()
    grouped = engineered.groupby(["sport", "player_id"])
    for lag in lags:
        engineered[f"lag_{lag}"] = grouped["performance_metric"].shift(lag)
    return engineered


def add_context_features(player_df: pd.DataFrame) -> pd.DataFrame:
    engineered = player_df.copy()
    engineered["is_home"] = engineered["is_home"].astype(int)
    engineered["days_rest"] = engineered["days_rest"].clip(lower=0, upper=14)
    engineered["availability_score"] = 1.0 - engineered["injury_risk"].clip(0, 1)
    return engineered


def add_statistical_features(df: pd.DataFrame) -> pd.DataFrame:
    engineered = df.copy()
    grouped_player = engineered.groupby(["sport", "player_id"])["performance_metric"]
    engineered["career_avg"] = grouped_player.transform(lambda s: s.shift(1).expanding().mean())
    engineered["career_std"] = grouped_player.transform(lambda s: s.shift(1).expanding().std())
    engineered["season_avg"] = engineered.groupby(["sport", "player_id", "season"])[
        "performance_metric"
    ].transform(lambda s: s.shift(1).expanding().mean())
    engineered["vs_opposition_avg"] = engineered.groupby(["sport", "player_id", "opposition"])[
        "performance_metric"
    ].transform(lambda s: s.shift(1).expanding().mean())
    return engineered


def add_environment_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds venue, weather, and dew-factor columns.

    Defensive: works even if 'venue_id', 'match_date', or 'is_day_night'
    are missing from *df*.  Calls fetch_match_weather() once per unique
    (venue_id, match_date) pair, not once per row.
    """
    engineered = df.copy()

    # (a) Ensure venue_id column exists
    if "venue_id" not in engineered.columns:
        engineered["venue_id"] = DEFAULT_VENUE_ID

    # --- Venue lookup (once per unique venue_id) --------------------------
    unique_venues = engineered["venue_id"].unique()
    venue_lookup: dict[str, dict | None] = {}
    for vid in unique_venues:
        venue_lookup[vid] = get_venue(str(vid))

    # (b) Derive is_day_night if missing
    if "is_day_night" not in engineered.columns:
        engineered["is_day_night"] = engineered["venue_id"].map(
            lambda vid: (
                venue_lookup.get(vid, {}) or {}
            ).get("is_day_night_ground", DEFAULT_IS_DAY_NIGHT)
        ).astype(int)

    # (c) Merge venue metadata columns
    venue_rows = []
    for vid, info in venue_lookup.items():
        if info is not None:
            venue_rows.append({
                "venue_id": vid,
                "venue_name": info.get("venue_name"),
                "pitch_type": info.get("pitch_type"),
                "straight_boundary_m": info.get("straight_boundary_m"),
                "square_boundary_m": info.get("square_boundary_m"),
                "avg_first_innings_score": info.get("avg_first_innings_score"),
                "avg_second_innings_score": info.get("avg_second_innings_score"),
            })
        else:
            venue_rows.append({
                "venue_id": vid,
                "venue_name": None,
                "pitch_type": None,
                "straight_boundary_m": np.nan,
                "square_boundary_m": np.nan,
                "avg_first_innings_score": np.nan,
                "avg_second_innings_score": np.nan,
            })

    venue_df = pd.DataFrame(venue_rows)
    # Drop venue metadata cols if they already exist to avoid merge conflicts
    for col in ["venue_name", "pitch_type", "straight_boundary_m", "square_boundary_m",
                "avg_first_innings_score", "avg_second_innings_score"]:
        if col in engineered.columns:
            engineered.drop(columns=[col], inplace=True)
    engineered = engineered.merge(venue_df, on="venue_id", how="left")

    # (d) Compute pitch batting friendliness
    engineered["pitch_batting_friendliness"] = engineered["pitch_type"].apply(
        pitch_batting_friendliness_score
    )

    # (e) Compute venue_avg_score
    engineered["venue_avg_score"] = engineered[
        ["avg_first_innings_score", "avg_second_innings_score"]
    ].mean(axis=1)

    # (f) Fetch weather per unique (venue_id, match_date) pair
    has_match_date = "match_date" in engineered.columns
    if has_match_date:
        # Ensure match_date is string-like for grouping
        engineered["_match_date_str"] = pd.to_datetime(
            engineered["match_date"]
        ).dt.strftime("%Y-%m-%d")

        weather_keys = engineered[["venue_id", "_match_date_str"]].drop_duplicates()
        weather_records = []
        for _, row in weather_keys.iterrows():
            w = fetch_match_weather(str(row["venue_id"]), str(row["_match_date_str"]))
            weather_records.append({
                "venue_id": row["venue_id"],
                "_match_date_str": row["_match_date_str"],
                "day_temp_c": w["day_temp_c"],
                "night_temp_c": w["night_temp_c"],
                "humidity_pct": w["humidity_pct"],
                "wind_speed_kmh": w["wind_speed_kmh"],
                "weather_source": w["source"],
            })
        weather_df = pd.DataFrame(weather_records)

        # Drop weather cols if they already exist to avoid merge conflicts
        for col in ["day_temp_c", "night_temp_c", "humidity_pct",
                    "wind_speed_kmh", "weather_source"]:
            if col in engineered.columns:
                engineered.drop(columns=[col], inplace=True)

        engineered = engineered.merge(
            weather_df, on=["venue_id", "_match_date_str"], how="left"
        )
        engineered.drop(columns=["_match_date_str"], inplace=True)
    else:
        # No match_date — fill weather columns with NaN for generic imputation
        for col in ["day_temp_c", "night_temp_c", "humidity_pct", "wind_speed_kmh"]:
            if col not in engineered.columns:
                engineered[col] = np.nan
        if "weather_source" not in engineered.columns:
            engineered["weather_source"] = "none"

    # (g) Compute dew_factor per row
    def _row_dew_factor(row):
        try:
            return compute_dew_factor(
                day_temp_c=float(row.get("day_temp_c", 0) or 0),
                night_temp_c=float(row.get("night_temp_c", 0) or 0),
                humidity_pct=float(row.get("humidity_pct", 0) or 0),
                wind_speed_kmh=float(row.get("wind_speed_kmh", 0) or 0),
                is_day_night_match=bool(int(row.get("is_day_night", 0) or 0)),
            )
        except Exception:
            return 0.0

    engineered["dew_factor"] = engineered.apply(_row_dew_factor, axis=1)

    return engineered


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    engineered = add_context_features(df)
    engineered = add_environment_features(engineered)
    engineered = add_statistical_features(engineered)
    engineered = engineer_time_series_features(engineered)
    engineered = add_lag_features(engineered)
    fill_cols = [col for col in DEFAULT_FEATURE_COLUMNS if col in engineered.columns]
    for col in fill_cols:
        sport_medians = engineered.groupby("sport")[col].transform("median")
        engineered[col] = engineered[col].fillna(sport_medians).fillna(engineered[col].median())
    engineered[fill_cols] = engineered[fill_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
    return engineered


def get_model_matrix(df: pd.DataFrame, sport: str | None = None) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    frame = build_feature_frame(df)
    if sport:
        frame = frame[frame["sport"].eq(sport)].copy()
    feature_cols = [col for col in DEFAULT_FEATURE_COLUMNS if col in frame.columns]
    X = frame[feature_cols]
    y = frame["performance_metric"]
    meta = frame[["sport", "player_id", "player_name", "match_date", "opposition"]].copy()
    return X, y, meta


def build_request_features(history: pd.DataFrame, request_values: dict[str, Any]) -> tuple[pd.DataFrame, dict]:
    row = history.iloc[-1:].copy()
    for key, value in request_values.items():
        if key in row.columns or key in ("venue_id", "is_day_night"):
            row[key] = value
    match_date_raw = request_values.get("match_date", pd.Timestamp.today())
    row["match_date"] = pd.to_datetime(str(match_date_raw))
    row["performance_metric"] = history["performance_metric"].iloc[-1]
    combined = pd.concat([history, row], ignore_index=True)
    features = build_feature_frame(combined).tail(1)

    # Extract context safely
    def clean_val(col_name: str, target_type: type) -> Any:
        if col_name not in features.columns:
            return None
        val = features[col_name].iloc[0]
        if pd.isna(val):
            return None
        try:
            if target_type == bool:
                return bool(int(val))
            return target_type(val)
        except Exception:
            return None

    context = {
        "venue_id": clean_val("venue_id", str),
        "venue_name": clean_val("venue_name", str),
        "pitch_type": clean_val("pitch_type", str),
        "pitch_batting_friendliness": clean_val("pitch_batting_friendliness", float),
        "straight_boundary_m": clean_val("straight_boundary_m", float),
        "square_boundary_m": clean_val("square_boundary_m", float),
        "venue_avg_score": clean_val("venue_avg_score", float),
        "day_temp_c": clean_val("day_temp_c", float),
        "night_temp_c": clean_val("night_temp_c", float),
        "humidity_pct": clean_val("humidity_pct", float),
        "wind_speed_kmh": clean_val("wind_speed_kmh", float),
        "dew_factor": clean_val("dew_factor", float),
        "is_day_night": clean_val("is_day_night", bool),
        "weather_source": clean_val("weather_source", str),
    }

    model_input = features[[col for col in DEFAULT_FEATURE_COLUMNS if col in features.columns]]
    return model_input, context
