# Data Dictionary

- `sport`: cricket, football, or nba.
- `player_id`: Numeric player identifier.
- `match_date`: Match or game date.
- `opposition`: Opposing team label.
- `is_home`: 1 for home, 0 for away.
- `opposition_strength`: Normalized opponent strength.
- `days_rest`: Days since the previous match.
- `injury_risk`: Normalized injury risk from 0 to 1.
- `performance_metric`: Sport-normalized target used by the demo model.

## Phase 3 — Environment & Venue Features

The following columns are added by `add_environment_features()` in `components/feature_engineering.py`
and are included in `DEFAULT_FEATURE_COLUMNS` for model training. All are numeric.

| Column | Type | Range / Units | Source |
| ------ | ---- | ------------- | ------ |
| `venue_id` | string | Venue slug (e.g. `wankhede`) | Synthetic generator / API request |
| `is_day_night` | int | 0 = day, 1 = day-night/floodlit | Derived from venue `is_day_night_ground` flag or synthetic roll |
| `day_temp_c` | float | °C, typically 5–45 | `fetch_match_weather()` — live (WeatherAPI) or deterministic synthetic fallback |
| `night_temp_c` | float | °C, typically 2–42 | Same as above; guaranteed < `day_temp_c` |
| `humidity_pct` | float | 0–100 % | Same as above |
| `wind_speed_kmh` | float | 0–80 km/h | Same as above |
| `dew_factor` | float | 0.0–1.0 | Derived via `dew_factor()` physics function from temp/humidity/wind/is_day_night |
| `pitch_batting_friendliness` | float | 0.0–1.0 | `pitch_batting_friendliness_score(pitch_type)` from venue metadata |
| `venue_avg_score` | float | 0–350+ runs | Mean of `avg_first_innings_score` and `avg_second_innings_score` from `venues` table |
| `straight_boundary_m` | float | metres (usually 65–90) | Venue metadata (`venues` table) |
| `square_boundary_m` | float | metres (usually 55–80) | Venue metadata (`venues` table) |
