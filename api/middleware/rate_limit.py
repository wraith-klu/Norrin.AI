def rate_limit_key(client_host: str | None) -> str:
    return client_host or "anonymous"
