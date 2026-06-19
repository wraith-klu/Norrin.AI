import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sports_predictor.models import train_all_models


if __name__ == "__main__":
    trained = train_all_models()
    for sport, bundle in trained.items():
        print(f"{sport}: R2={bundle.metrics['r2']:.3f}, MAE={bundle.metrics['mae']:.3f}")
