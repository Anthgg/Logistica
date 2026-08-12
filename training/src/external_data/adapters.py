from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

KEYBOARD_COLUMNS = [
    "keydown_time",
    "keyup_time",
    "dwell_time",
    "flight_time",
    "interval_time",
    "sequence_index",
    "session_id",
    "subject_id",
    "legitimate_label",
]
MOUSE_COLUMNS = [
    "timestamp",
    "normalized_x",
    "normalized_y",
    "delta_x",
    "delta_y",
    "distance",
    "velocity",
    "acceleration",
    "event_type",
    "button_category",
    "scroll_delta",
    "subject_id",
    "session_id",
    "legitimate_label",
]
FORBIDDEN_KEYBOARD_COLUMNS = {
    "key",
    "character",
    "ascii",
    "code",
    "text",
    "password",
    "palabra",
    "frase",
}
FORBIDDEN_MOUSE_COLUMNS = {
    "clicked_element",
    "button_text",
    "css_selector",
    "html",
    "window_name",
}


def _first_present(frame: pd.DataFrame, aliases: tuple[str, ...]) -> pd.Series:
    lookup = {str(column).casefold(): column for column in frame.columns}
    for alias in aliases:
        if alias.casefold() in lookup:
            return frame[lookup[alias.casefold()]]
    return pd.Series([None] * len(frame), index=frame.index, dtype=object)


def _assert_no_forbidden_columns(frame: pd.DataFrame, forbidden: set[str]) -> None:
    present = {str(column).casefold() for column in frame.columns} & forbidden
    if present:
        raise ValueError(f"Persisten columnas sensibles: {sorted(present)}")


def _mouse_event_category(value: object) -> str:
    normalized = str(value).strip().casefold()
    for category in ("move", "click", "press", "release", "scroll", "drag"):
        if category in normalized:
            return category
    return "other"


def _mouse_button_category(value: object) -> str:
    normalized = str(value).strip().casefold()
    if normalized in {"", "nan", "none", "no button", "0"}:
        return "none"
    for category in ("left", "right", "middle"):
        if category in normalized:
            return category
    return "other"


def adapt_keystroke_events(frame: pd.DataFrame) -> pd.DataFrame:
    output = pd.DataFrame(index=frame.index)
    output["keydown_time"] = _first_present(
        frame, ("keydown_time", "press_time", "key_down_time")
    )
    output["keyup_time"] = _first_present(
        frame, ("keyup_time", "release_time", "key_up_time")
    )
    output["dwell_time"] = _first_present(
        frame, ("dwell_time", "hold_time", "duration", "h")
    )
    output["flight_time"] = _first_present(
        frame, ("flight_time", "down_down_time", "dd", "ud")
    )
    output["interval_time"] = _first_present(
        frame, ("interval_time", "inter_key_time", "latency")
    )
    output["sequence_index"] = _first_present(
        frame, ("sequence_index", "sequence", "event_index")
    )
    output["session_id"] = _first_present(
        frame, ("session_id", "session", "rep", "repetition")
    )
    output["subject_id"] = _first_present(
        frame, ("subject_id", "subject", "user_id", "user")
    )
    output["legitimate_label"] = _first_present(
        frame, ("legitimate_label", "label", "is_legitimate", "genuine")
    )
    for column in (
        "keydown_time",
        "keyup_time",
        "dwell_time",
        "flight_time",
        "interval_time",
        "sequence_index",
    ):
        output[column] = pd.to_numeric(output[column], errors="coerce")
    _assert_no_forbidden_columns(output, FORBIDDEN_KEYBOARD_COLUMNS)
    return output.reindex(columns=KEYBOARD_COLUMNS)


def adapt_cmu_wide(frame: pd.DataFrame) -> pd.DataFrame:
    subject = _first_present(frame, ("subject", "subject_id"))
    session = _first_present(frame, ("sessionIndex", "session", "session_id"))
    repetition = _first_present(frame, ("rep", "repetition"))
    timing_columns = [
        column
        for column in frame.columns
        if re.match(r"^(H|DD|UD)\.", str(column), flags=re.IGNORECASE)
    ]
    rows: list[dict[str, object]] = []
    for source_index, row in frame.iterrows():
        sequence = 0
        for column in timing_columns:
            prefix = str(column).split(".", maxsplit=1)[0].upper()
            value = pd.to_numeric(pd.Series([row[column]]), errors="coerce").iloc[0]
            record: dict[str, object] = {
                "keydown_time": None,
                "keyup_time": None,
                "dwell_time": None,
                "flight_time": None,
                "interval_time": None,
                "sequence_index": sequence,
                "session_id": f"{session.loc[source_index]}-{repetition.loc[source_index]}",
                "subject_id": subject.loc[source_index],
                "legitimate_label": True,
            }
            if prefix == "H":
                record["dwell_time"] = value
            elif prefix == "DD":
                record["interval_time"] = value
            else:
                record["flight_time"] = value
            rows.append(record)
            sequence += 1
    output = pd.DataFrame(rows, columns=KEYBOARD_COLUMNS)
    _assert_no_forbidden_columns(output, FORBIDDEN_KEYBOARD_COLUMNS)
    return output


def adapt_mouse_events(frame: pd.DataFrame) -> pd.DataFrame:
    output = pd.DataFrame(index=frame.index)
    output["timestamp"] = pd.to_numeric(
        _first_present(frame, ("timestamp", "record timestamp", "client timestamp", "time")),
        errors="coerce",
    )
    x = pd.to_numeric(_first_present(frame, ("x", "client_x", "mouse_x")), errors="coerce")
    y = pd.to_numeric(_first_present(frame, ("y", "client_y", "mouse_y")), errors="coerce")
    subject = _first_present(frame, ("subject_id", "subject", "user_id", "user"))
    session = _first_present(frame, ("session_id", "session", "filename"))
    output["subject_id"] = subject
    output["session_id"] = session
    groups = (
        pd.DataFrame({"subject": subject, "session": session})
        .astype(str)
        .agg("|".join, axis=1)
    )

    def normalize(values: pd.Series) -> pd.Series:
        minimum = values.groupby(groups).transform("min")
        maximum = values.groupby(groups).transform("max")
        span = (maximum - minimum).replace(0, np.nan)
        return ((values - minimum) / span).fillna(0.0).clip(0.0, 1.0)

    output["normalized_x"] = normalize(x)
    output["normalized_y"] = normalize(y)
    output["delta_x"] = output.groupby(groups)["normalized_x"].diff().fillna(0.0)
    output["delta_y"] = output.groupby(groups)["normalized_y"].diff().fillna(0.0)
    output["distance"] = np.hypot(output["delta_x"], output["delta_y"])
    delta_time = output.groupby(groups)["timestamp"].diff().replace(0, np.nan)
    output["velocity"] = (output["distance"] / delta_time).replace(
        [np.inf, -np.inf], np.nan
    ).fillna(0.0)
    output["acceleration"] = (
        output.groupby(groups)["velocity"].diff() / delta_time
    ).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    output["event_type"] = _first_present(
        frame, ("event_type", "state", "event")
    ).map(_mouse_event_category)
    output["button_category"] = _first_present(
        frame, ("button_category", "button")
    ).map(_mouse_button_category)
    output["scroll_delta"] = pd.to_numeric(
        _first_present(frame, ("scroll_delta", "scroll", "wheel")), errors="coerce"
    ).fillna(0.0)
    output["legitimate_label"] = _first_present(
        frame, ("legitimate_label", "label", "is_legitimate", "genuine")
    )
    _assert_no_forbidden_columns(output, FORBIDDEN_MOUSE_COLUMNS)
    return output.reindex(columns=MOUSE_COLUMNS)


def read_tabular(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    suffix = source.suffix.casefold()
    if suffix == ".csv":
        return pd.read_csv(source)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(source)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(source)
    if suffix == ".json":
        return pd.read_json(source)
    raise ValueError(f"Formato tabular no admitido: {suffix}")
