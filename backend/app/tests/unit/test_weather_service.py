from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from app.services.weather_service import (
    _weather_cache,
    dew_factor,
    dew_point_celsius,
    fetch_match_weather,
    get_venue,
    load_venues,
    pitch_batting_friendliness_score,
)


class TestWeatherService(unittest.TestCase):

    def setUp(self):
        # Clear the in-memory weather cache before each test to ensure isolation
        _weather_cache.clear()

    def test_dew_factor_non_day_night(self):
        # dew_factor returns 0.0 when is_day_night_match=False regardless of inputs
        self.assertEqual(dew_factor(30.0, 26.0, 85.0, 5.0, False), 0.0)
        self.assertEqual(dew_factor(35.0, 15.0, 95.0, 0.0, False), 0.0)
        self.assertEqual(dew_factor(10.0, 5.0, 10.0, 40.0, False), 0.0)

    def test_dew_factor_comparison(self):
        # dew_factor returns a higher value for (humid, small temp-drop, low wind)
        # than for (dry, same temp-drop, high wind) — both day-night matches
        humid_low_wind = dew_factor(
            day_temp_c=30.0,
            night_temp_c=26.0,
            humidity_pct=85.0,
            wind_speed_kmh=5.0,
            is_day_night_match=True
        )
        dry_high_wind = dew_factor(
            day_temp_c=30.0,
            night_temp_c=26.0,
            humidity_pct=40.0,
            wind_speed_kmh=25.0,
            is_day_night_match=True
        )
        
        self.assertGreater(humid_low_wind, dry_high_wind)
        # Confirm noticeability: A should be quite high, B should be low
        self.assertGreater(humid_low_wind, 0.4)
        self.assertLess(dry_high_wind, 0.2)

    def test_dew_factor_boundaries(self):
        # dew_factor output is always within [0.0, 1.0]
        self.assertEqual(dew_factor(40.0, 10.0, 100.0, 0.0, True), 1.0)
        self.assertEqual(dew_factor(20.0, 20.0, 0.0, 50.0, True), 0.0)
        
        # Fuzz some parameter combinations to check bounds
        for temp_day in [15.0, 30.0, 45.0]:
            for temp_night in [10.0, 25.0, 35.0]:
                for hum in [0.0, 50.0, 100.0]:
                    for wind in [0.0, 15.0, 50.0]:
                        factor = dew_factor(temp_day, temp_night, hum, wind, True)
                        self.assertTrue(0.0 <= factor <= 1.0, f"Failed for {temp_day}, {temp_night}, {hum}, {wind}: {factor}")

    def test_pitch_batting_friendliness_score(self):
        # pitch_batting_friendliness_score returns exactly 0.5 for an unknown pitch_type string
        self.assertEqual(pitch_batting_friendliness_score("unknown"), 0.5)
        self.assertEqual(pitch_batting_friendliness_score("random_pitch"), 0.5)
        self.assertEqual(pitch_batting_friendliness_score(None), 0.5)
        
        # Test the rest of the exact mappings
        self.assertEqual(pitch_batting_friendliness_score("batting_friendly"), 1.0)
        self.assertEqual(pitch_batting_friendliness_score("balanced"), 0.6)
        self.assertEqual(pitch_batting_friendliness_score("dry_turner"), 0.4)
        self.assertEqual(pitch_batting_friendliness_score("green_seaming"), 0.2)
        self.assertEqual(pitch_batting_friendliness_score("bowling_friendly"), 0.15)

    def test_get_venue(self):
        # get_venue returns None for a nonexistent venue_id
        self.assertIsNone(get_venue("nonexistent_venue"))
        self.assertIsNone(get_venue(""))
        self.assertIsNone(get_venue(None))
        
        # get_venue returns a populated dict for one that exists in the seed data
        wankhede = get_venue("wankhede")
        self.assertIsNotNone(wankhede)
        self.assertEqual(wankhede["venue_id"], "wankhede")
        self.assertEqual(wankhede["city"], "Mumbai")
        self.assertEqual(wankhede["pitch_type"], "batting_friendly")
        self.assertEqual(wankhede["is_day_night_ground"], 1)
        self.assertTrue(isinstance(wankhede["latitude"], float))
        
        mcg = get_venue("mcg")
        self.assertIsNotNone(mcg)
        self.assertEqual(mcg["venue_id"], "mcg")
        self.assertEqual(mcg["city"], "Melbourne")
        self.assertEqual(mcg["pitch_type"], "balanced")
        self.assertEqual(mcg["is_day_night_ground"], 1)
        self.assertTrue(isinstance(mcg["latitude"], float))
        
        lords = get_venue("lords")
        self.assertIsNotNone(lords)
        self.assertEqual(lords["venue_id"], "lords")
        self.assertEqual(lords["is_day_night_ground"], 0)

    # --- Phase 2 Tests ---

    def test_synthetic_weather_temp_relation(self):
        # _synthetic_weather always returns night_temp_c < day_temp_c
        from app.services.weather_service import _synthetic_weather
        for i in range(100):
            res = _synthetic_weather(f"venue_{i}", f"2026-07-{i%28+1:02d}")
            self.assertLess(res["night_temp_c"], res["day_temp_c"])
            self.assertEqual(res["source"], "synthetic")

    def test_fetch_match_weather_no_api_key(self):
        # fetch_match_weather returns source="synthetic" and does not raise when WEATHER_API_KEY is unset
        with patch.dict(os.environ, {}, clear=True):
            res = fetch_match_weather("wankhede", "2026-07-20")
            self.assertEqual(res["source"], "synthetic")
            self.assertIn("day_temp_c", res)
            self.assertIn("night_temp_c", res)
            self.assertIn("humidity_pct", res)
            self.assertIn("wind_speed_kmh", res)

    def test_fetch_match_weather_determinism_and_caching(self):
        # fetch_match_weather for the SAME venue_id + match_date called twice returns IDENTICAL values both times
        with patch.dict(os.environ, {}, clear=True):
            res1 = fetch_match_weather("wankhede", "2026-07-20")
            res2 = fetch_match_weather("wankhede", "2026-07-20")
            self.assertEqual(res1, res2)

    def test_fetch_match_weather_different_dates(self):
        # fetch_match_weather for two DIFFERENT match_dates on the same venue returns different values
        with patch.dict(os.environ, {}, clear=True):
            res1 = fetch_match_weather("wankhede", "2026-07-20")
            res2 = fetch_match_weather("wankhede", "2026-07-21")
            self.assertNotEqual(res1, res2)

    def test_fetch_match_weather_api_failure(self):
        # fetch_match_weather with WEATHER_API_KEY set, but requests.get mocked to raise a ConnectionError,
        # still returns a valid dict with source="synthetic"
        with patch.dict(os.environ, {"WEATHER_API_KEY": "dummy_key"}):
            with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Connection timeout")):
                res = fetch_match_weather("wankhede", "2026-07-20")
                self.assertEqual(res["source"], "synthetic")
                self.assertIn("day_temp_c", res)

    def test_fetch_match_weather_api_success(self):
        # fetch_match_weather with WEATHER_API_KEY set and requests.get mocked to return a successful
        # JSON payload correctly parses it into the expected dict shape with source="live"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "forecast": {
                "forecastday": [
                    {
                        "day": {
                            "avgtemp_c": 31.2,
                            "avghumidity": 68.0,
                            "maxwind_kph": 15.5
                        },
                        "hour": [
                            {"time": f"2026-07-20 {h:02d}:00", "temp_c": 31.2 - (h - 12)*0.3, "humidity": 68, "wind_kph": 15.5}
                            for h in range(24)
                        ]
                    }
                ]
            }
        }
        # Evening hour index 19 (7 PM): temp_c = 31.2 - (19 - 12)*0.3 = 31.2 - 7*0.3 = 31.2 - 2.1 = 29.1
        
        with patch.dict(os.environ, {"WEATHER_API_KEY": "dummy_key"}):
            with patch("requests.get", return_value=mock_response) as mock_get:
                res = fetch_match_weather("wankhede", "2026-07-20")
                mock_get.assert_called_once()
                self.assertEqual(res["source"], "live")
                self.assertEqual(res["day_temp_c"], 31.2)
                self.assertEqual(res["night_temp_c"], 29.1)
                self.assertEqual(res["humidity_pct"], 68.0)
                self.assertEqual(res["wind_speed_kmh"], 15.5)

    def test_fetch_match_weather_unknown_venue(self):
        # fetch_match_weather with an unknown venue_id does not raise, and still returns a valid weather dict
        with patch.dict(os.environ, {}, clear=True):
            res = fetch_match_weather("unknown_venue_name", "2026-07-20")
            self.assertEqual(res["source"], "synthetic")
            self.assertIn("day_temp_c", res)
