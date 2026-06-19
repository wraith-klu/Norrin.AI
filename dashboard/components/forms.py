from sports_predictor.config import SPORTS


def sport_labels() -> list[str]:
    return [sport.title() for sport in SPORTS]
