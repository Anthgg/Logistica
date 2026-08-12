import argparse
import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings


def wait_for_database(timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = "database unavailable"
    while time.monotonic() < deadline:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("PostgreSQL disponible.", flush=True)
            return
        except SQLAlchemyError as exc:
            last_error = exc.__class__.__name__
            time.sleep(2)
        finally:
            engine.dispose()
    raise SystemExit(
        "PostgreSQL no estuvo disponible dentro del tiempo permitido "
        f"(último error: {last_error})."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Espera PostgreSQL sin registrar credenciales."
    )
    parser.add_argument("--timeout-seconds", type=int, default=90)
    arguments = parser.parse_args()
    if arguments.timeout_seconds < 1:
        raise SystemExit("--timeout-seconds debe ser positivo.")
    wait_for_database(arguments.timeout_seconds)


if __name__ == "__main__":
    main()
