CREATE TABLE IF NOT EXISTS player_matches (
    match_id TEXT PRIMARY KEY,
    player_id INTEGER,
    sport TEXT,
    match_date TEXT,
    opposition TEXT,
    performance_metric REAL
);

CREATE TABLE IF NOT EXISTS player_injuries (
    player_id INTEGER,
    sport TEXT,
    injury_date TEXT,
    recovery_date TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id TEXT PRIMARY KEY,
    venue_name TEXT,
    city TEXT,
    latitude REAL,
    longitude REAL,
    straight_boundary_m REAL,
    square_boundary_m REAL,
    pitch_type TEXT,  -- batting_friendly, balanced, dry_turner, green_seaming, bowling_friendly
    avg_first_innings_score REAL,
    avg_second_innings_score REAL,
    is_day_night_ground INTEGER
);
