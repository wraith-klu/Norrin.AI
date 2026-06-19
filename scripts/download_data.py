import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sports_predictor.data_collection import generate_sample_data, initialize_sqlite_database


if __name__ == "__main__":
    df = generate_sample_data()
    initialize_sqlite_database()
    print(f"Generated demo dataset with {len(df)} rows.")
