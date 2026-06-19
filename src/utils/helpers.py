from pathlib import Path


def project_path(*parts: str) -> Path:
    return Path(__file__).resolve().parents[2].joinpath(*parts)
