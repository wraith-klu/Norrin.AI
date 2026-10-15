"""
tests/test_realtime.py
Verifies the DuckDuckGo search utility and Cricbuzz scraper work end-to-end.
Run:  python tests/test_realtime.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.realtime_cricket import (
    search_ddg,
    scrape_cricbuzz_profile,
    find_cricbuzz_profile_url,
    collect_player_match_context,
    parse_cricbuzz_squad,
    build_environmental_conditions,
)

SEPARATOR = "-" * 60
CRICBUZZ_VIRAT = "https://www.cricbuzz.com/profiles/1413/virat-kohli"
CRICBUZZ_SQUAD_NEW = "https://www.cricbuzz.com/cricket-match-squads/153761/ban-vs-aus-2nd-t20i-australia-tour-of-bangladesh-2026"
CRICBUZZ_SQUAD_OLD = "https://www.cricbuzz.com/cricket-match-squads/129563/eng-vs-nz-2nd-test-new-zealand-tour-of-england-2026"


def test_search_ddg():
    print("\n" + SEPARATOR)
    print("TEST: search_ddg")
    results = search_ddg("Virat Kohli cricket", num_results=3)
    if not results:
        print("  WARN: DDG returned 0 results (likely rate limited). Skipping assertions.")
        return
    assert isinstance(results, list), "Expected list"
    r0 = results[0]
    for key in ("title", "url", "snippet"):
        assert key in r0, f"Result missing key '{key}'"
    print(f"  OK -- {len(results)} results, first: {r0['title'][:60]}")


def test_scrape_cricbuzz_profile():
    print("\n" + SEPARATOR)
    print("TEST: scrape_cricbuzz_profile (direct URL)")
    data = scrape_cricbuzz_profile(CRICBUZZ_VIRAT)
    assert "error" not in data, f"Scrape error: {data.get('error')}"
    assert data.get("name") == "Virat Kohli", f"Wrong name: {data.get('name')}"
    assert data.get("role"), "Expected role field"
    bat = data.get("batting_summary", {})
    assert bat.get("headers"), "Expected batting headers"
    assert bat.get("rows"), "Expected batting rows"
    bowl = data.get("bowling_summary", {})
    assert bowl.get("headers"), "Expected bowling headers"
    print(f"  OK -- Role: {data['role']}, Batting rows: {len(bat['rows'])}, Bowling rows: {len(bowl.get('rows', []))}")


def test_find_cricbuzz_url():
    print("\n" + SEPARATOR)
    print("TEST: find_cricbuzz_profile_url")
    url = find_cricbuzz_profile_url("Virat Kohli")
    if url is None:
        print("  WARN: Could not find Cricbuzz URL via DDG (rate limited?). Skipping URL assertion.")
        return
    assert "cricbuzz.com/profiles/" in url, f"Bad URL: {url}"
    print(f"  OK -- {url}")


def test_collect_context():
    print("\n" + SEPARATOR)
    print("TEST: collect_player_match_context")
    ctx = collect_player_match_context("Virat Kohli", "Pakistan", "Melbourne Cricket Ground")
    assert isinstance(ctx, dict), "Expected dict"
    for key in ("recent_form", "head_to_head", "pitch_report", "opposition_bowlers"):
        assert key in ctx, f"Context missing '{key}'"
    has_profile = "profile_data" in ctx or "profile_snippets" in ctx
    assert has_profile, "Context must have profile_data or profile_snippets"
    if "profile_data" in ctx and "error" not in ctx["profile_data"]:
        print(f"  OK -- Profile: {ctx['profile_data'].get('name')}, Keys: {list(ctx.keys())}")
    else:
        print(f"  OK -- Keys: {list(ctx.keys())} (profile via snippets)")


def test_parse_cricbuzz_squad():
    print("\n" + SEPARATOR)
    print("TEST: parse_cricbuzz_squad")
    for name, url in [("NEW", CRICBUZZ_SQUAD_NEW), ("OLD", CRICBUZZ_SQUAD_OLD)]:
        data = parse_cricbuzz_squad(url)
        assert "error" not in data, f"Error parsing {name} squad: {data.get('error')}"
        assert data.get("team1"), f"Missing team1 for {name} squad"
        assert data.get("team2"), f"Missing team2 for {name} squad"
        assert data.get("squad1"), f"Missing squad1 for {name} squad"
        assert data.get("squad2"), f"Missing squad2 for {name} squad"
        # Since OLD is 2026 Test, it might not be played yet or might have playing XI/bench, or full squads
        # Regardless, there should be parsed players in both squads
        assert len(data["squad1"]) > 0, f"squad1 is empty for {name} squad"
        assert len(data["squad2"]) > 0, f"squad2 is empty for {name} squad"
        print(f"  OK {name} -- Team1: {data['team1']} ({len(data['squad1'])} players), Team2: {data['team2']} ({len(data['squad2'])} players)")


def test_build_environmental_conditions():
    print("\n" + SEPARATOR)
    print("TEST: test_build_environmental_conditions")
    from app.services.weather_service import resolve_venue_id

    # Test resolve_venue_id with real & fake strings
    vid_real = resolve_venue_id("Melbourne Cricket Ground")
    assert vid_real == "mcg", f"Expected 'mcg', got '{vid_real}'"

    vid_fake = resolve_venue_id("some totally made up stadium xyz123")
    assert vid_fake is None, f"Expected None, got '{vid_fake}'"

    # Test build_environmental_conditions
    cond = build_environmental_conditions("Melbourne Cricket Ground", "2026-08-01", True)
    assert isinstance(cond, dict)
    
    # 14 expected keys
    expected_keys = [
        "venue_id", "venue_name", "pitch_type", "pitch_batting_friendliness",
        "straight_boundary_m", "square_boundary_m", "venue_avg_score",
        "day_temp_c", "night_temp_c", "humidity_pct", "wind_speed_kmh",
        "dew_factor", "is_day_night", "weather_source"
    ]
    for key in expected_keys:
        assert key in cond, f"Missing key: {key}"
        
    assert cond["venue_id"] == "mcg"
    assert cond["venue_name"] == "Melbourne Cricket Ground"
    assert cond["pitch_type"] == "balanced"
    assert cond["venue_avg_score"] == 155.0  # T20 base score
    
    # Test ODI score (155 * 1.6 = 248)
    cond_odi = build_environmental_conditions("Melbourne Cricket Ground", "2026-08-01", True, match_format="ODI")
    assert cond_odi["venue_avg_score"] == 248.0
    
    # Test Test score (155 * 2.0 = 310)
    cond_test = build_environmental_conditions("Melbourne Cricket Ground", "2026-08-01", True, match_format="Test")
    assert cond_test["venue_avg_score"] == 310.0
    
    assert isinstance(cond["dew_factor"], float)
    assert 0.0 <= cond["dew_factor"] <= 1.0, f"Dew factor out of bounds: {cond['dew_factor']}"
    assert cond["is_day_night"] is True
    print(f"  OK -- Venue: {cond['venue_name']}, Pitch: {cond['pitch_type']}, Dew: {cond['dew_factor']}, Scores: T20={cond['venue_avg_score']}, ODI={cond_odi['venue_avg_score']}, Test={cond_test['venue_avg_score']}")


if __name__ == "__main__":
    try:
        test_build_environmental_conditions()
        time.sleep(1)
        test_search_ddg()
        time.sleep(1)
        test_scrape_cricbuzz_profile()
        time.sleep(1)
        test_find_cricbuzz_url()
        time.sleep(1)
        test_collect_context()
        time.sleep(1)
        test_parse_cricbuzz_squad()
        print("\n" + SEPARATOR)
        print("ALL TESTS PASSED [OK]")
        sys.exit(0)
    except AssertionError as exc:
        print(f"\n[FAIL] ASSERTION FAILED: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] UNEXPECTED ERROR: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
