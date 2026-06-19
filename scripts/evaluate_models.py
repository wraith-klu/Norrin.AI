from pathlib import Path


if __name__ == "__main__":
    report = Path("reports/validation_results.json")
    print(report.read_text(encoding="utf-8") if report.exists() else "Run scripts/train_models.py first.")
