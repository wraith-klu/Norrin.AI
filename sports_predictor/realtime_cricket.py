"""
realtime_cricket.py
Real-time cricket player analysis and prediction engine.
Scrapes live data from DuckDuckGo and Cricbuzz, then calls OpenRouter LLM
to produce deep structured predictions for batsmen and bowlers.
"""
from __future__ import annotations

import json
import re
import urllib.parse
from typing import Any, Callable

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

def search_ddg(query: str, num_results: int = 5, _retry: int = 2) -> list[dict]:
    """Query DuckDuckGo HTML search and return list of {title, url, snippet}.
    Retries up to _retry times on empty or error responses.
    """
    import time
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    for attempt in range(max(1, _retry)):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                if attempt < _retry - 1:
                    time.sleep(2)
                    continue
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            results: list[dict] = []
            for div in soup.find_all("div", class_="result"):
                a_url = div.find("a", class_="result__url")
                a_snip = div.find("a", class_="result__snippet")
                if not (a_url and a_snip):
                    continue
                href = str(a_url.get("href") or "")
                # unwrap DuckDuckGo redirect
                parsed = urllib.parse.urlparse(href)
                real_url = href
                if parsed.query:
                    qs = urllib.parse.parse_qs(parsed.query)
                    if "uddg" in qs:
                        real_url = qs["uddg"][0]
                results.append(
                    {
                        "title": a_url.get_text().strip(),
                        "url": real_url,
                        "snippet": a_snip.get_text().strip(),
                    }
                )
                if len(results) >= num_results:
                    break
            if results or attempt >= _retry - 1:
                return results
            # Got an empty page — might be rate limited, wait and retry
            time.sleep(3)
        except Exception as exc:  # noqa: BLE001
            if attempt >= _retry - 1:
                return [{"title": "Search error", "url": "", "snippet": str(exc)}]
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


# ---------------------------------------------------------------------------
# Context collector
# ---------------------------------------------------------------------------

def collect_player_match_context(
    player_name: str,
    opposition: str,
    venue: str,
    match_format: str = "T20",
    status_callback: Callable[[str], None] | None = None,
) -> dict:
    """
    Run a battery of web searches and Cricbuzz scraping to build a
    rich, structured context dict for use with the LLM predictor.
    """

    def _cb(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    ctx: dict[str, Any] = {}

    # 1. Find & scrape Cricbuzz profile
    _cb(f"🔍 Searching Cricbuzz profile for **{player_name}**...")
    profile_url = find_cricbuzz_profile_url(player_name)

    if profile_url:
        _cb(f"📈 Scraping career statistics from Cricbuzz...")
        ctx["profile_data"] = scrape_cricbuzz_profile(profile_url)
    else:
        _cb("⚠️  No Cricbuzz profile found. Relying on search snippets.")
        ctx["profile_snippets"] = search_ddg(f"{player_name} cricket profile stats", 4)

    # 2. Recent form (format-specific)
    _cb(f"📅 Fetching recent **{match_format}** performances for **{player_name}**...")
    ctx["recent_form"] = search_ddg(
        f"{player_name} cricket {match_format} recent matches scores 2024 2025 2026", 5
    )

    # 3. Head-to-head vs opposition (format-specific)
    _cb(f"⚔️  Fetching head-to-head records: **{player_name}** vs **{opposition}** in **{match_format}**...")
    ctx["head_to_head"] = search_ddg(
        f"{player_name} vs {opposition} cricket {match_format} head to head stats records", 5
    )

    # 4. Venue / pitch report
    _cb(f"🏟️  Fetching pitch & venue report for **{venue}** ({match_format})...")
    ctx["pitch_report"] = search_ddg(
        f"{venue} cricket pitch report conditions {match_format} stats batting bowling", 5
    )

    # 5. Opposition bowling attack
    _cb(f"🏏  Analysing **{opposition}** bowling attack ({match_format})...")
    ctx["opposition_bowlers"] = search_ddg(
        f"{opposition} cricket team bowlers key players wicket-takers {match_format} 2025 2026", 5
    )

    return ctx


# ---------------------------------------------------------------------------
# LLM Predictor (OpenRouter)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a world-class cricket analyst and performance prediction engine. "
    "Your analysis is data-driven, deeply informed by a player's career stats, "
    "recent form, head-to-head records, pitch conditions and opponent bowling quality. "
    "Always respond with a single raw JSON object — no markdown wrapper, no extra text."
)

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
    "length_strength": ["list of lengths/deliveries he handles well"]
  },
  "bowler_prediction": {
    "predicted_wickets": "e.g. 2-3 wickets",
    "predicted_economy": "e.g. 6.8 runs/over",
    "success_rate": "e.g. Strike rate ~22 balls/wicket",
    "kind_of_ball_will_bowl": "Describe the primary delivery types this bowler will use",
    "success_rate_vs_batters": "Name the opposition batters he is most/least likely to trouble and why",
    "role_in_match": "e.g. Open the bowling and bowl 2 death overs, or Defensive mid-overs role"
  }
}

Rules:
- If the player is NOT a batsman (pure bowler), set "batsman_prediction" to null.
- If the player is NOT a bowler (pure batsman), set "bowler_prediction" to null.
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
    _add_section("PITCH & VENUE CONDITIONS (web)", "pitch_report")
    _add_section("OPPOSITION BOWLING ATTACK (web)", "opposition_bowlers")

    lines.append("")
    lines.append(PREDICTION_SCHEMA)
    return "\n".join(lines)


def predict_real_player(
    player_name: str,
    opposition: str,
    venue: str,
    api_key: str,
    match_format: str = "T20",
    model_name: str = "google/gemini-2.5-flash",
    status_callback: Callable[[str], None] | None = None,
) -> dict:
    """
    End-to-end: scrape context → build prompt → call OpenRouter → return parsed dict.
    Returns a dict that always contains 'scraped_context'.
    On error, also contains 'error'.
    """

    def _cb(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    # 1. Collect context
    ctx = collect_player_match_context(player_name, opposition, venue, match_format, status_callback)

    _cb("🤖 Building prediction prompt and calling OpenRouter LLM...")

    prompt = _build_prompt(player_name, opposition, venue, ctx, match_format)

    or_headers = {
        "Authorization": f"Bearer {api_key}",
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

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=or_headers,
            json=payload,
            timeout=60,
        )
        if resp.status_code != 200:
            err = f"OpenRouter returned HTTP {resp.status_code}: {resp.text[:400]}"
            return {"error": err, "scraped_context": ctx}

        raw = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip optional markdown code-fence wrapper
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw.strip())

        result = json.loads(raw)
        result["scraped_context"] = ctx
        _cb("✅ Prediction complete!")
        return result

    except json.JSONDecodeError as exc:
        return {
            "error": f"Failed to parse LLM JSON response: {exc}",
            "raw_response": raw if "raw" in dir() else "",  # type: ignore[name-defined]
            "scraped_context": ctx,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "scraped_context": ctx}


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
        tab_div = soup.find("div", class_=lambda x: x and "bg-cbInactTab" in x)
        team1, team2 = "Team 1", "Team 2"
        if tab_div:
            h1_tags = tab_div.find_all("h1", class_=lambda x: x and "font-bold" in x)
            if len(h1_tags) >= 2:
                team1 = h1_tags[0].get_text(strip=True)
                team2 = h1_tags[1].get_text(strip=True)
        else:
            # Fallback team names from page title
            title_str = str(soup.title.string) if soup.title and soup.title.string else ""
            if "|" in title_str and "," in title_str:
                teams_part = title_str.split("|")[1].split(",")[0].strip()
                if " vs " in teams_part:
                    t_split = teams_part.split(" vs ")
                    team1, team2 = t_split[0].strip(), t_split[1].strip()
        
        # 2. Extract series and venue details using regex
        venue, series = "Unknown Venue", "Unknown Series"
        info_divs = soup.find_all("div", class_=lambda x: x and "flex-wrap" in x and "items-center" in x)
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
        pb5_divs = soup.find_all("div", class_=lambda x: x and "pb-5" in x)
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
                
            flex_div = div.find("div", class_=lambda x: x and "flex" in x)
            if flex_div:
                cols = flex_div.find_all("div", class_=lambda x: x and "w-1/2" in x, recursive=False)
                if len(cols) >= 2:
                    # Column 0 is Team 1
                    for a in cols[0].find_all("a", href=True):
                        if "/profiles/" in a['href']:
                            name = ""
                            for span in a.find_all("span"):
                                txt = span.get_text(strip=True)
                                if txt:
                                    name = txt
                                    break
                            if not name:
                                name = a.get_text(strip=True)
                            role_div = a.find("div", class_=lambda x: x and "text-xs" in x)
                            role = role_div.get_text(strip=True) if role_div else ""
                            squad1.append({"name": name, "role": role, "href": a['href'], "status": status})
                            
                    # Column 1 is Team 2
                    for a in cols[1].find_all("a", href=True):
                        if "/profiles/" in a['href']:
                            name = ""
                            for span in a.find_all("span"):
                                txt = span.get_text(strip=True)
                                if txt:
                                    name = txt
                                    break
                            if not name:
                                name = a.get_text(strip=True)
                            role_div = a.find("div", class_=lambda x: x and "text-xs" in x)
                            role = role_div.get_text(strip=True) if role_div else ""
                            squad2.append({"name": name, "role": role, "href": a['href'], "status": status})
                            
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
) -> dict:
    """
    Run targeted web searches and scrape direct profile details to assemble
    a highly detailed context for the player matchup.
    """
    def _cb(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    ctx: dict[str, Any] = {}

    # 1. Scrape Cricbuzz profile directly
    _cb(f"📈 Scraping career statistics from Cricbuzz profile...")
    if player_profile_url:
        if player_profile_url.startswith("/"):
            player_profile_url = "https://www.cricbuzz.com" + player_profile_url
        ctx["profile_data"] = scrape_cricbuzz_profile(player_profile_url)
    else:
        ctx["profile_snippets"] = search_ddg(f"{player_name} cricket profile stats", 4)

    # 2. Recent form
    _cb(f"📅 Fetching recent **{match_format}** performances for **{player_name}**...")
    ctx["recent_form"] = search_ddg(
        f"{player_name} cricket recent matches scores {match_format} 2025 2026", 5
    )

    # 3. Head-to-head vs opposition
    _cb(f"⚔️  Fetching head-to-head records: **{player_name}** vs **{opposition_team}** in **{match_format}**...")
    ctx["head_to_head"] = search_ddg(
        f"{player_name} vs {opposition_team} cricket head to head stats records {match_format}", 5
    )

    # 4. Venue / pitch report
    _cb(f"🏟️  Fetching pitch & venue report for **{venue}** in **{match_format}**...")
    ctx["pitch_report"] = search_ddg(
        f"{venue} cricket pitch report conditions stats batting bowling {match_format}", 5
    )

    # 5. Opposition lineup
    _cb(f"🏏  Analysing **{opposition_team}** squad and matchups...")
    opp_names = [p["name"] for p in opponent_squad if p["name"]]
    ctx["opposition_lineup"] = opp_names
    ctx["opposition_bowlers"] = search_ddg(
        f"{opposition_team} cricket team key players bowlers batters match analysis {match_format}", 5
    )

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
    _add_section(f"PITCH & VENUE CONDITIONS FOR {match_format} (web)", "pitch_report")
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
    api_key: str,
    model_name: str = "google/gemini-2.5-flash",
    status_callback: Callable[[str], None] | None = None,
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
    )

    _cb("🤖 Building prediction prompt and calling OpenRouter LLM...")

    prompt = _build_prompt_squad(
        player_name=player_name,
        opposition=opposition_team,
        venue=venue,
        match_format=match_format,
        ctx=ctx
    )

    or_headers = {
        "Authorization": f"Bearer {api_key}",
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

    raw = ""
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=or_headers,
            json=payload,
            timeout=60,
        )
        if resp.status_code != 200:
            err = f"OpenRouter returned HTTP {resp.status_code}: {resp.text[:400]}"
            return {"error": err, "scraped_context": ctx}

        raw = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip optional markdown code-fence wrapper
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw.strip())

        result = json.loads(raw)
        result["scraped_context"] = ctx
        _cb("✅ Prediction complete!")
        return result

    except json.JSONDecodeError as exc:
        return {
            "error": f"Failed to parse LLM JSON response: {exc}",
            "raw_response": raw if "raw" in dir() else "",
            "scraped_context": ctx,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "scraped_context": ctx}
