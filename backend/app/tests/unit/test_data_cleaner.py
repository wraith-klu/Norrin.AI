from __future__ import annotations

import unittest

import pandas as pd

from app.services.data_collection import clean_and_validate, generate_sample_data
from app.services.weather_service import load_venues


class DataCleanerTests(unittest.TestCase):

    def test_cleaner_adds_outlier_flag(self):
        df = clean_and_validate(generate_sample_data(rows_per_sport=90, persist=False))
        self.assertIn("is_outlier", df.columns)

    # --- Phase 4 Tests ---

    def test_sample_data_has_venue_id_and_is_day_night(self):
        # generate_sample_data() output contains venue_id and is_day_night columns with no nulls
        df = generate_sample_data(rows_per_sport=90, persist=False)
        
        self.assertIn("venue_id", df.columns)
        self.assertIn("is_day_night", df.columns)
        
        self.assertEqual(df["venue_id"].isna().sum(), 0)
        self.assertEqual(df["is_day_night"].isna().sum(), 0)

    def test_venue_ids_are_valid(self):
        # venue_id values are drawn from the actual seeded venues table (not garbage strings)
        df = generate_sample_data(rows_per_sport=90, persist=False)
        
        venues_df = load_venues()
        valid_venue_ids = set(venues_df["venue_id"].dropna().unique())
        
        for vid in df["venue_id"].unique():
            self.assertIn(vid, valid_venue_ids)

    def test_sample_data_determinism(self):
        # calling it twice with the same seed produces identical venue_id/is_day_night assignments
        df1 = generate_sample_data(rows_per_sport=90, seed=42, persist=False)
        df2 = generate_sample_data(rows_per_sport=90, seed=42, persist=False)
        
        pd.testing.assert_frame_equal(df1, df2)
