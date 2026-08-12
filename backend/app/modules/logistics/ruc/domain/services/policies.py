"""Domain policies for RUC staleness, confidence, and provenance."""

from datetime import datetime, timezone
from typing import Any, Dict

from app.modules.logistics.ruc.domain.value_objects.enums import (
    ConfidenceLevel,
    RucSourceType,
    StalenessLevel,
)


class RucStalenessPolicy:
    """Calculates data age and staleness level."""

    WARNING_AGE_DAYS = 15
    STALE_AGE_DAYS = 30
    CRITICAL_AGE_DAYS = 60

    @classmethod
    def evaluate(cls, source_published_at: datetime | None, fetched_at: datetime) -> tuple[int | None, StalenessLevel, bool]:
        ref_time = source_published_at or fetched_at
        if not ref_time:
            return None, StalenessLevel.UNKNOWN, True

        now = datetime.now(timezone.utc)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        age_days = max(0, (now - ref_time).days)

        if age_days <= cls.WARNING_AGE_DAYS:
            level = StalenessLevel.FRESH
            is_stale = False
        elif age_days <= cls.STALE_AGE_DAYS:
            level = StalenessLevel.AGING
            is_stale = False
        elif age_days <= cls.CRITICAL_AGE_DAYS:
            level = StalenessLevel.STALE
            is_stale = True
        else:
            level = StalenessLevel.CRITICAL
            is_stale = True

        return age_days, level, is_stale


class RucConfidencePolicy:
    """Calculates confidence level based on source, age, and verification status."""

    @classmethod
    def calculate(cls, source_type: RucSourceType, staleness_level: StalenessLevel) -> ConfidenceLevel:
        if source_type in (RucSourceType.SUNAT_REDUCED_REGISTRY, RucSourceType.SUNAT_REDUCED_ANNEX_REGISTRY):
            if staleness_level in (StalenessLevel.FRESH, StalenessLevel.AGING):
                return ConfidenceLevel.HIGH
            elif staleness_level == StalenessLevel.STALE:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW

        if source_type == RucSourceType.AUTHORIZED_PROVIDER:
            if staleness_level in (StalenessLevel.FRESH, StalenessLevel.AGING):
                return ConfidenceLevel.HIGH
            return ConfidenceLevel.MEDIUM

        if source_type == RucSourceType.ASSISTED_OFFICIAL_REVIEW:
            return ConfidenceLevel.MEDIUM

        if source_type == RucSourceType.BUSINESS_PARTNER_DECLARED:
            return ConfidenceLevel.LOW

        return ConfidenceLevel.LOW


class RucFieldProvenanceBuilder:
    """Builds field-level provenance dictionary."""

    @classmethod
    def build_field(
        cls,
        field_name: str,
        value: Any,
        source: RucSourceType,
        source_reference: str,
        source_date: datetime | None,
        confidence_level: ConfidenceLevel,
        is_stale: bool,
    ) -> Dict[str, Any]:
        return {
            "field_name": field_name,
            "value": value,
            "source": source.value,
            "source_reference": source_reference,
            "source_date": source_date.isoformat() if source_date else None,
            "confidence_level": confidence_level.value,
            "is_stale": is_stale,
            "selected": True,
            "conflict_status": "NONE",
        }
