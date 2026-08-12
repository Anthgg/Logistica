"""Domain services for Vehicle code, plate, VIN, operational status, snapshot, and duplicate detection."""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.modules.logistics.vehicles.domain.value_objects.enums import (
    VehicleComplianceStatus,
    VehicleLifecycleStatus,
    VehicleOperationalStatus,
)


class VehicleCodeService:
    """Generates and validates sequential vehicle codes (e.g. VEH-000001)."""

    PREFIX = "VEH"
    PADDING = 6

    @classmethod
    def format_code(cls, sequence_num: int) -> str:
        return f"{cls.PREFIX}-{sequence_num:0{cls.PADDING}d}"

    @classmethod
    def normalize(cls, code: str) -> str:
        return code.strip().upper()


class VehiclePlateService:
    """Normalizes and formats license plates."""

    @classmethod
    def normalize(cls, display_plate: str) -> str:
        if not display_plate:
            return ""
        # Remove spaces and dashes for normalized plate index
        return re.sub(r"[^A-Z0-9]", "", display_plate.strip().upper())

    @classmethod
    def format_display(cls, raw_plate: str) -> str:
        norm = cls.normalize(raw_plate)
        if len(norm) == 6:
            # Format Peruvian standard ABC-123
            return f"{norm[:3]}-{norm[3:]}"
        return norm

    @classmethod
    def validate_format(cls, raw_plate: str) -> bool:
        norm = cls.normalize(raw_plate)
        return len(norm) >= 3 and len(norm) <= 15 and norm.isalnum()


class VehicleVinService:
    """Normalizes and masks VIN identifiers."""

    @classmethod
    def normalize(cls, vin: str | None) -> str | None:
        if not vin:
            return None
        clean = re.sub(r"[^A-Z0-9]", "", vin.strip().upper())
        return clean if clean else None

    @classmethod
    def mask_vin(cls, vin: str | None) -> str | None:
        if not vin:
            return None
        norm = cls.normalize(vin)
        if not norm or len(norm) <= 4:
            return "****"
        return f"***{norm[-4:]}"

    @classmethod
    def validate_format(cls, vin: str | None) -> bool:
        if not vin:
            return True
        norm = cls.normalize(vin)
        return norm is not None and len(norm) >= 11 and len(norm) <= 17


class VehicleOperationalStatusResolver:
    """Derives operational status and document compliance from vehicle state and metadata."""

    @classmethod
    def resolve(
        cls,
        lifecycle_status: str,
        is_blocked: bool,
        is_maintenance: bool,
        has_active_carrier: bool,
        has_expired_required_docs: bool,
        has_missing_required_docs: bool,
    ) -> Tuple[VehicleOperationalStatus, VehicleComplianceStatus, List[str]]:
        blocking_reasons = []

        if lifecycle_status == VehicleLifecycleStatus.RETIRED.value:
            return VehicleOperationalStatus.RETIRED, VehicleComplianceStatus.NON_COMPLIANT, ["Vehículo retirado permanentemente."]

        if lifecycle_status == VehicleLifecycleStatus.SUSPENDED.value:
            return VehicleOperationalStatus.UNAVAILABLE, VehicleComplianceStatus.NON_COMPLIANT, ["Vehículo suspendido administrativamente."]

        if is_blocked:
            return VehicleOperationalStatus.BLOCKED, VehicleComplianceStatus.NON_COMPLIANT, ["Vehículo bloqueado manualmente."]

        if is_maintenance:
            return VehicleOperationalStatus.MAINTENANCE, VehicleComplianceStatus.WARNING, ["Vehículo en mantenimiento manual."]

        if has_expired_required_docs:
            return VehicleOperationalStatus.DOCUMENTS_EXPIRED, VehicleComplianceStatus.EXPIRED_DOCUMENTS, ["Documentos obligatorios vencidos."]

        if has_missing_required_docs:
            return VehicleOperationalStatus.DOCUMENTS_INCOMPLETE, VehicleComplianceStatus.NON_COMPLIANT, ["Faltan documentos obligatorios."]

        if not has_active_carrier:
            return VehicleOperationalStatus.UNAVAILABLE, VehicleComplianceStatus.WARNING, ["Vehículo no tiene transportista activo asignado."]

        if lifecycle_status == VehicleLifecycleStatus.ACTIVE.value:
            return VehicleOperationalStatus.AVAILABLE, VehicleComplianceStatus.COMPLIANT, []

        return VehicleOperationalStatus.UNAVAILABLE, VehicleComplianceStatus.PENDING_REVIEW, ["Vehículo en estado Borrador o Inactivo."]


class VehicleSnapshotProvider:
    """Calculates canonical SHA-256 hash and snapshot dictionary for vehicle versioning."""

    @classmethod
    def build_snapshot_payload(
        cls,
        vehicle_code: str,
        plate: str,
        vin: str | None,
        make_name: str,
        model_name: str,
        vehicle_type: str,
        body_type: str,
        capacity_dict: Dict[str, Any] | None,
        dimensions_dict: Dict[str, Any] | None,
        owner_dict: Dict[str, Any] | None,
        carrier_dict: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        return {
            "vehicle_code": vehicle_code,
            "plate": plate,
            "masked_vin": VehicleVinService.mask_vin(vin),
            "make": make_name,
            "model": model_name,
            "vehicle_type": vehicle_type,
            "body_type": body_type,
            "capacity": capacity_dict or {},
            "dimensions": dimensions_dict or {},
            "owner": owner_dict or {},
            "carrier": carrier_dict or {},
        }

    @classmethod
    def calculate_content_hash(cls, payload: Dict[str, Any]) -> str:
        json_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
