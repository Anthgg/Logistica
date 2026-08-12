from datetime import datetime, timezone

import pandas as pd


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | str) -> datetime:
    parsed = (
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        if isinstance(value, str)
        else value
    )
    if parsed.tzinfo is None:
        raise ValueError("El timestamp debe incluir zona horaria.")
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime | str) -> str:
    return ensure_utc(value).isoformat().replace("+00:00", "Z")


def deterministic_source_timestamp(
    frame: pd.DataFrame, *columns: str
) -> str:
    values: list[datetime] = []
    for column in columns:
        if column not in frame:
            continue
        for value in frame[column].dropna():
            values.append(ensure_utc(value))
    selected = max(values) if values else datetime(1970, 1, 1, tzinfo=timezone.utc)
    return iso_utc(selected)
