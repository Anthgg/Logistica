"""Phase 043 — Putaway policy resolution service."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from ..enums import PolicyStatus, PolicyVersionStatus
from ..errors import PutawayPolicyNotFound
from ...infrastructure.persistence.repositories import (
    PutawayPolicyRepository,
    PutawayPolicyVersionRepository,
)


class PutawayPolicyService:
    """Resolves the effective putaway policy version for a given context."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._policy_repo = PutawayPolicyRepository(db)
        self._version_repo = PutawayPolicyVersionRepository(db)

    def resolve_effective_version(
        self,
        organization_id: UUID,
        warehouse_id: UUID,
        *,
        product_id: UUID | None = None,
        product_category_id: UUID | None = None,
        at: datetime | None = None,
    ):
        version = self._version_repo.get_effective_for_context(
            organization_id, warehouse_id,
            product_id=product_id,
            product_category_id=product_category_id,
            at=at,
        )
        if version is None:
            raise PutawayPolicyNotFound(
                f"No active putaway policy version for org={organization_id}, "
                f"warehouse={warehouse_id}"
            )
        return version

    def create_policy(
        self, organization_id: UUID, *, code: str, name: str,
        description: str | None = None, created_by: UUID,
    ):
        existing = self._policy_repo.get_by_code(organization_id, code)
        if existing:
            raise ValueError(f"Policy code already exists: {code}")

        from ...infrastructure.persistence.models import PutawayPolicyModel
        policy = PutawayPolicyModel(
            organization_id=organization_id,
            code=code.strip(),
            normalized_code=code.strip().upper(),
            name=name.strip(),
            description=description,
            status=PolicyStatus.DRAFT.value,
            created_by=created_by,
        )
        return self._policy_repo.create(policy)

    def activate_policy(self, policy_id: UUID, organization_id: UUID, *, activated_by: UUID):
        policy = self._policy_repo.get(policy_id, organization_id)
        if not policy:
            raise PutawayPolicyNotFound(str(policy_id))
        if policy.status != PolicyStatus.DRAFT.value:
            raise ValueError(f"Cannot activate policy in status: {policy.status}")

        policy.status = PolicyStatus.ACTIVE.value
        policy.updated_at = datetime.now(timezone.utc)
        self._policy_repo.update(policy)
        return policy

    def create_version(
        self, policy_id: UUID, *, created_by: UUID, **kwargs
    ):
        policy = self._policy_repo.get(policy_id)
        if not policy:
            raise PutawayPolicyNotFound(str(policy_id))

        version_number = self._version_repo.next_version_number(policy_id)

        from ...infrastructure.persistence.models import PutawayPolicyVersionModel
        version = PutawayPolicyVersionModel(
            policy_id=policy_id,
            version_number=version_number,
            status=PolicyVersionStatus.DRAFT.value,
            created_by=created_by,
            **kwargs,
        )
        return self._version_repo.create(version)

    def activate_version(self, version_id: UUID, *, activated_by: UUID):
        version = self._version_repo.get(version_id)
        if not version:
            raise PutawayPolicyNotFound(f"Version {version_id} not found")
        if version.status != PolicyVersionStatus.DRAFT.value:
            raise ValueError(f"Cannot activate version in status: {version.status}")

        version.status = PolicyVersionStatus.ACTIVE.value
        version.activated_by = activated_by
        version.activated_at = datetime.now(timezone.utc)

        policy = self._policy_repo.get(version.policy_id)
        if policy:
            policy.active_version_id = version.id
            policy.updated_at = datetime.now(timezone.utc)
            self._policy_repo.update(policy)

        return self._version_repo.create(version) if not version.id else version
