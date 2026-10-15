"""
realtime_cricket.py
Real-time cricket player analysis and prediction engine.
Scrapes live data from DuckDuckGo and Cricbuzz, then calls OpenRouter LLM
to produce deep structured predictions for batsmen and bowlers.
"""
from __future__ import annotations

from datetime import date
import json
import logging
import os
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

import requests
from bs4 import BeautifulSoup

from app.services.weather_service import (
    resolve_venue_id,
    get_venue,
    fetch_match_weather,
    dew_factor as compute_dew_factor,
    pitch_batting_friendliness_score,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

def search_ddg(query: str, num_results: int = 5) -> list[dict]:
    """Search DuckDuckGo and return list of {title, url, snippet}.

    Primary: duckduckgo-search package (uses primp TLS client — bypasses CF block).
    Fallback: raw html.duckduckgo.com scrape.
    Returns an empty list on total failure (never returns error-sentinel dicts).
    """
    # ── Primary: ddgs / duckduckgo-search package ──────────────────────────────
    try:
        try:
            from ddgs import DDGS  # type: ignore[import]  # ddgs >= 9.x
        except ImportError:
            from duckduckgo_search import DDGS  # type: ignore[import]  # duckduckgo-search 6-8.x
        with DDGS(timeout=8) as ddgs:
            raw = list(ddgs.text(query, max_results=num_results))
        if raw:
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                for r in raw
                if r.get("href")  # skip any blank-URL entries
            ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("DDGS package search failed (%s); falling back to HTML scrape.", exc)

    # ── Fallback: html.duckduckgo.com scrape ──────────────────────────────────
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    for attempt in range(2):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                time.sleep(2)
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            results: list[dict] = []
            for div in soup.find_all("div", class_="result"):
                a_url = div.find("a", class_="result__url")
                a_snip = div.find("a", class_="result__snippet")
                if not (a_url and a_snip):
                    continue
                href = str(a_url.get("href") or "")
                parsed = urllib.parse.urlparse(href)
                real_url = href
                if parsed.query:
                    qs = urllib.parse.parse_qs(parsed.query)
                    if "uddg" in qs:
                        real_url = qs["uddg"][0]
                if not real_url:
                    continue
                results.append(
                    {
                        "title": a_url.get_text().strip(),
                        "url": real_url,
                        "snippet": a_snip.get_text().strip(),
                    }
                )
                if len(results) >= num_results:
                    break
            if results:
                return results
            time.sleep(3)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DDG HTML fallback attempt %d failed: %s", attempt, exc)
            time.sleep(2)
    return []



# ---------------------------------------------------------------------------
# Cricbuzz scraper
# ---------------------------------------------------------------------------

def _extract_escaped_json_block(html: str, key: str) -> dict | None:
    """
    Extract a JSON object embedded inside Next.js RSC escaped HTML payload.
    The data appears as:  \\"key\\":{...}  inside a JS string.
    """
    marker = f'\\"{key}\\":{{'
    idx = html.find(marker)
    if idx == -1:
        return None
    start = idx + len(marker) - 1  # points at '{'
    depth = 0
    pos = start
    while pos < len(html):
        c = html[pos]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        pos += 1
    raw = html[start : pos + 1]
    # Unescape the double-escaped quotes / backslashes from the RSC wrapper
    unescaped = raw.replace('\\"', '"').replace("\\\\", "\\")
    try:
        return json.loads(unescaped)
    except Exception:  # noqa: BLE001
        return None


def scrape_cricbuzz_profile(url: str) -> dict:
    """
    Fetch a Cricbuzz player profile page and return structured data:
    {name, role, country, dob, bat_style, bowl_style,
     batting_summary, bowling_summary, recent_batting, recent_bowling,
     rankings, profile_url}
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code} fetching {url}"}

        html = resp.text

        player_raw = _extract_escaped_json_block(html, "playerData")
        batting_raw = _extract_escaped_json_block(html, "playerBattingStats")
        bowling_raw = _extract_escaped_json_block(html, "playerBowlingStats")

        if not player_raw:
            return {"error": "playerData block not found in page"}

        # --- batting summary ---
        batting_summary: dict[str, Any] = {}
        if batting_raw:
            headers_list = batting_raw.get("headers", [])
            # Replace ROWHEADER label with empty string for cleaner display
            display_headers = [h if h != "ROWHEADER" else "Stat" for h in headers_list]
            rows = [v.get("values", []) for v in batting_raw.get("values", [])]
            batting_summary = {"headers": display_headers, "rows": rows}

        # --- bowling summary ---
        bowling_summary: dict[str, Any] = {}
        if bowling_raw:
            headers_list = bowling_raw.get("headers", [])
            display_headers = [h if h != "ROWHEADER" else "Stat" for h in headers_list]
            rows = [v.get("values", []) for v in bowling_raw.get("values", [])]
            bowling_summary = {"headers": display_headers, "rows": rows}

        # Fallback to BeautifulSoup parsing of server-rendered tables if JSON keys are absent
        if not batting_summary or not bowling_summary:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                tables = soup.find_all("table")
                for table in tables:
                    tr_headers = table.find_all("th")
                    headers_list = [th.get_text(strip=True) for th in tr_headers]
                    if not headers_list:
                        # try getting from first tr's td if th is not used
                        first_tr = table.find("tr")
                        if first_tr:
                            headers_list = [td.get_text(strip=True) for td in first_tr.find_all(["td", "th"])]
                    
                    if not headers_list:
                        continue
                        
                    display_headers = [h if h else "Stat" for h in headers_list]
                    
                    rows = []
                    for tr in table.find_all("tr")[1:]:
                        row_vals = [td.get_text(strip=True) for td in tr.find_all("td")]
                        if row_vals:
                            rows.append(row_vals)
                            
                    if not rows:
                        continue
                        
                    # Check if it's the batting table (look at row headers in the first column)
                    first_cols = [r[0].lower().strip() for r in rows if r]
                    is_bat_table = any(x in first_cols for x in ["runs", "100", "50", "hs", "avg", "sr"])
                    is_bowl_table = any(x in first_cols for x in ["wkts", "bbi", "5w", "balls", "econ"])
                    
                    if is_bat_table and not batting_summary:
                        batting_summary = {"headers": display_headers, "rows": rows}
                    elif is_bowl_table and not bowling_summary:
                        bowling_summary = {"headers": display_headers, "rows": rows}
            except Exception as e:
                logger.warning(f"Error parsing tables using BeautifulSoup fallback: {e}")


        # --- recent form tables ---
        recent_bat = player_raw.get("recentBatting", {})
        recent_bowl = player_raw.get("recentBowling", {})

        recent_batting_rows = []
        if recent_bat:
            bat_headers = recent_bat.get("headers", [])
            for row in recent_bat.get("rows", []):
                vals = row.get("values", [])
                # first value is match_id, skip it
                if len(vals) > 1:
                    recent_batting_rows.append(vals[1:])
            recent_bat_headers = bat_headers  # Score, OPPN., Format, Date
        else:
            bat_headers = []
            recent_bat_headers = []

        recent_bowling_rows = []
        if recent_bowl:
            bowl_headers = recent_bowl.get("headers", [])
            for row in recent_bowl.get("rows", []):
                vals = row.get("values", [])
                if len(vals) > 1:
                    recent_bowling_rows.append(vals[1:])
            recent_bowl_headers = bowl_headers
        else:
            bowl_headers = []
            recent_bowl_headers = []

        rankings = player_raw.get("rankings", {})

        return {
            "name": player_raw.get("name", "Unknown"),
            "full_name": player_raw.get("fullName", ""),
            "role": player_raw.get("role", "Unknown"),
            "country": player_raw.get("intlTeam", "Unknown"),
            "dob": player_raw.get("DoBFormat", player_raw.get("DoB", "")),
            "bat_style": player_raw.get("bat", ""),
            "bowl_style": player_raw.get("bowl", ""),
            "height": player_raw.get("height", ""),
            "image_url": player_raw.get("image", ""),
            "batting_summary": batting_summary,
            "bowling_summary": bowling_summary,
            "recent_batting": {
                "headers": recent_bat_headers,
                "rows": recent_batting_rows,
            },
            "recent_bowling": {
                "headers": recent_bowl_headers,
                "rows": recent_bowling_rows,
            },
            "rankings": rankings,
            "profile_url": url,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"scrape_cricbuzz_profile failed: {exc}"}


def find_cricbuzz_profile_url(player_name: str) -> str | None:
    """Search DDG for the player's Cricbuzz profile URL.
    Matches both www.cricbuzz.com and m.cricbuzz.com URLs.
    Retries with an alternate query if first attempt fails.
    """
    queries = [
        f"{player_name} cricbuzz profile",
        f"cricbuzz {player_name} profiles cricket",
        f"{player_name} cricketer cricbuzz stats",
    ]
    for query in queries:
        results = search_ddg(query, num_results=6)
        for r in results:
            url = r["url"]
            if "cricbuzz.com/profiles/" in url:
                # Normalize mobile URL to desktop
                url = url.replace("m.cricbuzz.com", "www.cricbuzz.com")
                # Trim sub-paths like /all-matches/batting
                parts = url.split("/profiles/")
                if len(parts) == 2:
                    profile_id_name = "/".join(parts[1].split("/")[:2])
                    return f"{parts[0]}/profiles/{profile_id_name}"
                return url
    return None


def build_environmental_conditions(
    venue_text: str,
    match_date: str | None,
    is_day_night: bool | None,
    match_format: str = "T20"
) -> dict:
    if not match_date:
        match_date = date.today().isoformat()
        
    fmt = (match_format or "T20").upper().strip()
    if "TEST" in fmt:
        score_multiplier = 2.0
    elif "ODI" in fmt:
        score_multiplier = 1.6
    else:
        score_multiplier = 1.0

    res = {
        "venue_id": None,
        "venue_name": None,
        "pitch_type": None,
        "pitch_batting_friendliness": None,
        "straight_boundary_m": None,
        "square_boundary_m": None,
        "venue_avg_score": None,
        "day_temp_c": None,
        "night_temp_c": None,
        "humidity_pct": None,
        "wind_speed_kmh": None,
        "dew_factor": None,
        "is_day_night": None,
        "weather_source": None,
    }
    try:
        resolved_vid = resolve_venue_id(venue_text)
        venue_info = None
        if resolved_vid:
            res["venue_id"] = resolved_vid
            venue_info = get_venue(resolved_vid)
            if venue_info:
                res["venue_name"] = venue_info.get("venue_name")
                res["pitch_type"] = venue_info.get("pitch_type")
                res["straight_boundary_m"] = float(venue_info.get("straight_boundary_m")) if venue_info.get("straight_boundary_m") is not None else None
                res["square_boundary_m"] = float(venue_info.get("square_boundary_m")) if venue_info.get("square_boundary_m") is not None else None
                
                f_score = venue_info.get("avg_first_innings_score")
                s_score = venue_info.get("avg_second_innings_score")
                
                if f_score is not None:
                    f_score = float(f_score) * score_multiplier
                if s_score is not None:
                    s_score = float(s_score) * score_multiplier
                
                if f_score is not None and s_score is not None:
                    res["venue_avg_score"] = (f_score + s_score) / 2.0
                elif f_score is not None:
                    res["venue_avg_score"] = f_score
                elif s_score is not None:
                    res["venue_avg_score"] = s_score
                    
                res["pitch_batting_friendliness"] = pitch_batting_friendliness_score(res["pitch_type"])

        eff_is_day_night = True
        if is_day_night is not None:
            eff_is_day_night = is_day_night
        elif venue_info and venue_info.get("is_day_night_ground") is not None:
            eff_is_day_night = bool(int(venue_info.get("is_day_night_ground", 0)))
            
        res["is_day_night"] = eff_is_day_night

        w_key = resolved_vid if resolved_vid else venue_text
        weather = fetch_match_weather(w_key, match_date)
        if weather:
            res["day_temp_c"] = float(weather.get("day_temp_c")) if weather.get("day_temp_c") is not None else None
            res["night_temp_c"] = float(weather.get("night_temp_c")) if weather.get("night_temp_c") is not None else None
            res["humidity_pct"] = float(weather.get("humidity_pct")) if weather.get("humidity_pct") is not None else None
            res["wind_speed_kmh"] = float(weather.get("wind_speed_kmh")) if weather.get("wind_speed_kmh") is not None else None
            res["weather_source"] = weather.get("source")

            res["dew_factor"] = compute_dew_factor(
                day_temp_c=res["day_temp_c"] or 0.0,
                night_temp_c=res["night_temp_c"] or 0.0,
                humidity_pct=res["humidity_pct"] or 0.0,
                wind_speed_kmh=res["wind_speed_kmh"] or 0.0,
                is_day_night_match=eff_is_day_night,
            )
    except Exception:
        if is_day_night is not None:
            res["is_day_night"] = is_day_night
        else:
            res["is_day_night"] = True
            
    return res


# ---------------------------------------------------------------------------
# Context collector
# ---------------------------------------------------------------------------

def collect_player_match_context(
    player_name: str,
    opposition: str,
    venue: str,
    match_format: str = "T20",
    status_callback: Callable[[str], None] | None = None,
    match_date: str | None = None,
    is_day_night: bool | None = None,
) -> dict:
    """
    Run a battery of web searches and Cricbuzz scraping to build a
    rich, structured context dict for use with the LLM predictor.
    All independent I/O tasks run in parallel to minimise latency.
    """

    def _cb(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    ctx: dict[str, Any] = {}

    # Step 1: Resolve profile URL (fast lookup, done first so closures can capture it)
    _cb(f"🔍 Searching Cricbuzz profile for **{player_name}**...")
    profile_url = find_cricbuzz_profile_url(player_name)

    # Step 2: Fire all independent I/O tasks in parallel
    _cb(
        f"⚡ Parallel data gathering: Cricbuzz stats, recent {match_format} form, "
        f"head-to-head vs {opposition}, {venue} pitch + weather, opposition bowlers..."
    )

    def _fetch_profile() -> tuple[str, Any]:
        if profile_url:
            return "profile_data", scrape_cricbuzz_profile(profile_url)
        return "profile_snippets", search_ddg(f"{player_name} cricket profile stats", 4)

    def _fetch_recent_form() -> tuple[str, Any]:
        return "recent_form", search_ddg(
            f"{player_name} cricket {match_format} recent matches scores 2024 2025 2026", 5
        )

    def _fetch_head_to_head() -> tuple[str, Any]:
        return "head_to_head", search_ddg(
            f"{player_name} vs {opposition} cricket {match_format} head to head stats records", 5
        )

    def _fetch_pitch_report() -> tuple[str, Any]:
        return "pitch_report", search_ddg(
            f"{venue} cricket pitch report conditions {match_format} stats batting bowling", 5
        )

    def _fetch_env_conditions() -> tuple[str, Any]:
        return "environmental_conditions", build_environmental_conditions(
            venue,
            match_date or date.today().isoformat(),
            is_day_night,
            match_format=match_format,
        )

    def _fetch_opposition_bowlers() -> tuple[str, Any]:
        return "opposition_bowlers", search_ddg(
            f"{opposition} cricket team bowlers key players wicket-takers {match_format} 2025 2026", 5
        )

    def _fetch_venue_form() -> tuple[str, Any]:
        return "venue_form", search_ddg(
            f"{player_name} cricket stats scores records at {venue} {match_format}", 5
        )

    tasks = [
        _fetch_profile,
        _fetch_recent_form,
        _fetch_head_to_head,
        _fetch_venue_form,
        _fetch_pitch_report,
        _fetch_env_conditions,
        _fetch_opposition_bowlers,
    ]

    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = {pool.submit(fn): fn.__name__ for fn in tasks}
        for future in as_completed(futures):
            try:
                key, value = future.result()
                ctx[key] = value
            except Exception as exc:  # noqa: BLE001
                logger.warning("Parallel fetch '%s' failed: %s", futures[future], exc)

    _cb("✅ All data gathered — building AI prediction prompt...")
    return ctx


# ---------------------------------------------------------------------------
# Rate-limit / quota error classifier
# ---------------------------------------------------------------------------

def _classify_api_error(status_code: int, body_text: str) -> dict | None:
    """Inspect an OpenRouter error response and return a structured error dict
    if it is a rate-limit, quota, or payment issue.  Returns None for other errors.
    """
    body_lower = body_text.lower()

    # --- HTTP 429  Too Many Requests ---
    if status_code == 429:
        if "free" in body_lower or "limit" in body_lower:
            return {
                "error_type": "rate_limit",
                "error": (
                    "🚫 Rate Limit Reached — Your free-tier API quota has been exhausted for today.\n\n"
                    "What you can do:\n"
                    "• Wait and try again tomorrow — free-tier limits reset every 24 hours.\n"
                    "• Switch to a different free model from the model dropdown (each model has its own quota).\n"
                    "• Replace your OpenRouter API key in the backend .env file with a fresh one "
                    "(create a new key at https://openrouter.ai/keys).\n"
                    "• Upgrade to a paid LLM API key on OpenRouter for unlimited usage."
                ),
            }
        return {
            "error_type": "rate_limit",
            "error": (
                "🚫 Too Many Requests (429) — The AI model is temporarily rate-limiting your requests.\n\n"
                "Try again in a few minutes, or switch to a different model from the dropdown."
            ),
        }

    # --- HTTP 402  Payment Required / credits exhausted ---
    if status_code == 402:
        return {
            "error_type": "quota_exceeded",
            "error": (
                "💳 API Credits Exhausted — Your OpenRouter account has no remaining credits.\n\n"
                "What you can do:\n"
                "• Switch to a free model (marked with ✅ in the model dropdown).\n"
                "• Add credits to your OpenRouter account at https://openrouter.ai/credits.\n"
                "• Replace your API key with one that has a paid plan."
            ),
        }

    # --- HTTP 403  Forbidden (invalid key, suspended, etc.) ---
    if status_code == 403:
        return {
            "error_type": "auth_error",
            "error": (
                "🔑 API Key Error (403 Forbidden) — Your OpenRouter API key was rejected.\n\n"
                "• Double-check the OPENROUTER_API_KEY in your backend .env file.\n"
                "• Generate a new key at https://openrouter.ai/keys if the current one is revoked."
            ),
        }

    # --- Body-text heuristics for other status codes ---
    rate_keywords = ["rate limit", "rate_limit", "too many request", "quota", "exceeded", "throttl"]
    if any(kw in body_lower for kw in rate_keywords):
        return {
            "error_type": "rate_limit",
            "error": (
                "🚫 Rate Limit / Quota Issue — The AI provider has limited your requests.\n\n"
                "What you can do:\n"
                "• Wait a few minutes and try again.\n"
                "• Switch to a different model from the dropdown.\n"
                "• Use a fresh API key or upgrade to a paid plan at https://openrouter.ai."
            ),
        }

    payment_keywords = ["payment", "billing", "credits", "insufficient", "balance"]
    if any(kw in body_lower for kw in payment_keywords):
        return {
            "error_type": "payment_required",
            "error": (
                "💳 Payment / Billing Issue — Your API account requires payment or has insufficient credits.\n\n"
                "• Switch to a free model (marked with ✅ in the model dropdown).\n"
                "• Add credits at https://openrouter.ai/credits.\n"
                "• Or use a different API key with available balance."
            ),
        }

    return None  # Not a rate-limit / quota error


# ---------------------------------------------------------------------------
# LLM Predictor (Google Gemini & OpenRouter with automatic fallback)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a world-class cricket analyst and performance prediction engine. "
    "Your analysis is data-driven, deeply informed by a player's career stats, "
    "recent form, head-to-head records, pitch conditions and opponent bowling quality. "
    "Always respond with a single raw JSON object — no markdown wrapper, no extra text."
)

def _call_gemini_direct(prompt: str, gemini_key: str, model_name: str = "gemini-3.6-flash") -> tuple[int, str]:
    """Call Google Gemini Generative Language API directly."""
    # Strip any prefix like google/ or models/ if passed
    clean_model = model_name
    if "/" in clean_model:
        clean_model = clean_model.split("/")[-1]
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={gemini_key}"
    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code == 200:
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts and "text" in parts[0]:
                return 200, parts[0]["text"]
        return 500, f"Malformed Gemini response: {resp.text[:300]}"
    return resp.status_code, resp.text

def _call_openrouter(prompt: str, openrouter_key: str, model_name: str) -> tuple[int, str]:
    """Call OpenRouter Chat Completions API."""
    or_headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "HTTP-Referer": "https://cricket-predictor.ai",
        "X-Title": "Elite Cricket Player Predictor",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=or_headers,
        json=payload,
        timeout=60,
    )
    if resp.status_code == 200:
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        return 200, raw
    return resp.status_code, resp.text

def execute_llm_prediction(
    prompt: str,
    requested_model: str,
    openrouter_key: str = "",
    gemini_key: str = "",
    status_cb: Callable[[str], None] | None = None,
) -> tuple[int, str, str]:
    """
    Executes prediction with intelligent routing:
    - If model is a Gemini direct model (e.g. 'gemini-3.6-flash', 'gemini-2.5-flash', or starts with 'gemini-'):
      Uses Google Gemini API first; falls back to OpenRouter if configured.
    - If model is an OpenRouter model:
      Uses OpenRouter first; falls back to Gemini if OpenRouter is out of credits / rate-limited.
    Returns: (status_code, text_result_or_error, provider_used)
    """
    def _log(m: str) -> None:
        if status_cb:
            status_cb(m)

    is_gemini_direct = (
        requested_model.startswith("gemini-")
        or requested_model == "google/gemini-3.6-flash"
        or requested_model == "google/gemini-2.5-flash"
    )

    err = ""
    err_status = 500
    provider_used = "AI Model"

    # Strategy 1: User requested Gemini direct or default
    if is_gemini_direct and gemini_key:
        _log(f"⚡ Querying Google Gemini ({requested_model})...")
        status, text = _call_gemini_direct(prompt, gemini_key, requested_model)
        if status == 200:
            return 200, text, "Google Gemini"
        err_status, err, provider_used = status, text, "Google Gemini"
        _log(f"⚠️ Gemini returned HTTP {status}. Attempting fallback to OpenRouter...")

        if openrouter_key:
            or_model = "google/gemini-2.5-flash"
            _log(f"🔄 Switching to fallback provider: OpenRouter ({or_model})...")
            status, text = _call_openrouter(prompt, openrouter_key, or_model)
            if status == 200:
                return 200, text, "OpenRouter (Fallback)"
            err_status, err, provider_used = status, text, "OpenRouter"

    # Strategy 2: OpenRouter requested
    elif openrouter_key:
        _log(f"🤖 Querying OpenRouter ({requested_model})...")
        status, text = _call_openrouter(prompt, openrouter_key, requested_model)
        if status == 200:
            return 200, text, "OpenRouter"
        err_status, err, provider_used = status, text, "OpenRouter"
        _log(f"⚠️ OpenRouter returned HTTP {status}...")

        # Fallback to Gemini if OpenRouter failed and Gemini key is available
        if gemini_key:
            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
            _log(f"🔄 Switching to fallback provider: Google Gemini ({gemini_model})...")
            status, text = _call_gemini_direct(prompt, gemini_key, gemini_model)
            if status == 200:
                return 200, text, "Google Gemini (Fallback)"
            err_status, err, provider_used = status, text, "Google Gemini"

    # If both failed or missing keys
    if not err:
        err = "No valid API keys configured (OPENROUTER_API_KEY or GEMINI_API_KEY)."
        err_status = 400
        provider_used = "Config"
    return err_status, err, provider_used


PREDICTION_SCHEMA = """
Output a single raw JSON object with EXACTLY these top-level keys:
{
  "player_name": "string",
  "role": "batsman" | "bowler" | "all-rounder",
  "visual_tagline": "One punchy sentence summarising the prediction",
  "reasoning_markdown": "Multi-paragraph markdown analysis covering: career record, recent form, head-to-head vs this opposition, how the pitch conditions affect this player, the quality/type of opposition bowlers/batters, and your overall verdict. Use **bold** for emphasis.",
  "batsman_prediction": {
    "predicted_runs_range": "e.g. 45 to 70",
    "who_can_get_him_out": "Comma-separated bowler names with brief reason",
    "possible_mode_of_dismissal": "e.g. Caught behind off outswing, or LBW to off-break",
    "possible_threats": "Describe the main bowling/pitch threats in detail",
    "bowling_weakness": ["list of bowling types he struggles against"],
    "bowling_strength": ["list of bowling types he dominates"],
    "length_weakness": ["list of lengths/deliveries he is weak to"],
    "length_strength": ["list of lengths/deliveries he handles well"],
    "phase_impact": {
      "powerplay_pct": "number 0-100 indicating predicted success/impact in overs 1-6",
      "middle_pct": "number 0-100 indicating predicted success/impact in overs 7-15",
      "death_pct": "number 0-100 indicating predicted success/impact in overs 16-20"
    },
    "shot_distribution": [
      { "shot_name": "Cover Drive", "sector": "Cover", "efficiency": "strength" },
      { "shot_name": "Pull Shot", "sector": "Mid-Wicket", "efficiency": "strength" },
      { "shot_name": "Edge / Cut", "sector": "Third Man", "efficiency": "weakness" }
    ],
    "venue_performance_history": [
      "list of recent 3-5 scores or bowling figures by this player at this specific venue"
    ]
  },
  "bowler_prediction": {
    "predicted_wickets": "e.g. 2-3 wickets",
    "predicted_economy": "e.g. 6.8 runs/over",
    "success_rate": "e.g. Strike rate ~22 balls/wicket",
    "kind_of_ball_will_bowl": "Describe the primary delivery types this bowler will use",
    "success_rate_vs_batters": "Name the opposition batters he is most/least likely to trouble and why",
    "role_in_match": "e.g. Open the bowling and bowl 2 death overs, or Defensive mid-overs role",
    "venue_performance_history": [
      "list of recent 3-5 bowling figures by this player at this specific venue"
    ],
    "delivery_types": [
      { "type": "Outswing", "percentage": 35, "avg_speed_kph": 142 },
      { "type": "Bouncer", "percentage": 20, "avg_speed_kph": 148 },
      { "type": "Yorker", "percentage": 15, "avg_speed_kph": 140 },
      { "type": "Slower Ball", "percentage": 10, "avg_speed_kph": 118 },
      { "type": "Off-cutter", "percentage": 20, "avg_speed_kph": 130 }
    ],
    "pitch_zones": [
      { "zone": "good_length", "percentage": 40, "wicket_pct": 50 },
      { "zone": "short", "percentage": 25, "wicket_pct": 20 },
      { "zone": "yorker", "percentage": 15, "wicket_pct": 20 },
      { "zone": "full", "percentage": 15, "wicket_pct": 8 },
      { "zone": "half_volley", "percentage": 5, "wicket_pct": 2 }
    ],
    "phase_bowling": {
      "powerplay_economy": "number — predicted economy rate in overs 1-6",
      "middle_economy": "number — predicted economy rate in overs 7-15",
      "death_economy": "number — predicted economy rate in overs 16-20"
    }
  },
  "conditions_impact": {
    "pitch_reading": "Your interpretation of how this specific pitch type and ground dimensions affect this player",
    "weather_dew_note": "How the temperature/humidity/wind/dew factor specifically affects this player's performance tonight (e.g. dew helping a chasing batsman, or hurting a spinner's grip)",
    "ground_dimension_note": "How the boundary dimensions affect this player's shot-making or bowling plans"
  },
  "test_match_innings_breakdown": {
    "first_innings": {
      "predicted_performance": "e.g. 60 to 95 runs or 2-3 wickets",
      "pitch_condition": "Fresh Day 1-2 pitch behavior (seam, bounce, pace)",
      "weather_impact": "Overhead clouds & morning moisture impact",
      "tactical_plan": "Specific tactical approach for 1st innings"
    },
    "second_innings": {
      "predicted_performance": "e.g. 40 to 70 runs or 3-4 wickets",
      "pitch_condition": "Day 4-5 deteriorated pitch, cracks & variable bounce",
      "weather_impact": "Drier conditions & footmarks aiding spin",
      "tactical_plan": "Specific tactical approach for 2nd innings / 4th innings chase"
    },
    "pitch_deterioration_summary": "Summary of how 5-day pitch wear & cracks affect this player",
    "day_by_day_breakdown": [
      { "days": "Day 1-2", "pitch_state": "Hard & Seaming", "key_factor": "Seam & Bounce" },
      { "days": "Day 3", "pitch_state": "Settled & Batting Friendly", "key_factor": "True Bounce & High Scoring" },
      { "days": "Day 4-5", "pitch_state": "Cracked & Dusty", "key_factor": "Variable Bounce & Sharp Spin" }
    ]
  }
}

Rules:
- If the player is NOT a batsman (pure bowler), set "batsman_prediction" to null.
- If the player is NOT a bowler (pure batsman), set "bowler_prediction" to null.
- The "conditions_impact" key and all its inner fields must always be populated (not null), since environmental data is always available (even if partially synthetic/estimated).
- For an all-rounder, provide BOTH sections fully.
- All string values must be properly escaped; use \\n for newlines inside strings.
- Return ONLY the raw JSON — no ```json wrapper, no introductory sentence.
"""


def _build_prompt(player_name: str, opposition: str, venue: str, ctx: dict, match_format: str = "T20") -> str:
    lines: list[str] = []
    lines.append(f"=== PREDICTION REQUEST ===")
    lines.append(f"PLAYER: {player_name}")
    lines.append(f"OPPOSITION: {opposition}")
    lines.append(f"VENUE: {venue}")
    lines.append(f"MATCH FORMAT: {match_format}")
    lines.append("")
    lines.append(f"--- MATCH FORMAT DIRECTIVE ---")
    lines.append(f"Target Format: {match_format}")
    lines.append(f"• TEST MATCH: Evaluate for multi-day endurance, patience, high runs range expectation (e.g., 55 to 110 runs across match), defensive technique against seam/spin.")
    lines.append(f"• ODI MATCH: Evaluate for 50-over building & acceleration, moderate runs range (e.g., 40 to 80 runs), strike rate ~85-100.")
    lines.append(f"• T20 MATCH: Evaluate for 20-over powerplay/death boundary hitting, runs range (e.g., 25 to 55 runs), high strike rate 135+.")
    lines.append("")

    # Career profile
    pd = ctx.get("profile_data", {})
    if pd and "error" not in pd:
        lines.append("--- CAREER PROFILE (Cricbuzz) ---")
        lines.append(
            f"Name: {pd.get('name')} | Role: {pd.get('role')} | "
            f"Country: {pd.get('country')} | DoB: {pd.get('dob')} | "
            f"Bat: {pd.get('bat_style')} | Bowl: {pd.get('bowl_style')}"
        )
        bat = pd.get("batting_summary", {})
        if bat and "headers" in bat:
            lines.append("BATTING CAREER SUMMARY:")
            lines.append(" | ".join(bat["headers"]))
            for row in bat.get("rows", []):
                lines.append(" | ".join(str(x) for x in row))
        bowl = pd.get("bowling_summary", {})
        if bowl and "headers" in bowl:
            lines.append("BOWLING CAREER SUMMARY:")
            lines.append(" | ".join(bowl["headers"]))
            for row in bowl.get("rows", []):
                lines.append(" | ".join(str(x) for x in row))
        rb = pd.get("recent_batting", {})
        if rb and rb.get("rows"):
            lines.append("RECENT BATTING SCORES (last 5):")
            for row in rb["rows"][:5]:
                lines.append("  " + " | ".join(str(x) for x in row))
        rbwl = pd.get("recent_bowling", {})
        if rbwl and rbwl.get("rows"):
            lines.append("RECENT BOWLING FIGURES (last 5):")
            for row in rbwl["rows"][:5]:
                lines.append("  " + " | ".join(str(x) for x in row))
    elif "profile_snippets" in ctx:
        lines.append("--- CAREER PROFILE (search snippets) ---")
        for s in ctx["profile_snippets"]:
            lines.append(f"• {s['title']}: {s['snippet']}")

    def _add_section(title: str, key: str) -> None:
        items = ctx.get(key, [])
        if not items:
            return
        lines.append(f"\n--- {title} ---")
        for s in items:
            lines.append(f"• {s.get('title','')}: {s.get('snippet','')}")

    _add_section("RECENT FORM (web)", "recent_form")
    _add_section("HEAD-TO-HEAD vs OPPOSITION (web)", "head_to_head")
    _add_section(f"PLAYER'S RECENT SCORES & PERFORMANCE AT THIS SPECIFIC VENUE ({venue})", "venue_form")
    _add_section("PITCH & VENUE CONDITIONS (web)", "pitch_report")
    
    env = ctx.get("environmental_conditions", {})
    if env:
        lines.append("\n--- MATCH-DAY ENVIRONMENTAL CONDITIONS ---")
        day_temp = f"{env.get('day_temp_c')}°C" if env.get("day_temp_c") is not None else "unknown"
        night_temp = f"{env.get('night_temp_c')}°C" if env.get("night_temp_c") is not None else "unknown"
        humidity = f"{env.get('humidity_pct')}%" if env.get("humidity_pct") is not None else "unknown"
        wind = f"{env.get('wind_speed_kmh')} km/h" if env.get("wind_speed_kmh") is not None else "unknown"
        dew = f"{env.get('dew_factor')}" if env.get("dew_factor") is not None else "unknown"
        pitch = f"{env.get('pitch_type')}" if env.get("pitch_type") is not None else "unknown"
        batting_friendliness = f"{env.get('pitch_batting_friendliness')}" if env.get("pitch_batting_friendliness") is not None else "unknown"
        straight = f"{env.get('straight_boundary_m')}m" if env.get("straight_boundary_m") is not None else "unknown"
        square = f"{env.get('square_boundary_m')}m" if env.get("square_boundary_m") is not None else "unknown"
        avg_score = f"{env.get('venue_avg_score')}" if env.get("venue_avg_score") is not None else "unknown"
        
        lines.append(f"Day temp: {day_temp} | Night temp: {night_temp} |")
        lines.append(f"Humidity: {humidity} | Wind: {wind}")
        lines.append(f"Estimated dew factor: {dew} (0=none, 1=heavy dew — favors the chasing team and hurts bowlers' grip)")
        lines.append(f"Pitch type: {pitch} (batting-friendliness: {batting_friendliness})")
        lines.append(f"Ground dimensions: straight boundary {straight}, square boundary {square}")
        lines.append(f"Venue historical average score: {avg_score}")

    _add_section("OPPOSITION BOWLING ATTACK (web)", "opposition_bowlers")

    lines.append("")
    lines.append(PREDICTION_SCHEMA)
    return "\n".join(lines)


def predict_real_player(
    player_name: str,
    opposition: str,
    venue: str,
    api_key: str = "",
    match_format: str = "T20",
    model_name: str = "gemini-3.6-flash",
    status_callback: Callable[[str], None] | None = None,
    match_date: str | None = None,
    is_day_night: bool | None = None,
) -> dict:
    """
    End-to-end: scrape context → build prompt → call OpenRouter → return parsed dict.
    Returns a dict that always contains 'scraped_context' and 'contextual_factors'.
    On error, also contains 'error'.
    """

    def _cb(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    # 1. Collect context
    ctx = collect_player_match_context(
        player_name=player_name,
        opposition=opposition,
        venue=venue,
        match_format=match_format,
        status_callback=status_callback,
        match_date=match_date,
        is_day_night=is_day_night
    )

    _cb("🤖 Building prediction prompt and querying AI model...")

    prompt = _build_prompt(player_name, opposition, venue, ctx, match_format)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    status_code, response_text, provider_used = execute_llm_prediction(
        prompt=prompt,
        requested_model=model_name,
        openrouter_key=api_key,
        gemini_key=gemini_key,
        status_cb=_cb,
    )

    try:
        if status_code != 200:
            classified = _classify_api_error(status_code, response_text[:1000])
            if classified:
                _cb(f"⚠️ {classified['error_type'].replace('_', ' ').title()} error detected.")
                return {
                    **classified,
                    "scraped_context": ctx,
                    "contextual_factors": ctx.get("environmental_conditions", {}),
                }
            err = f"{provider_used} returned HTTP {status_code}: {response_text[:400]}"
            return {
                "error": err,
                "error_type": "api_error",
                "scraped_context": ctx,
                "contextual_factors": ctx.get("environmental_conditions", {}),
            }

        raw = response_text.strip()
        # Strip optional markdown code-fence wrapper
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw.strip())

        result = json.loads(raw)
        result["scraped_context"] = ctx
        result["contextual_factors"] = ctx.get("environmental_conditions", {})
        _cb("✅ Prediction complete!")
        return result

    except json.JSONDecodeError as exc:
        return {
            "error": f"Failed to parse LLM JSON response: {exc}",
            "raw_response": raw if "raw" in dir() else "",  # type: ignore[name-defined]
            "scraped_context": ctx,
            "contextual_factors": ctx.get("environmental_conditions", {})
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "error": str(exc),
            "scraped_context": ctx,
            "contextual_factors": ctx.get("environmental_conditions", {})
        }


# ---------------------------------------------------------------------------
# Squad match predictor and parsing
# ---------------------------------------------------------------------------

def parse_cricbuzz_squad(url: str) -> dict:
    """
    Fetch a Cricbuzz squad URL and return team squads, venue, series, etc.
    URL format: https://www.cricbuzz.com/cricket-match-squads/129563/eng-vs-nz-2nd-test-new-zealand-tour-of-england-2026
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code} fetching {url}"}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Parse team names from the tabs header (bg-cbInactTab)
        tab_div = soup.find("div", class_=re.compile(r"bg-cbInactTab"))
        team1, team2 = "Team 1", "Team 2"
        if tab_div:
            h1_tags = tab_div.find_all("h1", class_=re.compile(r"font-bold"))
            if len(h1_tags) >= 2:
                team1 = h1_tags[0].get_text(strip=True)
                team2 = h1_tags[1].get_text(strip=True)
        else:
            # Fallback team names from page title
            title_str = soup.title.string if soup.title and soup.title.string else ""
            if "|" in title_str and "," in title_str:
                teams_part = title_str.split("|")[1].split(",")[0].strip()
                if " vs " in teams_part:
                    t_split = teams_part.split(" vs ")
                    team1, team2 = t_split[0].strip(), t_split[1].strip()
        
        # 2. Extract series and venue details using regex
        venue, series = "Unknown Venue", "Unknown Series"
        info_divs = soup.find_all("div", class_=re.compile(r"flex-wrap"))
        for div in info_divs:
            txt = div.get_text()
            if "Venue:" in txt:
                # Normalize non-breaking spaces and bullet separators
                clean_txt = (
                    txt
                    .replace('\xa0', ' ')
                    .replace('\u00a0', ' ')
                    .replace('\u2022', '|')   # bullet •
                    .replace('\u00b7', '|')   # middle dot ·
                )
                venue_match = re.search(r"Venue:\s*(.*?)(?:\s*[|]\s*Date|\s+Date &|\s+Time:|$)", clean_txt)
                series_match = re.search(r"Series:\s*(.*?)(?:\s*[|]\s*Venue:|\s+Venue:|$)", clean_txt)
                if venue_match:
                    venue = venue_match.group(1).strip().rstrip('•·|').strip()
                if series_match:
                    series = series_match.group(1).strip().rstrip('•·|').strip()
                break
        
        # 3. Extract player squads from pb-5 divs
        pb5_divs = soup.find_all("div", class_=re.compile(r"\bpb-5\b"))
        squad1, squad2 = [], []
        
        for div in pb5_divs:
            header_text = div.get_text(strip=True).lower()
            if "playing xi" in header_text:
                status = "Playing XI"
            elif "bench" in header_text:
                status = "Bench"
            elif "squad" in header_text:
                status = "Squad"
            else:
                continue
                
            flex_div = div.find("div", class_=re.compile(r"\bflex\b"))
            if flex_div:
                cols = flex_div.find_all("div", class_=re.compile(r"w-1/2"), recursive=False)
                if len(cols) >= 2:
                    def _is_player_link(href: str) -> bool:
                        return "/profiles/" in href or "/cricket-player-profile/" in href

                    def _extract_profile(a_tag) -> dict | None:
                        href = a_tag.get("href", "")
                        if not _is_player_link(href):
                            return None
                        # Normalise /cricket-player-profile/ID/name  ->  /profiles/name-ID
                        if "/cricket-player-profile/" in href:
                            parts = href.split("/cricket-player-profile/", 1)[1].split("/")
                            if len(parts) >= 2:
                                pid, pname = parts[0], parts[1]
                                href = f"/profiles/{pname}-{pid}"
                        name = ""
                        for span in a_tag.find_all("span"):
                            txt = span.get_text(strip=True)
                            if txt:
                                name = txt
                                break
                        if not name:
                            name = a_tag.get_text(strip=True)
                        role_div = a_tag.find("div", class_=re.compile(r"\btext-xs\b"))
                        role = role_div.get_text(strip=True) if role_div else ""
                        return {"name": name, "role": role, "href": href}

                    # Column 0 is Team 1
                    for a in cols[0].find_all("a", href=True):
                        p = _extract_profile(a)
                        if p:
                            squad1.append({**p, "status": status})

                    # Column 1 is Team 2
                    for a in cols[1].find_all("a", href=True):
                        p = _extract_profile(a)
                        if p:
                            squad2.append({**p, "status": status})

                            
        return {
            "team1": team1,
            "team2": team2,
            "squad1": squad1,
            "squad2": squad2,
            "venue": venue,
            "series": series,
            "url": url,
        }
    except Exception as exc:
        return {"error": f"parse_cricbuzz_squad failed: {exc}"}


def collect_player_match_context_squad(
    player_name: str,
    player_profile_url: str,
    opposition_team: str,
    opponent_squad: list[dict],
    match_format: str,
    venue: str,
    status_callback: Callable[[str], None] | None = None,
    match_date: str | None = None,
    is_day_night: bool | None = None,
) -> dict:
    """
    Run targeted web searches and scrape direct profile details to assemble
    a highly detailed context for the player matchup.
    All independent I/O tasks run in parallel to minimise latency.
    """
    def _cb(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    ctx: dict[str, Any] = {}

    # Normalise profile URL early so the closure captures the correct value
    if player_profile_url and player_profile_url.startswith("/"):
        player_profile_url = "https://www.cricbuzz.com" + player_profile_url

    _cb(
        f"\u26a1 Parallel data gathering: Cricbuzz profile, recent {match_format} form, "
        f"head-to-head vs {opposition_team}, {venue} pitch + weather, opposition analysis..."
    )

    def _fetch_profile() -> tuple[str, Any]:
        if player_profile_url:
            return "profile_data", scrape_cricbuzz_profile(player_profile_url)
        return "profile_snippets", search_ddg(f"{player_name} cricket profile stats", 4)

    def _fetch_recent_form() -> tuple[str, Any]:
        return "recent_form", search_ddg(
            f"{player_name} cricket recent matches scores {match_format} 2025 2026", 5
        )

    def _fetch_head_to_head() -> tuple[str, Any]:
        return "head_to_head", search_ddg(
            f"{player_name} vs {opposition_team} cricket head to head stats records {match_format}", 5
        )

    def _fetch_pitch_report() -> tuple[str, Any]:
        return "pitch_report", search_ddg(
            f"{venue} cricket pitch report conditions stats batting bowling {match_format}", 5
        )

    def _fetch_env_conditions() -> tuple[str, Any]:
        return "environmental_conditions", build_environmental_conditions(
            venue,
            match_date or date.today().isoformat(),
            is_day_night,
            match_format=match_format,
        )

    def _fetch_opposition_bowlers() -> tuple[str, Any]:
        return "opposition_bowlers", search_ddg(
            f"{opposition_team} cricket team key players bowlers batters match analysis {match_format}", 5
        )

    def _fetch_venue_form() -> tuple[str, Any]:
        return "venue_form", search_ddg(
            f"{player_name} cricket stats scores records at {venue} {match_format}", 5
        )

    tasks = [
        _fetch_profile,
        _fetch_recent_form,
        _fetch_head_to_head,
        _fetch_venue_form,
        _fetch_pitch_report,
        _fetch_env_conditions,
        _fetch_opposition_bowlers,
    ]

    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = {pool.submit(fn): fn.__name__ for fn in tasks}
        for future in as_completed(futures):
            try:
                key, value = future.result()
                ctx[key] = value
            except Exception as exc:  # noqa: BLE001
                logger.warning("Parallel fetch '%s' failed: %s", futures[future], exc)

    # Opposition lineup is derived from the already-passed squad data — no extra I/O needed
    opp_names = [p["name"] for p in opponent_squad if p.get("name")]
    ctx["opposition_lineup"] = opp_names

    _cb("\u2705 All data gathered \u2014 building AI prediction prompt...")
    return ctx


def _build_prompt_squad(
    player_name: str,
    opposition: str,
    venue: str,
    match_format: str,
    ctx: dict
) -> str:
    lines: list[str] = []
    lines.append("=== PREDICTION REQUEST ===")
    lines.append(f"PLAYER: {player_name}")
    lines.append(f"OPPOSITION TEAM: {opposition}")
    lines.append(f"VENUE: {venue}")
    lines.append(f"MATCH FORMAT: {match_format}")
    
    if "opposition_lineup" in ctx:
        lines.append(f"OPPOSITION SQUAD ROSTER: {', '.join(ctx['opposition_lineup'])}")
    lines.append("")

    # Career profile
    pd = ctx.get("profile_data", {})
    if pd and "error" not in pd:
        lines.append("--- CAREER PROFILE (Cricbuzz) ---")
        lines.append(
            f"Name: {pd.get('name')} | Role: {pd.get('role')} | "
            f"Country: {pd.get('country')} | DoB: {pd.get('dob')} | "
            f"Bat: {pd.get('bat_style')} | Bowl: {pd.get('bowl_style')}"
        )
        bat = pd.get("batting_summary", {})
        if bat and "headers" in bat:
            lines.append("BATTING CAREER SUMMARY:")
            lines.append(" | ".join(bat["headers"]))
            for row in bat.get("rows", []):
                lines.append(" | ".join(str(x) for x in row))
        bowl = pd.get("bowling_summary", {})
        if bowl and "headers" in bowl:
            lines.append("BOWLING CAREER SUMMARY:")
            lines.append(" | ".join(bowl["headers"]))
            for row in bowl.get("rows", []):
                lines.append(" | ".join(str(x) for x in row))
        rb = pd.get("recent_batting", {})
        if rb and rb.get("rows"):
            lines.append("RECENT BATTING SCORES (last 5):")
            for row in rb["rows"][:5]:
                lines.append("  " + " | ".join(str(x) for x in row))
        rbwl = pd.get("recent_bowling", {})
        if rbwl and rbwl.get("rows"):
            lines.append("RECENT BOWLING FIGURES (last 5):")
            for row in rbwl["rows"][:5]:
                lines.append("  " + " | ".join(str(x) for x in row))
    elif "profile_snippets" in ctx:
        lines.append("--- CAREER PROFILE (search snippets) ---")
        for s in ctx["profile_snippets"]:
            lines.append(f"• {s['title']}: {s['snippet']}")

    def _add_section(title: str, key: str) -> None:
        items = ctx.get(key, [])
        if not items:
            return
        lines.append(f"\n--- {title} ---")
        for s in items:
            lines.append(f"• {s.get('title','')}: {s.get('snippet','')}")

    _add_section(f"RECENT FORM IN {match_format} (web)", "recent_form")
    _add_section(f"HEAD-TO-HEAD vs OPPOSITION IN {match_format} (web)", "head_to_head")
    _add_section(f"PLAYER'S RECENT SCORES & PERFORMANCE AT THIS SPECIFIC VENUE ({venue})", "venue_form")
    _add_section(f"PITCH & VENUE CONDITIONS FOR {match_format} (web)", "pitch_report")
    
    env = ctx.get("environmental_conditions", {})
    if env:
        lines.append("\n--- MATCH-DAY ENVIRONMENTAL CONDITIONS ---")
        day_temp = f"{env.get('day_temp_c')}°C" if env.get("day_temp_c") is not None else "unknown"
        night_temp = f"{env.get('night_temp_c')}°C" if env.get("night_temp_c") is not None else "unknown"
        humidity = f"{env.get('humidity_pct')}%" if env.get("humidity_pct") is not None else "unknown"
        wind = f"{env.get('wind_speed_kmh')} km/h" if env.get("wind_speed_kmh") is not None else "unknown"
        dew = f"{env.get('dew_factor')}" if env.get("dew_factor") is not None else "unknown"
        pitch = f"{env.get('pitch_type')}" if env.get("pitch_type") is not None else "unknown"
        batting_friendliness = f"{env.get('pitch_batting_friendliness')}" if env.get("pitch_batting_friendliness") is not None else "unknown"
        straight = f"{env.get('straight_boundary_m')}m" if env.get("straight_boundary_m") is not None else "unknown"
        square = f"{env.get('square_boundary_m')}m" if env.get("square_boundary_m") is not None else "unknown"
        avg_score = f"{env.get('venue_avg_score')}" if env.get("venue_avg_score") is not None else "unknown"
        
        lines.append(f"Day temp: {day_temp} | Night temp: {night_temp} |")
        lines.append(f"Humidity: {humidity} | Wind: {wind}")
        lines.append(f"Estimated dew factor: {dew} (0=none, 1=heavy dew — favors the chasing team and hurts bowlers' grip)")
        lines.append(f"Pitch type: {pitch} (batting-friendliness: {batting_friendliness})")
        lines.append(f"Ground dimensions: straight boundary {straight}, square boundary {square}")
        lines.append(f"Venue historical average score: {avg_score}")

    _add_section("OPPOSITION BOWLING/BATTING ATTACK DETAILS (web)", "opposition_bowlers")

    lines.append("")
    lines.append(PREDICTION_SCHEMA)
    return "\n".join(lines)


def predict_real_player_squad(
    player_name: str,
    player_role: str,
    player_profile_url: str,
    opposition_team: str,
    opponent_squad: list[dict],
    match_format: str,
    venue: str,
    api_key: str = "",
    model_name: str = "gemini-3.6-flash",
    status_callback: Callable[[str], None] | None = None,
    match_date: str | None = None,
    is_day_night: bool | None = None,
) -> dict:
    """
    End-to-end squad prediction flow: collect context -> build prompt -> call OpenRouter LLM.
    """
    def _cb(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    # 1. Collect context
    ctx = collect_player_match_context_squad(
        player_name=player_name,
        player_profile_url=player_profile_url,
        opposition_team=opposition_team,
        opponent_squad=opponent_squad,
        match_format=match_format,
        venue=venue,
        status_callback=status_callback,
        match_date=match_date,
        is_day_night=is_day_night
    )

    _cb("🤖 Building prediction prompt and querying AI model...")

    prompt = _build_prompt_squad(
        player_name=player_name,
        opposition=opposition_team,
        venue=venue,
        match_format=match_format,
        ctx=ctx
    )

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    status_code, response_text, provider_used = execute_llm_prediction(
        prompt=prompt,
        requested_model=model_name,
        openrouter_key=api_key,
        gemini_key=gemini_key,
        status_cb=_cb,
    )

    raw = ""
    try:
        if status_code != 200:
            classified = _classify_api_error(status_code, response_text[:1000])
            if classified:
                _cb(f"⚠️ {classified['error_type'].replace('_', ' ').title()} error detected.")
                return {
                    **classified,
                    "scraped_context": ctx,
                    "contextual_factors": ctx.get("environmental_conditions", {}),
                }
            err = f"{provider_used} returned HTTP {status_code}: {response_text[:400]}"
            return {
                "error": err,
                "error_type": "api_error",
                "scraped_context": ctx,
                "contextual_factors": ctx.get("environmental_conditions", {})
            }

        raw = response_text.strip()

        # Strip optional markdown code-fence wrapper
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw.strip())

        result = json.loads(raw)
        result["scraped_context"] = ctx
        result["contextual_factors"] = ctx.get("environmental_conditions", {})
        _cb("✅ Prediction complete!")
        return result

    except json.JSONDecodeError as exc:
        return {
            "error": f"Failed to parse LLM JSON response: {exc}",
            "raw_response": raw if "raw" in dir() else "",
            "scraped_context": ctx,
            "contextual_factors": ctx.get("environmental_conditions", {})
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "error": str(exc),
            "scraped_context": ctx,
            "contextual_factors": ctx.get("environmental_conditions", {})
        }
