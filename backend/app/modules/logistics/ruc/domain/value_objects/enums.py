"""Domain Value Objects and Enums for Phase 026 (RUC Lookup)."""

from enum import Enum


class TaxpayerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    TEMPORARY_DEREGISTRATION = "TEMPORARY_DEREGISTRATION"
    DEFINITIVE_DEREGISTRATION = "DEFINITIVE_DEREGISTRATION"
    PROVISIONAL_DEREGISTRATION = "PROVISIONAL_DEREGISTRATION"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def normalize_raw(cls, raw: str | None) -> "TaxpayerStatus":
        if not raw:
            return cls.UNKNOWN
        val = raw.strip().upper()
        if "ACTIVO" in val:
            return cls.ACTIVE
        if "SUSPENSION" in val or "SUSPENDIDO" in val:
            return cls.SUSPENDED
        if "TEMPORAL" in val:
            return cls.TEMPORARY_DEREGISTRATION
        if "DEFINITIV" in val or "BAJA" in val:
            return cls.DEFINITIVE_DEREGISTRATION
        if "PROVISIONAL" in val:
            return cls.PROVISIONAL_DEREGISTRATION
        return cls.UNKNOWN


class DomicileCondition(str, Enum):
    HABIDO = "HABIDO"
    NO_HABIDO = "NO_HABIDO"
    PENDING = "PENDING"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def normalize_raw(cls, raw: str | None) -> "DomicileCondition":
        if not raw:
            return cls.UNKNOWN
        val = raw.strip().upper()
        if "HABIDO" in val and "NO" not in val:
            return cls.HABIDO
        if "NO HABIDO" in val or "NO_HABIDO" in val or "NO HALLADO" in val:
            return cls.NO_HABIDO
        if "PENDIENTE" in val:
            return cls.PENDING
        if "NO ENCONTRADO" in val:
            return cls.NOT_FOUND
        return cls.UNKNOWN


class StalenessLevel(str, Enum):
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_EVALUATED = "NOT_EVALUATED"


class RucSourceType(str, Enum):
    SUNAT_REDUCED_REGISTRY = "SUNAT_REDUCED_REGISTRY"
    SUNAT_REDUCED_ANNEX_REGISTRY = "SUNAT_REDUCED_ANNEX_REGISTRY"
    AUTHORIZED_PROVIDER = "AUTHORIZED_PROVIDER"
    ASSISTED_OFFICIAL_REVIEW = "ASSISTED_OFFICIAL_REVIEW"
    BUSINESS_PARTNER_DECLARED = "BUSINESS_PARTNER_DECLARED"
    LEGACY_IMPORT = "LEGACY_IMPORT"
    UNKNOWN = "UNKNOWN"
