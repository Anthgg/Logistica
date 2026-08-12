"""Authorized RUC Enrichment Provider Adapter Interface & Test Fake."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.modules.logistics.ruc.domain.value_objects.enums import ConfidenceLevel, DomicileCondition, RucSourceType, TaxpayerStatus


class RucEnrichmentProvider(ABC):
    """Abstract contract for authorized external RUC enrichment providers."""

    @property
    @abstractmethod
    def provider_code(self) -> str:
        pass

    @abstractmethod
    def lookup(self, ruc: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass


class NoOpRucProvider(RucEnrichmentProvider):
    @property
    def provider_code(self) -> str:
        return "NOOP"

    def lookup(self, ruc: str) -> Optional[Dict[str, Any]]:
        return None

    def health_check(self) -> bool:
        return True


class FakeRucProvider(RucEnrichmentProvider):
    """Fake authorized provider used in test suite."""

    def __init__(self, simulate_failure: bool = False, simulate_not_found: bool = False):
        self.simulate_failure = simulate_failure
        self.simulate_not_found = simulate_not_found
        self.call_count = 0

    @property
    def provider_code(self) -> str:
        return "FAKE_AUTHORIZED_PROVIDER"

    def lookup(self, ruc: str) -> Optional[Dict[str, Any]]:
        self.call_count += 1
        if self.simulate_failure:
            raise Exception("Provider connection timeout.")
        if self.simulate_not_found:
            return None

        return {
            "ruc": ruc,
            "legal_name": f"EMPRESA PROVEEDOR AUTORIZADO {ruc} SAC",
            "taxpayer_status": TaxpayerStatus.ACTIVE.value,
            "domicile_condition": DomicileCondition.HABIDO.value,
            "ubigeo_code": "150101",
            "provider_code": self.provider_code,
            "source_type": RucSourceType.AUTHORIZED_PROVIDER.value,
            "confidence_level": ConfidenceLevel.HIGH.value,
        }

    def health_check(self) -> bool:
        return not self.simulate_failure
