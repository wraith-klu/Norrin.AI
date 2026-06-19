import pandas as pd


def validate_required_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [column for column in required if column not in df.columns]
