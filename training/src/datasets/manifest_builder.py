import json
from pathlib import Path

import pandas as pd


def write_manifest(
    frame: pd.DataFrame,
    path: str | Path,
    *,
    csv_copy: bool = False,
    dry_run: bool = False,
) -> Path:
    target = Path(path)
    if any(
        Path(str(value)).is_absolute()
        for value in frame.get("file_path", pd.Series(dtype=str)).dropna()
    ):
        raise ValueError("Los manifiestos no pueden contener rutas absolutas.")
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(target, index=False)
        if csv_copy:
            csv_frame = frame.copy()
            for column in ("rejection_reasons",):
                if column in csv_frame:
                    csv_frame[column] = csv_frame[column].apply(
                        lambda value: (
                            json.dumps(value, ensure_ascii=False)
                            if isinstance(value, list)
                            else value
                        )
                    )
            csv_frame.to_csv(target.with_suffix(".csv"), index=False)
    return target


def read_manifest(path: str | Path) -> pd.DataFrame:
    return pd.read_parquet(Path(path))
