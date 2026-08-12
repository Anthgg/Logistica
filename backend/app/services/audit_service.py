from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self) -> None:
        self.repository = AuditLogRepository()

    def record(
        self,
        database: Session,
        event_type: str,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        event_metadata: dict[str, object] | None = None,
    ) -> None:
        self.repository.create(
            database,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=event_metadata,
        )
