from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.models.session import UserSession


class SessionRepository:
    def get_by_token_hash(self, database: Session, token_hash: str) -> UserSession | None:
        return database.scalar(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )

    def get_by_refresh_hash(
        self, database: Session, refresh_hash: str
    ) -> tuple[UserSession | None, bool]:
        user_session = database.scalar(
            select(UserSession).where(
                or_(
                    UserSession.refresh_token_hash == refresh_hash,
                    UserSession.previous_refresh_token_hash == refresh_hash,
                )
            )
        )
        reused = bool(
            user_session
            and user_session.previous_refresh_token_hash == refresh_hash
        )
        return user_session, reused

    def get_by_id_for_user(
        self, database: Session, session_id: UUID, user_id: UUID
    ) -> UserSession | None:
        return database.scalar(
            select(UserSession).where(
                UserSession.id == session_id, UserSession.user_id == user_id
            )
        )

    def list_for_user(self, database: Session, user_id: UUID) -> list[UserSession]:
        return list(
            database.scalars(
                select(UserSession)
                .where(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > utc_now(),
                )
                .order_by(UserSession.created_at.desc())
            )
        )

    def create(self, database: Session, **values: object) -> UserSession:
        user_session = UserSession(**values)
        database.add(user_session)
        database.flush()
        return user_session

    def revoke(self, database: Session, user_session: UserSession, when: datetime) -> bool:
        if user_session.revoked_at is not None:
            return False
        user_session.revoked_at = when
        database.flush()
        return True

    def revoke_all_for_user(
        self,
        database: Session,
        user_id: UUID,
        when: datetime,
        except_session_id: UUID | None = None,
    ) -> int:
        conditions = [
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        ]
        if except_session_id:
            conditions.append(UserSession.id != except_session_id)
        result = database.execute(
            update(UserSession).where(*conditions).values(revoked_at=when)
        )
        return int(result.rowcount or 0)