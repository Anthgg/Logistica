import logging

from app.database.session import SessionLocal
from app.services.research_service import ResearchService

logger = logging.getLogger("app.commands.invalidate_stale_research_sessions")


def main() -> None:
    service = ResearchService()
    with SessionLocal() as database:
        count = service.invalidate_stale_sessions(database)
    logger.info("Sesiones experimentales invalidadas: %s", count)
    print(f"Sesiones experimentales invalidadas: {count}")


if __name__ == "__main__":
    main()
