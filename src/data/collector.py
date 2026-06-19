from sports_predictor.data_collection import DataCollector


class CricketDataCollector(DataCollector):
    def __init__(self, seed: int = 42):
        super().__init__(sport="cricket", seed=seed)


class FootballDataCollector(DataCollector):
    def __init__(self, seed: int = 42):
        super().__init__(sport="football", seed=seed)


class NBADataCollector(DataCollector):
    def __init__(self, seed: int = 42):
        super().__init__(sport="nba", seed=seed)
