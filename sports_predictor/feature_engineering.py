from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DEFAULT_FEATURE_COLUMNS


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


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    engineered = add_context_features(df)
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


def build_request_features(history: pd.DataFrame, request_values: dict[str, object]) -> pd.DataFrame:
    row = history.iloc[-1:].copy()
    for key, value in request_values.items():
        if key in row.columns:
            row.loc[row.index[0], key] = value
    row.loc[row.index[0], "match_date"] = pd.to_datetime(request_values.get("match_date", pd.Timestamp.today()))
    row.loc[row.index[0], "performance_metric"] = history["performance_metric"].iloc[-1]
    combined = pd.concat([history, row], ignore_index=True)
    features = build_feature_frame(combined).tail(1)
    return features[[col for col in DEFAULT_FEATURE_COLUMNS if col in features.columns]]
