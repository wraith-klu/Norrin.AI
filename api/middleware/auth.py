def validate_api_key(api_key: str | None) -> bool:
    return api_key is None or bool(api_key.strip())
