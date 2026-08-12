"""Phase 043 — Storage compatibility evaluation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from ..enums import StorageCompatibilityRuleType, StorageCompatibilityAction, StorageCompatibilitySeverity
from ...infrastructure.persistence.repositories import StorageCompatibilityRuleRepository


class StorageCompatibilityAllow:
    ALLOW = StorageCompatibilityAction.ALLOW
    DENY = StorageCompatibilityAction.DENY
    REQUIRE_REVIEW = StorageCompatibilityAction.REQUIRE_REVIEW


@dataclass
class CompatibilityResult:
    compatible: bool = True
    action: str = StorageCompatibilityAction.ALLOW.value
    severity: str = StorageCompatibilitySeverity.MEDIUM.value
    matched_rules: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class StorageCompatibilityService:
    """Evaluates product-location compatibility against storage rules."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._rule_repo = StorageCompatibilityRuleRepository(db)

    def evaluate(
        self,
        warehouse_id: UUID,
        location_id: UUID,
        *,
        product_id: UUID | None = None,
        product_category_id: UUID | None = None,
        location_type: str | None = None,
        policy_version_id: UUID | None = None,
    ) -> CompatibilityResult:
        result = CompatibilityResult()

        rules = self._rule_repo.list_by_warehouse(
            warehouse_id,
            product_id=product_id,
            location_id=location_id,
        )

        if policy_version_id:
            policy_rules = self._rule_repo.list_by_policy_version(policy_version_id)
            seen_ids = {r.id for r in rules}
            for r in policy_rules:
                if r.id not in seen_ids:
                    rules.append(r)

        for rule in rules:
            if rule.location_type and location_type and rule.location_type != location_type:
                continue

            matched = True
            if rule.rule_type == StorageCompatibilityRuleType.PRODUCT_CATEGORY.value:
                if product_category_id and rule.product_category_id:
                    matched = rule.product_category_id == product_category_id
                else:
                    matched = False

            if rule.rule_type == StorageCompatibilityRuleType.LOCATION_ZONE.value:
                if rule.location_id:
                    matched = rule.location_id == location_id
                else:
                    matched = True

            if not matched:
                continue

            result.matched_rules.append({
                "rule_id": str(rule.id),
                "rule_type": rule.rule_type,
                "action": rule.action,
                "severity": rule.severity,
                "reason": rule.reason,
            })

            if rule.action == StorageCompatibilityAction.DENY.value:
                result.compatible = False
                result.action = StorageCompatibilityAction.DENY.value
                result.severity = rule.severity
                break

            if rule.action == StorageCompatibilityAction.REQUIRE_REVIEW.value:
                result.warnings.append(rule.reason or f"Rule {rule.rule_type} warning")
                if rule.severity in (StorageCompatibilitySeverity.HIGH.value, StorageCompatibilitySeverity.CRITICAL.value):
                    result.severity = rule.severity

        return result

    def is_compatible(self, result: CompatibilityResult) -> bool:
        return result.compatible

    def has_warnings(self, result: CompatibilityResult) -> bool:
        return len(result.warnings) > 0
