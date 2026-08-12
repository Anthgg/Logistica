from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreateInternal


class DuplicateEmailError(ValueError):
    """Raised when creating a user with an already existing email."""
    pass


class UserRepository:
    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    def get_by_id(self, database: Session, user_id: UUID) -> User | None:
        return database.get(User, user_id)

    def get_by_email(self, database: Session, email: str) -> User | None:
        normalized = self.normalize_email(email)
        return database.scalar(select(User).where(User.email == normalized))

    def create(self, database: Session, data: UserCreateInternal) -> User:
        user = User(
            email=self.normalize_email(data.email),
            password_hash=data.password_hash,
            full_name=data.full_name,
            role=data.role,
        )
        database.add(user)
        try:
            database.flush()
        except IntegrityError as exc:
            database.rollback()
            raise DuplicateEmailError("email_already_exists") from exc
        return user

    def list(self, database: Session, *, offset: int = 0, limit: int = 100) -> List[User]:
        return list(database.scalars(select(User).offset(offset).limit(limit)))

    def update_active_status(
        self, database: Session, user: User, is_active: bool
    ) -> User:
        user.is_active = is_active
        database.flush()
        return user

    def delete(self, database: Session, user: User) -> None:
        database.delete(user)
        database.flush()
