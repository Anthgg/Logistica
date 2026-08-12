from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def create(self, database: Session, **values: object) -> AuditLog:
        audit_log = AuditLog(**values)
        database.add(audit_log)
        database.flush()
        return audit_log
