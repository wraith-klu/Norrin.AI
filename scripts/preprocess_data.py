import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.model_selection import train_test_split

from sports_predictor.config import DATA_DIR, SPORTS
from sports_predictor.data_collection import clean_and_validate, load_or_create_dataset
from sports_predictor.feature_engineering import build_feature_frame


if __name__ == "__main__":
    df = build_feature_frame(clean_and_validate(load_or_create_dataset()))
    for sport in SPORTS:
        sport_df = df[df["sport"].eq(sport)].sort_values("match_date")
        train_val, test = train_test_split(sport_df, test_size=0.2, shuffle=False)
        train, val = train_test_split(train_val, test_size=0.25, shuffle=False)
        output_dir = DATA_DIR / "processed" / sport
        output_dir.mkdir(parents=True, exist_ok=True)
        train.to_csv(output_dir / "train_features.csv", index=False)
        val.to_csv(output_dir / "val_features.csv", index=False)
        test.to_csv(output_dir / "test_features.csv", index=False)
    print("Wrote processed train/val/test feature files.")
