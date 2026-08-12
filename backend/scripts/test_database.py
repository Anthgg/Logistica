import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import engine


def main() -> int:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            tables = inspect(connection).get_table_names()
        print("PostgreSQL conectado correctamente.")
        print(f"Tablas disponibles: {', '.join(sorted(tables)) or 'ninguna'}")
        return 0
    except SQLAlchemyError:
        print("No fue posible conectar con PostgreSQL.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
