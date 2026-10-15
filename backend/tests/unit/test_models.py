import unittest

from src.models.xgboost_model import PerformancePredictor
from sports_predictor.data_collection import clean_and_validate, generate_sample_data
from sports_predictor.feature_engineering import get_model_matrix


class ModelTests(unittest.TestCase):
    def test_performance_predictor_training(self):
        df = clean_and_validate(generate_sample_data(rows_per_sport=180, persist=False))
        X, y, _ = get_model_matrix(df, "football")
        model = PerformancePredictor("football").train(X, y)
        self.assertTrue(model.is_trained)
        self.assertEqual(len(model.predict(X.head(3))), 3)
