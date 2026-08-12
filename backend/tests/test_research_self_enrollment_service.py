from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ApplicationError
from app.models.research_participant import ResearchParticipant
from app.models.user import User
from app.services.research_service import ResearchService


def _user() -> User:
    return User(
        id=uuid4(),
        email="self-enrollment@example.test",
        password_hash="not-a-real-hash",
        full_name="Self Enrollment Test",
        role="dispatcher",
        is_active=True,
    )


def _participant(user: User, *, active: bool = True) -> ResearchParticipant:
    now = datetime.now(timezone.utc)
    return ResearchParticipant(
        id=uuid4(),
        linked_user_id=user.id,
        participant_code="P-0042",
        is_active=active,
        enrollment_date=now,
        withdrawal_date=None if active else now,
        created_at=now,
        updated_at=now,
    )


def test_self_enrollment_returns_existing_active_profile() -> None:
    service = ResearchService()
    user = _user()
    existing = _participant(user)
    service.repository = Mock()
    service.repository.participant_for_user.return_value = existing
    database = Mock()

    result = service.self_enroll(database, user)

    assert result.created is False
    assert result.participant.id == existing.id
    database.add.assert_not_called()
    database.commit.assert_not_called()


def test_self_enrollment_creates_pseudonymous_profile() -> None:
    service = ResearchService()
    user = _user()
    service.repository = Mock()
    service.repository.participant_for_user.return_value = None
    service.audit = Mock()
    database = Mock()
    database.execute.return_value.scalar_one.return_value = 17

    def populate_defaults(participant: ResearchParticipant) -> None:
        now = datetime.now(timezone.utc)
        participant.id = uuid4()
        participant.is_active = True
        participant.enrollment_date = now
        participant.created_at = now
        participant.updated_at = now

    database.add.side_effect = populate_defaults

    result = service.self_enroll(database, user)

    assert result.created is True
    assert result.participant.linked_user_id == user.id
    assert result.participant.participant_code == "P-0017"
    database.commit.assert_called_once()
    service.audit.record.assert_called_once()


def test_self_enrollment_does_not_reactivate_withdrawn_profile() -> None:
    service = ResearchService()
    user = _user()
    service.repository = Mock()
    service.repository.participant_for_user.return_value = _participant(
        user, active=False
    )

    with pytest.raises(ApplicationError) as error:
        service.self_enroll(Mock(), user)

    assert error.value.code == "PARTICIPANT_INACTIVE"
    assert error.value.status_code == 409


def test_self_enrollment_recovers_from_concurrent_duplicate() -> None:
    service = ResearchService()
    user = _user()
    concurrent = _participant(user)
    service.repository = Mock()
    service.repository.participant_for_user.side_effect = [None, concurrent]
    database = Mock()
    database.execute.return_value.scalar_one.return_value = 43
    database.flush.side_effect = IntegrityError(
        "INSERT research_participants", {}, Exception("unique violation")
    )

    result = service.self_enroll(database, user)

    assert result.created is False
    assert result.participant.id == concurrent.id
    database.rollback.assert_called_once()
