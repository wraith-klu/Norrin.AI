from sports_predictor.data_collection import *  # noqa: F401,F403


if __name__ == "__main__":
    df = generate_sample_data()
    db_path = initialize_sqlite_database()
    print(f"Generated {len(df)} rows at data/sample_player_stats.csv")
    print(f"Initialized database at {db_path}")
