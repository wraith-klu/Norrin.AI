from __future__ import annotations

from datetime import date
import functools
import hashlib
import logging
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from app.config import DATA_DIR

logger = logging.getLogger(__name__)

# In-memory weather cache: keyed by f"{venue_id}:{match_date}" -> weather dict
_weather_cache: dict[str, dict] = {}



def dew_point_celsius(temp_c: float, humidity_pct: float) -> float:
    """Calculates dew point temperature in Celsius using the Magnus-Tetens formula.
    
    Formula:
        alpha = ((a * T) / (b + T)) + ln(RH / 100)
        Td = (b * alpha) / (a - alpha)
        where a = 17.27 and b = 237.7
    """
    a = 17.27
    b = 237.7
    # Clip relative humidity to prevent log(0) errors
    rh = max(0.01, min(100.0, humidity_pct))
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh / 100.0)
    return (b * alpha) / (a - alpha)


def dew_factor(day_temp_c: float, night_temp_c: float,
               humidity_pct: float, wind_speed_kmh: float,
               is_day_night_match: bool) -> float:
    """Calculates a physics-based dew factor (0.0 to 1.0) for a match.
    
    If the match is not played under day-night conditions, the dew factor is 0.0.
    Otherwise, we use Magnus-Tetens dew point, temperature drop, and wind penalty
    to estimate dew risk, capped at 1.0 and rounded to 3 decimal places.
    """
    if not is_day_night_match:
        return 0.0

    # Calculate dew point at the night temperature
    dp = dew_point_celsius(night_temp_c, humidity_pct)
    
    # Dew point depression (difference between night temp and dew point)
    depression = max(0.0, night_temp_c - dp)
    
    # 1. Closeness to dew point (0.0 to 1.0).
    # Dew forms when depression is 0. We scale it linearly up to a 10°C gap.
    closeness_factor = max(0.0, 1.0 - (depression / 10.0))
    
    # 2. Temperature drop factor (0.0 to 1.0).
    # Large temperature drops from day to night trigger rapid condensation.
    temp_drop = max(0.0, day_temp_c - night_temp_c)
    temp_drop_factor = min(1.0, temp_drop / 15.0)
    
    # 3. Relative Humidity factor (0.0 to 1.0).
    humidity_factor = max(0.0, min(100.0, humidity_pct)) / 100.0
    
    # 4. Wind penalty factor (0.0 to 1.0).
    # Wind mixes air layers, preventing surface cooling and moisture settlement.
    # Wind speeds >= 30 km/h are assumed to prevent dew completely.
    wind_penalty = max(0.0, 1.0 - (wind_speed_kmh / 30.0))
    
    # Combine thermodynamic components:
    # 40% dew point proximity, 30% relative humidity, 30% temperature drop.
    thermo_score = (0.4 * closeness_factor) + (0.3 * humidity_factor) + (0.3 * temp_drop_factor)
    
    # Apply wind penalty as a direct inhibitor multiplier
    raw_factor = thermo_score * wind_penalty
    
    return round(max(0.0, min(1.0, raw_factor)), 3)


def pitch_batting_friendliness_score(pitch_type: str | None) -> float:
    """Maps a pitch type string to a batting friendliness score from 0.0 to 1.0.
    
    Mapping:
        batting_friendly = 1.0
        balanced = 0.6
        dry_turner = 0.4
        green_seaming = 0.2
        bowling_friendly = 0.15
        unknown / None = 0.5
    """
    if not pitch_type or not isinstance(pitch_type, str):
        return 0.5
        
    mapping = {
        "batting_friendly": 1.0,
        "balanced": 0.6,
        "dry_turner": 0.4,
        "green_seaming": 0.2,
        "bowling_friendly": 0.15,
    }
    
    return mapping.get(pitch_type.lower().strip(), 0.5)


@functools.lru_cache(maxsize=4)
def load_venues(csv_path: Path | None = None) -> pd.DataFrame:
    """Loads seed_venues.csv into a pandas DataFrame.
    
    The loading is cached via lru_cache.
    """
    if csv_path is None:
        # Check standard data path or app data path
        paths_to_try = [
            DATA_DIR / "seed_venues.csv",
            Path(__file__).resolve().parent.parent / "data" / "seed_venues.csv",
        ]
        for path in paths_to_try:
            if path.exists():
                csv_path = path
                break
        if csv_path is None:
            raise FileNotFoundError("Could not find seed_venues.csv in standard directories.")
            
    return pd.read_csv(csv_path)


def get_venue(venue_id: str | None) -> dict | None:
    """Retrieves a single venue's row as a dictionary, or None if not found."""
    if not venue_id:
        return None
        
    try:
        df = load_venues()
    except Exception:
        return None
        
    target = venue_id.lower().strip()
    
    # Add defensive column cleaner
    df_clean = df.copy()
    if "venue_id" not in df_clean.columns:
        return None
        
    df_clean["_venue_id_clean"] = df_clean["venue_id"].astype(str).str.lower().str.strip()
    match = df_clean[df_clean["_venue_id_clean"] == target]
    
    if match.empty:
        return None
        
    row = match.iloc[0].drop("_venue_id_clean")
    
    # Convert row to dict, mapping NaN values to None and numpy types to python native types
    result = {}
    for col, val in row.items():
        if pd.isna(val):
            result[col] = None
        elif isinstance(val, (np.integer, int)):
            result[col] = int(val)
        elif isinstance(val, (np.floating, float)):
            result[col] = float(val)
        else:
            result[col] = val
            
    return result


def _synthetic_weather(venue_id: str, match_date: str) -> dict:
    """Generates a deterministic synthetic weather dictionary.
    
    The generation is seeded from a stable SHA-256 hash of the venue_id and match_date.
    Realistic ranges:
        day_temp_c: [15.0, 40.0]
        night_temp_c: day_temp_c - [2.0, 8.0]
        humidity_pct: [20.0, 95.0]
        wind_speed_kmh: [0.0, 30.0]
    """
    key = f"{venue_id}:{match_date}".encode("utf-8")
    hash_hex = hashlib.sha256(key).hexdigest()
    # Use the first 8 bytes of the hash to create an integer seed
    seed_int = int(hash_hex[:8], 16)
    
    rng = np.random.default_rng(seed_int)
    
    day_temp_c = rng.uniform(15.0, 40.0)
    temp_drop = rng.uniform(2.0, 8.0)
    night_temp_c = day_temp_c - temp_drop
    humidity_pct = rng.uniform(20.0, 95.0)
    wind_speed_kmh = rng.uniform(0.0, 30.0)
    
    return {
        "day_temp_c": round(day_temp_c, 1),
        "night_temp_c": round(night_temp_c, 1),
        "humidity_pct": round(humidity_pct, 1),
        "wind_speed_kmh": round(wind_speed_kmh, 1),
        "source": "synthetic",
    }



def _fetch_from_openweathermap(lat: float, lon: float, match_date_str: str, api_key: str) -> dict | None:
    """Queries OpenWeatherMap API for current or forecast weather."""
    try:
        match_dt = date.fromisoformat(match_date_str)
        today = date.today()
        diff_days = (match_dt - today).days
        
        # OpenWeatherMap Free API only supports:
        # - Current weather (for today/yesterday)
        # - 5-day forecast (for up to 5 days ahead)
        # Anything else is not accessible on the Free plan, so we return None to trigger synthetic fallback.
        if diff_days < -1 or diff_days > 5:
            logger.info(f"Date {match_date_str} is out of range for OpenWeatherMap Free API (diff_days={diff_days}). Falling back.")
            return None
            
        if diff_days <= 0:
            # Query Current Weather
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric"
            }
            res = requests.get(url, params=params, timeout=8)
            if res.status_code != 200:
                logger.warning(f"OpenWeatherMap current weather query failed: {res.text}")
                return None
            data = res.json()
            main = data.get("main", {})
            temp = float(main.get("temp", 20.0))
            temp_max = float(main.get("temp_max", temp))
            temp_min = float(main.get("temp_min", temp))
            if temp_max == temp_min:
                temp_min = temp_max - 5.0  # simple fallback for night drop
                
            humidity = float(main.get("humidity", 60.0))
            wind_speed = float(data.get("wind", {}).get("speed", 3.0)) * 3.6
            
            return {
                "day_temp_c": round(temp_max, 1),
                "night_temp_c": round(temp_min, 1),
                "humidity_pct": round(humidity, 1),
                "wind_speed_kmh": round(wind_speed, 1),
                "source": "live",
            }
        else:
            # Query 5-Day Forecast
            url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric"
            }
            res = requests.get(url, params=params, timeout=8)
            if res.status_code != 200:
                logger.warning(f"OpenWeatherMap forecast query failed: {res.text}")
                return None
            data = res.json()
            forecast_list = data.get("list", [])
            
            # Filter list to items on the match date
            match_items = []
            for item in forecast_list:
                dt_txt = item.get("dt_txt", "")  # e.g., "2026-07-09 12:00:00"
                if dt_txt.startswith(match_date_str):
                    match_items.append(item)
                    
            if not match_items:
                # If no forecast items found for that specific date, use the first item in the list
                if forecast_list:
                    match_items = [forecast_list[0]]
                else:
                    return None
                    
            temps = [float(item["main"]["temp"]) for item in match_items]
            humidities = [float(item["main"]["humidity"]) for item in match_items]
            wind_speeds = [float(item["wind"]["speed"]) * 3.6 for item in match_items]
            
            day_temp = max(temps) if temps else 20.0
            night_temp = day_temp - 5.0
            for item in match_items:
                dt_txt = item.get("dt_txt", "")
                if "18:00:00" in dt_txt or "21:00:00" in dt_txt:
                    night_temp = float(item["main"]["temp"])
                    break
                    
            avg_humidity = sum(humidities) / len(humidities) if humidities else 60.0
            avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 10.0
            
            return {
                "day_temp_c": round(day_temp, 1),
                "night_temp_c": round(night_temp, 1),
                "humidity_pct": round(avg_humidity, 1),
                "wind_speed_kmh": round(avg_wind, 1),
                "source": "live",
            }
    except Exception as e:
        logger.warning(f"Error parsing OpenWeatherMap data: {e}")
        return None


def fetch_match_weather(venue_id: str, match_date: str) -> dict:
    """Fetches weather conditions for a venue on a given match date.
    
    Tries to retrieve live data from WeatherAPI.com or OpenWeatherMap if WEATHER_API_KEY is configured.
    Falls back to deterministic synthetic weather on any error or if the key is missing.
    Queries are cached in-memory.
    """
    # Normalize inputs
    venue_id_clean = venue_id.lower().strip() if venue_id else ""
    match_date_clean = match_date.strip() if match_date else ""
    
    cache_key = f"{venue_id_clean}:{match_date_clean}"
    if cache_key in _weather_cache:
        return _weather_cache[cache_key]
        
    # Default fallback generator
    fallback = lambda: _synthetic_weather(venue_id_clean, match_date_clean)
    
    # 1. Resolve venue coordinates
    lat, lon = 0.0, 0.0
    if venue_id_clean:
        venue = get_venue(venue_id_clean)
        if venue:
            lat = venue.get("latitude") or 0.0
            lon = venue.get("longitude") or 0.0
        else:
            logger.warning(
                f"Venue '{venue_id_clean}' not found in database. "
                "Proceeding with generic coordinates (0.0, 0.0)."
            )
    else:
        logger.warning("Empty venue_id provided. Proceeding with generic coordinates (0.0, 0.0).")
        
    # 2. Check API key
    api_key = os.environ.get("WEATHER_API_KEY", "").strip()
    if not api_key:
        result = fallback()
        _weather_cache[cache_key] = result
        return result
        
    # Detect if the key is an OpenWeatherMap API key (typically a 32-char hex string)
    is_owm = len(api_key) == 32 and all(c in "0123456789abcdefABCDEF" for c in api_key)
    
    if is_owm:
        logger.info("Detected OpenWeatherMap API key format. Attempting query.")
        result = _fetch_from_openweathermap(lat, lon, match_date_clean, api_key)
        if result:
            _weather_cache[cache_key] = result
            return result
        logger.warning("OpenWeatherMap fetch failed. Falling back to synthetic.")
        result = fallback()
        _weather_cache[cache_key] = result
        return result
        
    # 3. Fetch from WeatherAPI
    try:
        # Determine if date is in the future relative to today
        match_dt = date.fromisoformat(match_date_clean)
        is_future = match_dt > date.today()
        
        endpoint = "future.json" if is_future else "history.json"
        url = f"http://api.weatherapi.com/v1/{endpoint}"
        
        params = {
            "key": api_key,
            "q": f"{lat},{lon}",
            "dt": match_date_clean,
        }
        
        response = requests.get(url, params=params, timeout=8)
        
        if response.status_code != 200:
            logger.warning(
                f"WeatherAPI request failed with status code {response.status_code}: "
                f"{response.text}. Falling back to synthetic weather."
            )
            result = fallback()
            _weather_cache[cache_key] = result
            return result
            
        data = response.json()
        forecastday = data["forecast"]["forecastday"][0]
        
        day_temp_c = float(forecastday["day"]["avgtemp_c"])
        
        # Night weather retrieval: attempt to get evening hour (19:00 = 7 PM)
        hours = forecastday.get("hour", [])
        
        # Default evening fallbacks from the day summary
        night_temp_c = day_temp_c
        humidity_pct = float(forecastday["day"]["avghumidity"])
        wind_speed_kmh = float(forecastday["day"].get("maxwind_kph", 0.0))
        
        if len(hours) > 19:
            hour_19 = hours[19]
            night_temp_c = float(hour_19["temp_c"])
            humidity_pct = float(hour_19["humidity"])
            wind_speed_kmh = float(hour_19["wind_kph"])
        elif len(hours) > 0:
            closest_hour = hours[min(19, len(hours) - 1)]
            night_temp_c = float(closest_hour["temp_c"])
            humidity_pct = float(closest_hour["humidity"])
            wind_speed_kmh = float(closest_hour["wind_kph"])
            
        result = {
            "day_temp_c": round(day_temp_c, 1),
            "night_temp_c": round(night_temp_c, 1),
            "humidity_pct": round(humidity_pct, 1),
            "wind_speed_kmh": round(wind_speed_kmh, 1),
            "source": "live",
        }
    except Exception as e:
        logger.warning(
            f"Exception occurred while calling WeatherAPI for venue={venue_id_clean}, "
            f"date={match_date_clean}: {e}. Falling back to synthetic weather."
        )
        result = fallback()
        
    _weather_cache[cache_key] = result
    return result



def resolve_venue_id(venue_text: str) -> str | None:
    """
    Fuzzy-match a free-text venue string (e.g. "Wankhede Stadium, Mumbai") against the venues table's venue_name and city columns
    (case-insensitive substring match in both directions — check if venue_text contains the venue_name, or venue_name contains a
    significant chunk of venue_text). Return the matched venue_id, or None if nothing matches confidently. Must not raise on empty/odd
    input — return None instead.
    """
    if not venue_text or not isinstance(venue_text, str):
        return None
    venue_text_lower = venue_text.lower().strip()
    try:
        df = load_venues()
        # First try exact match on venue_id
        for _, row in df.iterrows():
            vid = str(row.get("venue_id", "")).lower().strip()
            if vid == venue_text_lower:
                return str(row.get("venue_id"))
        
        # Next try substring match (venue_name inside venue_text, or venue_text inside venue_name)
        for _, row in df.iterrows():
            vname = str(row.get("venue_name", "")).lower().strip()
            vcity = str(row.get("city", "")).lower().strip()
            vid = str(row.get("venue_id", "")).lower().strip()
            
            if vname and (vname in venue_text_lower or venue_text_lower in vname):
                return str(row.get("venue_id"))
            if vcity and (vcity in venue_text_lower or venue_text_lower in vcity) and (vid in venue_text_lower or venue_text_lower in vid):
                return str(row.get("venue_id"))
            # Check if it has a city match + part of venue name
            if vcity and vcity in venue_text_lower:
                words = [w for w in vname.replace(".", "").split() if len(w) > 3]
                if any(w in venue_text_lower for w in words):
                    return str(row.get("venue_id"))
        
        # Next try stripping simple punctuation and matching
        stripped_text = "".join(c for c in venue_text_lower if c.isalnum() or c.isspace())
        for _, row in df.iterrows():
            vname = str(row.get("venue_name", "")).lower().strip()
            stripped_name = "".join(c for c in vname if c.isalnum() or c.isspace())
            if stripped_name in stripped_text or stripped_text in stripped_name:
                return str(row.get("venue_id"))
                
    except Exception:
        pass
    return None


