import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sports_predictor.config import ensure_directories


if __name__ == "__main__":
    ensure_directories()
    print("Project directories are ready.")
