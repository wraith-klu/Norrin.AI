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
