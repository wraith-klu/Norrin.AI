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

- `data_collection.py`: sample data generation, ETL cleaning, SQLite schema initialization.
- `feature_engineering.py`: rolling windows, lags, momentum, context, career/season/opposition features.
- `models.py`: gradient boosting baseline, ensemble model, PyTorch LSTM class, interval models, training persistence.
- `evaluation.py`: MAE, RMSE, MAPE, R2, interval coverage, time-series CV helpers.
- `api.py`: FastAPI `/health`, `/train`, and `/predict` endpoints.
- `dashboard.py`: Streamlit dashboard with predictions, history, feature importance, and recent form.

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
- `models/{sport}_model.joblib`
- `models/{sport}_feature_importance.csv`
- `reports/validation_results.json`
