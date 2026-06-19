# API Docs

Run locally:

```powershell
uvicorn api.main:app --reload
```

Open interactive docs at `http://127.0.0.1:8000/docs`.

## `GET /health`

Returns service status.

```json
{"status": "ok"}
```

## `POST /v1/models/train`

Regenerates trained model artifacts for all sports.

## `POST /v1/predict`

Request:

```json
{
  "player_id": 1,
  "sport": "cricket",
  "match_date": "2026-06-19",
  "opposition": "Team 2",
  "home_away": "home",
  "opposition_strength": 0.5,
  "injury_risk": 0.05,
  "days_rest": 4
}
```

Response:

```json
{
  "player_id": 1,
  "sport": "cricket",
  "predicted_performance": 28.4,
  "confidence_interval": [23.1, 31.9],
  "confidence_level": "80%",
  "risk_level": "Low"
}
```
