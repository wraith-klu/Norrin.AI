from fastapi import FastAPI

from api.routes import admin, health, models, predictions

app = FastAPI(
    title="Player Performance API",
    description="Predicts player performance across cricket, football, and NBA.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(predictions.router)
app.include_router(models.router)
app.include_router(admin.router)


@app.post("/predict")
def legacy_predict(request: predictions.PredictionRequest) -> dict:
    return predictions.predict(request)


@app.post("/train")
def legacy_train() -> dict[str, dict[str, float]]:
    return models.train()
