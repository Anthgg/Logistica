from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
JWT_PATTERN = re.compile(
    r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
)
SECRET_PATTERN = re.compile(
    r"(?i)\b(password|passwd|secret|authorization|bearer|cookie|token)\b\s*[:=]"
)
WINDOWS_PATH_PATTERN = re.compile(r"\b[A-Za-z]:\\(?:[^\\\r\n]+\\)+[^\\\r\n]*")
UNIX_HOME_PATTERN = re.compile(r"/(?:home|Users)/[^/\s]+/")


class PrivacyViolationError(RuntimeError):
    """Raised when a report contains forbidden personal or secret material."""


def participant_code(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"P-{digest[:10].upper()}"


def pseudonymize_participants(
    frame: pd.DataFrame,
    *,
    participant_column: str,
) -> pd.DataFrame:
    result = frame.copy()
    if participant_column in result:
        result[participant_column] = result[participant_column].map(
            lambda value: participant_code(str(value))
        )
    return result


def public_prediction_columns(
    frame: pd.DataFrame,
    *,
    participant_column: str,
) -> pd.DataFrame:
    forbidden_tokens = {
        "address",
        "cookie",
        "dni",
        "email",
        "embedding",
        "image",
        "name",
        "password",
        "path",
        "payload",
        "phone",
        "secret",
        "text",
        "token",
    }
    safe_columns = [
        column
        for column in frame.columns
        if not (
            {
                token
                for token in re.split(r"[^a-z0-9]+", column.casefold())
                if token
            }
            & forbidden_tokens
        )
    ]
    return pseudonymize_participants(
        frame.loc[:, safe_columns],
        participant_column=participant_column,
    )


def assert_report_privacy(output_directory: Path) -> None:
    violations: list[str] = []
    text_suffixes = {".csv", ".json", ".md", ".txt", ".yaml", ".yml"}
    for path in output_directory.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.casefold()
        if suffix in {".jpg", ".jpeg", ".webp", ".bmp"}:
            violations.append(f"{path.name}:facial_binary")
            continue
        if suffix not in text_suffixes:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        patterns = (
            ("email", EMAIL_PATTERN),
            ("jwt", JWT_PATTERN),
            ("secret", SECRET_PATTERN),
            ("windows_path", WINDOWS_PATH_PATTERN),
            ("home_path", UNIX_HOME_PATTERN),
        )
        for label, pattern in patterns:
            if pattern.search(content):
                violations.append(f"{path.name}:{label}")
    if violations:
        raise PrivacyViolationError(
            "Los informes contienen material prohibido: "
            + ", ".join(sorted(violations))
        )
