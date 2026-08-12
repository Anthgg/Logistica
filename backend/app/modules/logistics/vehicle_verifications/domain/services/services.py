"""Domain Services for Phase 028 — Vehicle Verifications."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.database.base import utc_now
from app.modules.logistics.vehicle_verifications.domain.value_objects.enums import (
    ConfidenceLevel,
    ConflictSeverity,
    ConflictStatus,
    ConflictType,
    StalenessStatus,
    VerificationComplianceStatus,
    VerificationDomain,
    VerificationResultStatus,
    VerificationStatus,
)


class VehicleVerificationNormalizer:
    @staticmethod
    def mask_identifier(val: Optional[str]) -> Optional[str]:
        if not val:
            return None
        val_clean = val.strip()
        if len(val_clean) <= 4:
            return "***" + val_clean[-2:]
        return "***" + val_clean[-4:]

    @staticmethod
    def mask_vin(vin: Optional[str]) -> Optional[str]:
        if not vin:
            return None
        clean_vin = vin.strip().upper()
        if len(clean_vin) < 6:
            return "***" + clean_vin
        return "***" + clean_vin[-4:]

    @staticmethod
    def calculate_hash(data: Dict[str, Any]) -> str:
        dumped = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


@dataclass
class DetectedConflict:
    conflict_type: ConflictType
    master_display: str
    verified_display: str
    severity: str  # HIGH, MEDIUM, LOW


class VehicleVerificationConflictDetector:
    @staticmethod
    def detect_conflicts(
        master_plate: str,
        master_vin: Optional[str],
        master_make: Optional[str],
        master_model: Optional[str],
        master_year: Optional[int],
        verified_plate: Optional[str],
        verified_vin: Optional[str],
        verified_make: Optional[str],
        verified_model: Optional[str],
        verified_year: Optional[int],
        verified_status: Optional[str],
    ) -> List[DetectedConflict]:
        conflicts = []

        # Plate check
        if verified_plate:
            norm_m = master_plate.replace("-", "").strip().upper()
            norm_v = verified_plate.replace("-", "").strip().upper()
            if norm_m != norm_v:
                conflicts.append(
                    DetectedConflict(
                        conflict_type=ConflictType.PLATE_MISMATCH,
                        master_display=master_plate,
                        verified_display=verified_plate,
                        severity="HIGH",
                    )
                )

        # Make check
        if verified_make and master_make:
            if master_make.strip().upper() != verified_make.strip().upper():
                conflicts.append(
                    DetectedConflict(
                        conflict_type=ConflictType.MAKE_MISMATCH,
                        master_display=master_make,
                        verified_display=verified_make,
                        severity="MEDIUM",
                    )
                )

        # Model check
        if verified_model and master_model:
            if master_model.strip().upper() != verified_model.strip().upper():
                conflicts.append(
                    DetectedConflict(
                        conflict_type=ConflictType.MODEL_MISMATCH,
                        master_display=master_model,
                        verified_display=verified_model,
                        severity="MEDIUM",
                    )
                )

        # Year check
        if verified_year and master_year:
            if master_year != verified_year:
                conflicts.append(
                    DetectedConflict(
                        conflict_type=ConflictType.YEAR_MISMATCH,
                        master_display=str(master_year),
                        verified_display=str(verified_year),
                        severity="LOW",
                    )
                )

        # VIN check
        if verified_vin and master_vin:
            norm_m_vin = master_vin.strip().upper()
            norm_v_vin = verified_vin.strip().upper()
            if norm_m_vin[-4:] != norm_v_vin[-4:]:
                conflicts.append(
                    DetectedConflict(
                        conflict_type=ConflictType.VIN_MISMATCH,
                        master_display=VehicleVerificationNormalizer.mask_vin(master_vin),
                        verified_display=VehicleVerificationNormalizer.mask_vin(verified_vin),
                        severity="HIGH",
                    )
                )

        return conflicts


class VehicleVerificationStalenessPolicy:
    @staticmethod
    def evaluate_staleness(
        source_data_at: Optional[datetime],
        expires_at: Optional[datetime],
        warning_age_days: int = 30,
        stale_age_days: int = 90,
        critical_age_days: int = 180,
    ) -> StalenessStatus:
        now = utc_now()

        # Check explicit expiration first
        if expires_at and expires_at < now:
            return StalenessStatus.EXPIRED

        if not source_data_at:
            return StalenessStatus.UNKNOWN

        age_days = (now - source_data_at).days

        if age_days < warning_age_days:
            return StalenessStatus.FRESH
        elif age_days < stale_age_days:
            return StalenessStatus.AGING
        elif age_days < critical_age_days:
            return StalenessStatus.STALE
        else:
            return StalenessStatus.CRITICAL


@dataclass
class VerificationComplianceResult:
    compliance_status: VerificationComplianceStatus
    required_domains: List[str]
    completed_domains: List[str]
    missing_domains: List[str]
    expired_domains: List[str]
    stale_domains: List[str]
    has_open_conflicts: bool
    blocking_reasons: List[str]
    warnings: List[str]


class VehicleVerificationComplianceResolver:
    @staticmethod
    def resolve_compliance(
        required_requirements: List[Tuple[str, bool, int]],  # (domain, blocking, max_age_days)
        verifications_summary: List[Tuple[str, str, datetime, Optional[datetime], str]],  # (domain, status, source_at, expires_at, result_status)
        has_open_conflicts: bool,
    ) -> VerificationComplianceResult:
        now = utc_now()
        req_map = {domain: (blocking, max_age) for domain, blocking, max_age in required_requirements}
        required_domains = list(req_map.keys())

        completed_domains = []
        missing_domains = []
        expired_domains = []
        stale_domains = []
        blocking_reasons = []
        warnings = []

        verif_by_domain = {}
        for domain, status, source_at, expires_at, res_status in verifications_summary:
            if status == VerificationStatus.COMPLETED.value:
                verif_by_domain[domain] = (source_at, expires_at, res_status)

        for req_dom, (blocking, max_age) in req_map.items():
            if req_dom not in verif_by_domain:
                missing_domains.append(req_dom)
                msg = f"Falta verificación obligatoria para el dominio '{req_dom}'."
                if blocking:
                    blocking_reasons.append(msg)
                else:
                    warnings.append(msg)
            else:
                source_at, expires_at, res_status = verif_by_domain[req_dom]

                if expires_at and expires_at < now:
                    expired_domains.append(req_dom)
                    msg = f"La verificación del dominio '{req_dom}' está vencida (expiró en {expires_at.strftime('%Y-%m-%d')})."
                    if blocking:
                        blocking_reasons.append(msg)
                    else:
                        warnings.append(msg)
                elif res_status in [VerificationResultStatus.INVALID.value, VerificationResultStatus.EXPIRED.value, VerificationResultStatus.SUSPENDED.value]:
                    expired_domains.append(req_dom)
                    msg = f"La verificación del dominio '{req_dom}' retornó resultado no válido/suspendido: {res_status}."
                    if blocking:
                        blocking_reasons.append(msg)
                    else:
                        warnings.append(msg)
                else:
                    age_days = (now - source_at).days if source_at else 0
                    if age_days > max_age:
                        stale_domains.append(req_dom)
                        warnings.append(f"La verificación del dominio '{req_dom}' está desactualizada ({age_days} días > máximo {max_age} días).")
                    else:
                        completed_domains.append(req_dom)

        if has_open_conflicts:
            warnings.append("Existen conflictos abiertos entre los datos verificados y el maestro vehicular.")

        # Resolve overall status
        if blocking_reasons:
            if expired_domains:
                status = VerificationComplianceStatus.EXPIRED
            else:
                status = VerificationComplianceStatus.NON_COMPLIANT
        elif has_open_conflicts:
            status = VerificationComplianceStatus.CONFLICTED
        elif missing_domains or stale_domains:
            status = VerificationComplianceStatus.PARTIALLY_COMPLIANT
        elif required_domains:
            status = VerificationComplianceStatus.COMPLIANT
        else:
            status = VerificationComplianceStatus.NOT_EVALUATED

        return VerificationComplianceResult(
            compliance_status=status,
            required_domains=required_domains,
            completed_domains=completed_domains,
            missing_domains=missing_domains,
            expired_domains=expired_domains,
            stale_domains=stale_domains,
            has_open_conflicts=has_open_conflicts,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )
