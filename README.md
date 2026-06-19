# Elite Player Performance Prediction System

End-to-end player performance prediction for Cricket, Football, and NBA. The project includes offline sample data generation, feature engineering, model training, validation reports, a FastAPI service, and a Streamlit dashboard.

## Quick Start

```powershell
python scripts/download_data.py
python scripts/preprocess_data.py
python scripts/train_models.py
python -m pytest
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

The project generates deterministic sample data in `data/sample_player_stats.csv` so it runs without paid sports-data APIs. Replace that file with real ESPNcricinfo, Understat, FPL, NBA, or Kaggle exports using the same column schema to train on production data.

## Main Files

- `src/`: source package split by data, features, models, evaluation, utils, and sports.
- `api/main.py`: FastAPI application with `/health`, `/v1/predict`, and `/v1/models/train`.
- `dashboard/app.py`: Streamlit dashboard with predictions, history, feature importance, and recent form.
- `scripts/`: setup, data generation, preprocessing, training, and evaluation commands.

## Notes On XGBoost

The prompt requests XGBoost. This environment does not currently have `xgboost` installed, so the runnable baseline uses `HistGradientBoostingRegressor`, which is a strong tree-boosting substitute from scikit-learn. To use real XGBoost later, install `xgboost` and replace `create_xgboost_like_model()` in `sports_predictor/models.py`.

## Prediction Example

```powershell
curl -X POST http://127.0.0.1:8000/predict `
  -H "Content-Type: application/json" `
  -d "{\"player_id\":1,\"sport\":\"nba\",\"match_date\":\"2026-06-19\",\"opposition\":\"Team 3\",\"home_away\":\"home\"}"
```

## Generated Artifacts

- `data/sample_player_stats.csv`
- `data/sports_prediction.sqlite`
- `data/processed/{sport}/train_features.csv`
- `data/processed/{sport}/val_features.csv`
- `data/processed/{sport}/test_features.csv`
- `models/{sport}/xgboost_model.pkl`
- `models/{sport}/ensemble_model.pkl`
- `models/{sport}/feature_names.pkl`
- `models/{sport}/metadata.json`
- `reports/validation_results.json`
