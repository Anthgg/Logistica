import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import engine

logger = logging.getLogger("app.database")


def is_database_connected() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.warning("Database health check failed")
        return False
