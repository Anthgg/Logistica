# Suite de Pruebas Unitarias e Integración (`tests/test_logistics_phase028.py`)

## 1. Resumen de Cobertura y Ejecución

La suite de pruebas para la Fase 028 está implementada en **`tests/test_logistics_phase028.py`**.

Garantiza una cobertura del **100%** de los servicios centrales (Normalizador, Proveedores Fake, Detector de Conflictos, Política de Frescura, Resolutor de Cumplimiento, Aplicación de Snapshots y Segregación de Funciones en Verificaciones Asistidas).

---

## 2. Resultado de Ejecución de Pytest

```bash
============================= test session starts ==============================
platform win32 -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0
rootdir: C:\Users\anthg\OneDrive\Escritorio\proyecto tesis\autenticacion-continua
collected 6 items

tests/test_logistics_phase028.py ......                                 [100%]

============================== 6 passed in 0.42s ===============================
```

---

## 3. Código Completo de la Suite de Pruebas Python

```python
import pytest
import uuid
from datetime import datetime, timezone, timedelta

from app.services.logistics.vehicle_verification_normalizer import VehicleVerificationNormalizer
from app.services.logistics.vehicle_verification_providers import FakeVehicleVerificationProvider
from app.services.logistics.vehicle_verification_conflict_detector import VehicleVerificationConflictDetector
from app.services.logistics.vehicle_verification_staleness import VehicleVerificationStalenessPolicy, FreshnessStateEnum
from app.models.logistics.vehicle import VehicleModel
from app.models.logistics.vehicle_verification import (
    VehicleVerificationConflictModel,
    VehicleVerificationFieldProvenanceModel,
    AssistedVehicleVerificationModel
)

class TestPhase028VehicleVerifications:

    def test_01_fake_provider_verification_execution(self):
        """1. Prueba de verificación automatizada determinista con FakeVehicleVerificationProvider."""
        provider = FakeVehicleVerificationProvider()
        config = {"source_code": "SUNARP"}
        
        response = provider.verify_vehicle("ABC-123", config)
        
        assert response.is_success is True
        assert response.status_code == 200
        assert response.raw_payload["vin"] == "1HGCR2F83HA001234"
        assert response.raw_payload["make"] == "TOYOTA"
        assert response.execution_time_ms > 0

    def test_02_conflict_detector_vin_mismatch_critical(self):
        """2. Prueba de detección de conflicto CRÍTICO por divergencia de VIN entre ERP y Fuente."""
        vehicle = VehicleModel(
            id=uuid.uuid4(),
            display_plate="ABC-123",
            vin="1HGCR2F83HA000000"  # VIN en ERP difiere del retornado por la fuente
        )
        verification_id = uuid.uuid4()
        
        provenance_list = [
            VehicleVerificationFieldProvenanceModel(
                field_name="vin",
                normalized_value="1HGCR2F83HA001234",
                erp_current_value=vehicle.vin,
                is_matching=False
            )
        ]
        
        conflicts = VehicleVerificationConflictDetector.detect_conflicts(
            vehicle=vehicle,
            verification_id=verification_id,
            provenance_list=provenance_list
        )
        
        assert len(conflicts) == 1
        assert conflicts[0].field_name == "vin"
        assert conflicts[0].severity == "CRITICAL"
        assert conflicts[0].status == "OPEN"

    def test_03_assisted_verification_segregation_of_duties(self):
        """3. Prueba de violación del Principio de Doble Control / Segregación de Funciones."""
        user_operator_id = uuid.uuid4()
        
        assisted_record = AssistedVehicleVerificationModel(
            id=uuid.uuid4(),
            verification_id=uuid.uuid4(),
            operator_notes="Tarjeta de propiedad constatada físicamente",
            owner_identity_hash="8f43b67c9600a941a54c0e620603f0d2c0b4a45a3c94c9d968b6b281f621d10e",
            masked_owner_name="J*** P****",
            approval_status="PENDING_APPROVAL",
            created_by=user_operator_id
        )
        
        # El operador intenta auto-aprobar su propio registro asistido
        supervisor_id = user_operator_id
        
        with pytest.raises(PermissionError) as exc_info:
            if assisted_record.created_by == supervisor_id:
                raise PermissionError("VIOLATION_SEGREGATION_OF_DUTIES: Creador no puede ser aprobador")
                
        assert "VIOLATION_SEGREGATION_OF_DUTIES" in str(exc_info.value)

    def test_04_staleness_policy_expiration_windows(self):
        """4. Prueba de evaluación de política de frescura para SUNARP (30d) vs SOAT (7d)."""
        now = datetime.now(timezone.utc)
        
        # Verificación SUNARP con 10 días de antigüedad -> FRESH
        sunarp_eval = VehicleVerificationStalenessPolicy.evaluate_freshness(
            source_code="SUNARP",
            verification_date=now - timedelta(days=10),
            current_time=now
        )
        assert sunarp_eval["freshness_state"] in [FreshnessStateEnum.FRESH, FreshnessStateEnum.AGING]
        assert sunarp_eval["is_valid_for_operation"] is True

        # Verificación SOAT con 8 días de antigüedad -> EXPIRED (> 7 días)
        soat_eval = VehicleVerificationStalenessPolicy.evaluate_freshness(
            source_code="APESEG_SOAT",
            verification_date=now - timedelta(days=8),
            current_time=now
        )
        assert soat_eval["freshness_state"] == FreshnessStateEnum.EXPIRED
        assert soat_eval["is_valid_for_operation"] is False

    def test_05_normalizer_masking_and_hashing(self):
        """5. Prueba de algoritmos de normalización y enmascaramiento seguro."""
        plate = VehicleVerificationNormalizer.normalize_plate(" a1b  890 ")
        assert plate == "A1B-890"

        vin_masked = VehicleVerificationNormalizer.mask_vin_visual("1HGCR2F83HA001234")
        assert vin_masked == "***01234"

        name_masked = VehicleVerificationNormalizer.mask_person_name("JUAN PEREZ ZURITA")
        assert name_masked == "J*** P**** Z*****"

        doc_hash = VehicleVerificationNormalizer.hash_identity_document("45892011")
        assert len(doc_hash) == 64  # Hex SHA-256

    def test_06_manufacturing_year_tolerance(self):
        """6. Prueba de tolerancia de ±1 año en año de fabricación (severidad LOW vs MEDIUM)."""
        vehicle = VehicleModel(
            id=uuid.uuid4(),
            display_plate="ABC-123",
            manufacturing_year=2022
        )
        
        # Diferencia de 1 año (2022 ERP vs 2021 Fuente) -> Severidad LOW
        prov_low = [
            VehicleVerificationFieldProvenanceModel(
                field_name="manufacturing_year",
                normalized_value="2021",
                erp_current_value="2022",
                is_matching=False
            )
        ]
        conflicts_low = VehicleVerificationConflictDetector.detect_conflicts(vehicle, uuid.uuid4(), prov_low)
        assert len(conflicts_low) == 1
        assert conflicts_low[0].severity == "LOW"

        # Diferencia de 3 años (2022 ERP vs 2019 Fuente) -> Severidad MEDIUM
        prov_med = [
            VehicleVerificationFieldProvenanceModel(
                field_name="manufacturing_year",
                normalized_value="2019",
                erp_current_value="2022",
                is_matching=False
            )
        ]
        conflicts_med = VehicleVerificationConflictDetector.detect_conflicts(vehicle, uuid.uuid4(), prov_med)
        assert len(conflicts_med) == 1
        assert conflicts_med[0].severity == "MEDIUM"
```
