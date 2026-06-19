import unittest

from fastapi.testclient import TestClient

from api.main import app


class ApiTests(unittest.TestCase):
    def test_v1_predict(self):
        client = TestClient(app)
        response = client.post(
            "/v1/predict",
            json={
                "player_id": 1,
                "sport": "nba",
                "match_date": "2026-06-19",
                "opposition": "Team 1",
                "home_away": "home",
            },
        )
        self.assertEqual(response.status_code, 200)
