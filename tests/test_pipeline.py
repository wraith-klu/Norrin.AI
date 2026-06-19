import unittest

from fastapi.testclient import TestClient

from api import app
from sports_predictor.data_collection import clean_and_validate, generate_sample_data
from sports_predictor.feature_engineering import get_model_matrix
from sports_predictor.models import train_sport_model


class PipelineTests(unittest.TestCase):
    def test_feature_pipeline_creates_model_matrix(self):
        df = clean_and_validate(generate_sample_data(rows_per_sport=180, persist=False))
        X, y, meta = get_model_matrix(df, sport="cricket")
        self.assertFalse(X.empty)
        self.assertEqual(len(X), len(y))
        self.assertEqual(len(X), len(meta))
        self.assertIn("rolling_avg_5", X.columns)
        self.assertEqual(int(X.isna().sum().sum()), 0)

    def test_train_single_sport_model(self):
        df = clean_and_validate(generate_sample_data(rows_per_sport=240, persist=False))
        bundle = train_sport_model(df, "nba")
        self.assertGreater(bundle.metrics["r2"], 0.5)
        self.assertGreater(bundle.feature_importance.shape[0], 0)

    def test_api_prediction(self):
        client = TestClient(app)
        response = client.post(
            "/predict",
            json={
                "player_id": 1,
                "sport": "football",
                "match_date": "2026-06-19",
                "opposition": "Team 1",
                "home_away": "home",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["sport"], "football")
        self.assertIn("confidence_interval", payload)


if __name__ == "__main__":
    unittest.main()
