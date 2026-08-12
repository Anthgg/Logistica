from sqlalchemy.orm import Session

from app.models.risk_event import RiskEvent


class RiskEventRepository:
    def create(self, database: Session, event: RiskEvent) -> RiskEvent:
        database.add(event)
        database.flush()
        return event
