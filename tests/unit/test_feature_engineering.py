import unittest

from sports_predictor.data_collection import clean_and_validate, generate_sample_data
from sports_predictor.feature_engineering import get_model_matrix


class FeatureEngineeringTests(unittest.TestCase):
    def test_feature_matrix_has_rolling_features(self):
        df = clean_and_validate(generate_sample_data(rows_per_sport=180, persist=False))
        X, y, _ = get_model_matrix(df, "cricket")
        self.assertIn("rolling_avg_5", X.columns)
        self.assertEqual(len(X), len(y))
