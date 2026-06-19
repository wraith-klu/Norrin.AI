from sports_predictor.models import create_xgboost_like_model


class PerformancePredictor:
    def __init__(self, sport: str):
        self.sport = sport
        self.model = create_xgboost_like_model()
        self.is_trained = False

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)
        self.is_trained = True
        return self

    def predict(self, X):
        return self.model.predict(X)
