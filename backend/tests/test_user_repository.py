import pytest

from app.repositories.user_repository import DuplicateEmailError, UserRepository
from app.schemas.user import UserCreateInternal, UserRead

repository = UserRepository()


def user_data(email: str = "database-test@example.com") -> UserCreateInternal:
    return UserCreateInternal(
        email=email,
        password_hash="temporary-test-hash-not-for-production",
        full_name="Database Test",
        role="user",
    )


def test_user_crud(database) -> None:
    user = repository.create(database, user_data())
    assert repository.get_by_email(database, "database-test@example.com") is user
    assert repository.get_by_id(database, user.id) is user

    repository.update_active_status(database, user, False)
    assert user.is_active is False
    assert user in repository.list(database)

    public_user = UserRead.model_validate(user).model_dump()
    assert "password_hash" not in public_user

    user_id = user.id
    repository.delete(database, user)
    assert repository.get_by_id(database, user_id) is None


def test_duplicate_email_is_handled(database) -> None:
    repository.create(database, user_data("duplicate@example.com"))
    with pytest.raises(DuplicateEmailError):
        repository.create(database, user_data("duplicate@example.com"))


def test_rollback_removes_uncommitted_user(database) -> None:
    repository.create(database, user_data("rollback@example.com"))
    database.rollback()
    assert repository.get_by_email(database, "rollback@example.com") is None


def test_public_schema_never_declares_password_hash() -> None:
    assert "password_hash" not in UserRead.model_fields
