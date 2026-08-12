import logging
from pathlib import Path


def configure_logging(log_file: Path | None = None) -> logging.Logger:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=handlers,
        force=True,
    )
    return logging.getLogger("training")


def safe_database_description(database_url: str) -> str:
    if "@" not in database_url:
        return "postgresql://[redacted]"
    return f"postgresql://[redacted]@{database_url.rsplit('@', 1)[1]}"
