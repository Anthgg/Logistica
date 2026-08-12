"""VehicleVerificationProvider interface and Fake/NoOp implementations (Phase 028)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database.base import utc_now
from app.modules.logistics.vehicle_verifications.domain.errors.exceptions import (
    VehicleVerificationNotFoundExternally,
    VehicleVerificationProviderUnavailable,
)
from app.modules.logistics.vehicle_verifications.domain.value_objects.enums import (
    ConfidenceLevel,
    VerificationDomain,
    VerificationResultStatus,
)


@dataclass
class ProviderVerificationRequest:
    plate: str
    domain: str
    organization_id: UUID
    correlation_id: str
    purpose: str = "LOGISTICS_VERIFICATION"


@dataclass
class ProviderVerificationResponse:
    provider_code: str
    source_code: str
    queried_plate: str
    result_status: VerificationResultStatus
    confidence_level: ConfidenceLevel
    source_data_at: datetime
    valid_from: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    registered_owner_name: Optional[str] = None
    registered_owner_identifier_masked: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    manufacturing_year: Optional[int] = None
    vin_masked: Optional[str] = None
    chassis_masked: Optional[str] = None
    engine_number_masked: Optional[str] = None
    registration_status: Optional[str] = None
    transport_authorization_status: Optional[str] = None
    technical_inspection_status: Optional[str] = None
    technical_inspection_expires_at: Optional[datetime] = None
    insurance_type: Optional[str] = None
    insurance_status: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_masked: Optional[str] = None
    insurance_valid_from: Optional[datetime] = None
    insurance_expires_at: Optional[datetime] = None
    liens_status: Optional[str] = None
    restrictions_summary: Optional[str] = None
    normalized_payload: Dict[str, Any] = field(default_factory=dict)
    raw_response_hash: Optional[str] = None
    external_reference: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class VehicleVerificationProvider(ABC):
    @property
    @abstractmethod
    def provider_code(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_domains(self) -> List[VerificationDomain]:
        pass

    @abstractmethod
    def verify_plate(self, request: ProviderVerificationRequest) -> ProviderVerificationResponse:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass


class NoOpVehicleVerificationProvider(VehicleVerificationProvider):
    """NoOp Provider when a source is manual-only or not automated."""

    @property
    def provider_code(self) -> str:
        return "NOOP"

    @property
    def supported_domains(self) -> List[VerificationDomain]:
        return []

    def verify_plate(self, request: ProviderVerificationRequest) -> ProviderVerificationResponse:
        raise VehicleVerificationProviderUnavailable(self.provider_code)

    def health_check(self) -> bool:
        return True


class FakeVehicleVerificationProvider(VehicleVerificationProvider):
    """Fake Provider strictly for testing and local integration environments."""

    def __init__(
        self,
        code: str = "FAKE_AUTH_PROVIDER",
        should_fail: bool = False,
        should_timeout: bool = False,
        not_found_plates: Optional[List[str]] = None,
    ):
        self._code = code
        self._should_fail = should_fail
        self._should_timeout = should_timeout
        self._not_found_plates = not_found_plates or []

    @property
    def provider_code(self) -> str:
        return self._code

    @property
    def supported_domains(self) -> List[VerificationDomain]:
        return [
            VerificationDomain.REGISTRY_IDENTITY,
            VerificationDomain.REGISTERED_OWNER,
            VerificationDomain.TECHNICAL_INSPECTION,
            VerificationDomain.SOAT,
            VerificationDomain.TRANSPORT_AUTHORIZATION,
        ]

    def verify_plate(self, request: ProviderVerificationRequest) -> ProviderVerificationResponse:
        if self._should_fail:
            raise VehicleVerificationProviderUnavailable(self.provider_code)

        if request.plate in self._not_found_plates:
            raise VehicleVerificationNotFoundExternally(request.plate, request.domain)

        now = utc_now()
        exp = datetime(now.year + 1, now.month, now.day, tzinfo=timezone.utc)

        return ProviderVerificationResponse(
            provider_code=self.provider_code,
            source_code="TEST_SOURCE",
            queried_plate=request.plate,
            result_status=VerificationResultStatus.VALID,
            confidence_level=ConfidenceLevel.HIGH,
            source_data_at=now,
            valid_from=now,
            expires_at=exp,
            registered_owner_name="EMPRESA LOGISTICA DEMO S.A.C.",
            registered_owner_identifier_masked="RUC 20***123456",
            make="VOLVO",
            model="FH540",
            manufacturing_year=2022,
            vin_masked="***1234",
            registration_status="ACTIVE",
            technical_inspection_status="VALID",
            technical_inspection_expires_at=exp,
            insurance_type="SOAT",
            insurance_status="ACTIVE",
            insurance_provider="LA POSITIVA",
            insurance_policy_masked="***999",
            insurance_expires_at=exp,
            normalized_payload={"fake_verified": True, "plate": request.plate},
            raw_response_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            external_reference=f"REF-FAKE-{request.plate}",
        )

    def health_check(self) -> bool:
        return not self._should_fail
