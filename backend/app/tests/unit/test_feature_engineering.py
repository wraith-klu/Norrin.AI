from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from app.services.data_collection import clean_and_validate, generate_sample_data
from app.components.feature_engineering import (
    add_environment_features,
    build_feature_frame,
    get_model_matrix,
)
from app.config import DEFAULT_FEATURE_COLUMNS


# Phase 3: ensure no real weather API calls occur during tests
@patch.dict(os.environ, {}, clear=True)
class FeatureEngineeringTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Generate sample data once for all tests in this class."""
        cls.sample_df = clean_and_validate(
            generate_sample_data(rows_per_sport=180, persist=False)
        )

    def test_feature_matrix_has_rolling_features(self):
        X, y, _ = get_model_matrix(self.sample_df, "cricket")
        self.assertIn("rolling_avg_5", X.columns)
        self.assertEqual(len(X), len(y))

    # --- Phase 3 Tests ---

    def test_build_feature_frame_no_venue_columns(self):
        """build_feature_frame() produces all 10 new environment columns with
        no unhandled NaNs after the fill step, regardless of whether venue_id
        was pre-populated (Phase 4) or injected defensively (Phase 3 fallback).
        Also verifies a stripped DataFrame (no venue_id/is_day_night) still works."""
        # 1. Standard path: Phase 4 data includes venue_id and is_day_night
        out = build_feature_frame(self.sample_df)

        new_cols = [
            "day_temp_c", "night_temp_c", "humidity_pct", "wind_speed_kmh",
            "dew_factor", "is_day_night", "pitch_batting_friendliness",
            "venue_avg_score", "straight_boundary_m", "square_boundary_m",
        ]
        for col in new_cols:
            self.assertIn(col, out.columns, f"Missing column: {col}")
            nan_count = out[col].isna().sum()
            self.assertEqual(nan_count, 0, f"Column {col} has {nan_count} NaN values after fill step")

        # 2. Defensive path: strip venue_id and is_day_night — must still work
        stripped = self.sample_df.drop(columns=["venue_id", "is_day_night"], errors="ignore")
        self.assertNotIn("venue_id", stripped.columns)
        self.assertNotIn("is_day_night", stripped.columns)
        out_stripped = build_feature_frame(stripped)
        for col in new_cols:
            self.assertIn(col, out_stripped.columns, f"Stripped: missing column {col}")
            nan_count = out_stripped[col].isna().sum()
            self.assertEqual(nan_count, 0, f"Stripped: column {col} has {nan_count} NaN values")


    def test_determinism_same_venue_date(self):
        """Two rows with identical venue_id + match_date + is_day_night
        produce identical weather and dew_factor values."""
        df = self.sample_df.head(10).copy()
        df["venue_id"] = "wankhede"
        df["is_day_night"] = 1
        # Set same match_date for first two rows
        df.at[df.index[0], "match_date"] = pd.Timestamp("2026-07-20")
        df.at[df.index[1], "match_date"] = pd.Timestamp("2026-07-20")

        out = add_environment_features(df)
        row0 = out.iloc[0]
        row1 = out.iloc[1]

        for col in ["day_temp_c", "night_temp_c", "humidity_pct", "wind_speed_kmh", "dew_factor"]:
            self.assertEqual(row0[col], row1[col], f"Mismatch in {col} for same venue+date")

    def test_known_venue_produces_valid_scores(self):
        """A row with a known seeded venue_id produces pitch_batting_friendliness
        and venue_avg_score that are NOT NaN and within expected ranges."""
        df = self.sample_df.head(5).copy()
        df["venue_id"] = "wankhede"

        out = add_environment_features(df)

        for _, row in out.iterrows():
            self.assertFalse(pd.isna(row["pitch_batting_friendliness"]))
            self.assertTrue(0.0 <= row["pitch_batting_friendliness"] <= 1.0)
            self.assertFalse(pd.isna(row["venue_avg_score"]))
            # Wankhede avg scores: 180, 170 -> avg = 175
            self.assertTrue(100.0 <= row["venue_avg_score"] <= 250.0)
            # Boundary checks
            self.assertFalse(pd.isna(row["straight_boundary_m"]))
            self.assertFalse(pd.isna(row["square_boundary_m"]))

    def test_model_matrix_contains_new_columns(self):
        """get_model_matrix() output X contains all 10 new columns as numeric dtypes."""
        X, y, _ = get_model_matrix(self.sample_df, "cricket")

        new_cols = [
            "day_temp_c", "night_temp_c", "humidity_pct", "wind_speed_kmh",
            "dew_factor", "is_day_night", "pitch_batting_friendliness",
            "venue_avg_score", "straight_boundary_m", "square_boundary_m",
        ]
        for col in new_cols:
            self.assertIn(col, X.columns, f"Missing column in model matrix: {col}")
            self.assertTrue(
                pd.api.types.is_numeric_dtype(X[col]),
                f"Column {col} has dtype {X[col].dtype}, expected numeric"
            )

    def test_build_request_features_tuple_return(self):
        """build_request_features returns a tuple of (DataFrame, dict) with valid types."""
        from app.components.feature_engineering import build_request_features
        # Create a small history dataframe filtered by sport and player_id
        history = self.sample_df[(self.sample_df["sport"] == "cricket") & (self.sample_df["player_id"] == 1)].copy()
        
        request_values = {
            "player_id": 1,
            "sport": "cricket",
            "match_date": pd.Timestamp("2026-08-01"),
            "opposition": "Team X",
            "is_home": 1,
            "opposition_strength": 0.6,
            "injury_risk": 0.1,
            "days_rest": 3,
            "venue_id": "wankhede",
            "is_day_night": 1
        }
        
        X, context = build_request_features(history, request_values)
        self.assertIsInstance(X, pd.DataFrame)
        self.assertIsInstance(context, dict)
        
        # Verify columns in X
        self.assertEqual(len(X), 1)
        
        # Verify keys in context
        expected_keys = [
            "venue_id", "venue_name", "pitch_type", "pitch_batting_friendliness",
            "straight_boundary_m", "square_boundary_m", "venue_avg_score",
            "day_temp_c", "night_temp_c", "humidity_pct", "wind_speed_kmh",
            "dew_factor", "is_day_night", "weather_source"
        ]
        for key in expected_keys:
            self.assertIn(key, context)
            
        # Verify types in context
        self.assertEqual(context["venue_id"], "wankhede")
        self.assertEqual(context["venue_name"], "Wankhede Stadium")
        self.assertEqual(context["pitch_type"], "batting_friendly")
        self.assertTrue(isinstance(context["pitch_batting_friendliness"], float))
        self.assertTrue(isinstance(context["straight_boundary_m"], float))
        self.assertTrue(isinstance(context["is_day_night"], bool))
        self.assertTrue(context["is_day_night"])

