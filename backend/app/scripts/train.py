from app.models import train_all_models


if __name__ == "__main__":
    trained = train_all_models()
    for sport, bundle in trained.items():
        print(f"{sport}: R2={bundle.metrics['r2']:.3f}, MAE={bundle.metrics['mae']:.3f}")
