import logging
from app.config import SPORTS


def validate_api_key(api_key: str | None) -> bool:
    return api_key is None or bool(api_key.strip())


def rate_limit_key(client_host: str | None) -> str:
    return client_host or "anonymous"


def supported_sports() -> tuple[str, ...]:
    return SPORTS


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return logging.getLogger(name)
