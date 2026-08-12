from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device


class DeviceRepository:
    def get_for_user_by_identifier(
        self, database: Session, user_id: UUID, identifier: str
    ) -> Device | None:
        return database.scalar(
            select(Device).where(
                Device.user_id == user_id,
                Device.device_identifier == identifier,
            )
        )

    def get_for_user_by_profile(
        self,
        database: Session,
        user_id: UUID,
        browser: str,
        operating_system: str,
        device_type: str,
    ) -> Device | None:
        return database.scalar(
            select(Device).where(
                Device.user_id == user_id,
                Device.browser == browser,
                Device.operating_system == operating_system,
                Device.device_type == device_type,
                Device.is_blocked.is_(False),
            ).order_by(Device.last_seen_at.desc())
        )

    def create(self, database: Session, **values: object) -> Device:
        device = Device(**values)
        database.add(device)
        database.flush()
        return device