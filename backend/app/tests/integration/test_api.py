import json
import unittest
import unittest.mock
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


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

    def test_v1_predict_without_venue_overrides(self):
        """POST /v1/predict without venue_id/is_day_night still returns 200 and contextual_factors key."""
        client = TestClient(app)
        response = client.post(
            "/v1/predict",
            json={
                "player_id": 1,
                "sport": "cricket",
                "match_date": "2026-08-01",
                "opposition": "Team X",
                "home_away": "home",
            },
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify JSON is parseable by default json module (fails if bare NaN/Infinity exist)
        data = json.loads(response.text)
        self.assertIn("contextual_factors", data)
        cf = data["contextual_factors"]
        self.assertIsInstance(cf, dict)
        
        # Assert values are only str, float, bool, int, or None
        allowed_types = (str, float, bool, int, type(None))
        for k, v in cf.items():
            self.assertIsInstance(v, allowed_types, f"Key {k} has invalid type {type(v)}")

    def test_v1_predict_with_venue_overrides(self):
        """POST /v1/predict with a venue_id from seed_venues.csv returns venue_name and pitch_type."""
        client = TestClient(app)
        response = client.post(
            "/v1/predict",
            json={
                "player_id": 1,
                "sport": "cricket",
                "match_date": "2026-08-01",
                "opposition": "Team X",
                "home_away": "home",
                "venue_id": "wankhede",
                "is_day_night": True
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertIn("contextual_factors", data)
        cf = data["contextual_factors"]
        
        self.assertEqual(cf["venue_id"], "wankhede")
        self.assertEqual(cf["venue_name"], "Wankhede Stadium")
        self.assertEqual(cf["pitch_type"], "batting_friendly")
        self.assertTrue(cf["is_day_night"])
        
        # Assert values are only str, float, bool, int, or None
        allowed_types = (str, float, bool, int, type(None))
        for k, v in cf.items():
            self.assertIsInstance(v, allowed_types, f"Key {k} has invalid type {type(v)}")

    def test_v1_predict_batch_mix(self):
        """POST /v1/predict-batch with 2 requests (one with venue_id, one without) succeeds."""
        client = TestClient(app)
        response = client.post(
            "/v1/predict-batch",
            json=[
                {
                    "player_id": 1,
                    "sport": "cricket",
                    "match_date": "2026-08-01",
                    "opposition": "Team X",
                    "home_away": "home",
                    "venue_id": "mcg",
                    "is_day_night": False
                },
                {
                    "player_id": 2,
                    "sport": "football",
                    "match_date": "2026-08-02",
                    "opposition": "Team Y",
                    "home_away": "away"
                }
            ]
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        
        # Verify first prediction (with override)
        p1 = data[0]
        self.assertIn("contextual_factors", p1)
        cf1 = p1["contextual_factors"]
        self.assertEqual(cf1["venue_id"], "mcg")
        self.assertEqual(cf1["venue_name"], "Melbourne Cricket Ground")
        self.assertEqual(cf1["pitch_type"], "balanced")
        self.assertFalse(cf1["is_day_night"])
        
        # Verify second prediction (without override)
        p2 = data[1]
        self.assertIn("contextual_factors", p2)
        cf2 = p2["contextual_factors"]
        self.assertIsInstance(cf2, dict)

    @patch("requests.post")
    @patch("requests.get")
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "fake_key"})
    def test_v1_cricket_predict_manual_mocked(self, mock_get, mock_post):
        """POST /v1/cricket/predict-manual with match_date returns contextual_factors and prompt has environmental section."""
        # Mock requests.get (for DDG / Cricbuzz) to return some mock HTML
        mock_get_response = unittest.mock.MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.text = "<html></html>"
        mock_get_response.json.return_value = {}
        mock_get.return_value = mock_get_response

        # Mock requests.post (for OpenRouter) to return a structured JSON response
        mock_post_response = unittest.mock.MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "player_name": "Virat Kohli",
                            "role": "batsman",
                            "visual_tagline": "A dominant run scorer",
                            "reasoning_markdown": "Matches details...",
                            "batsman_prediction": {
                                "predicted_runs_range": "40 to 60",
                                "who_can_get_him_out": "none",
                                "possible_mode_of_dismissal": "caught",
                                "possible_threats": "none",
                                "bowling_weakness": [],
                                "bowling_strength": [],
                                "length_weakness": [],
                                "length_strength": []
                            },
                            "bowler_prediction": None,
                            "conditions_impact": {
                                "pitch_reading": "Pitch is good for batting",
                                "weather_dew_note": "Dew might help chasing",
                                "ground_dimension_note": "Short boundaries favor shot making"
                            }
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_post_response

        # Call endpoint
        client = TestClient(app)
        response = client.post(
            "/v1/cricket/predict-manual",
            json={
                "player_name": "Virat Kohli",
                "opposition": "Australia",
                "venue": "Melbourne Cricket Ground",
                "match_format": "T20",
                "match_date": "2026-08-01",
                "is_day_night": True
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("contextual_factors", data)
        self.assertEqual(data["contextual_factors"]["venue_id"], "mcg")
        self.assertEqual(data["contextual_factors"]["venue_name"], "Melbourne Cricket Ground")
        self.assertEqual(data["contextual_factors"]["is_day_night"], True)
        
        self.assertIn("conditions_impact", data)
        self.assertEqual(data["conditions_impact"]["pitch_reading"], "Pitch is good for batting")

        # Verify the prompt sent to OpenRouter contains the environmental header
        self.assertTrue(mock_post.called)
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_args[0], "https://openrouter.ai/api/v1/chat/completions")
        
        payload = called_kwargs["json"]
        user_message = payload["messages"][1]["content"]
        self.assertIn("MATCH-DAY ENVIRONMENTAL CONDITIONS", user_message)

