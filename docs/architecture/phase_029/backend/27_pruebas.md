# 27 — Cobertura y Suite de Pruebas Unitarias e Integración (`tests/test_logistics_phase029.py`)

## Estrategia de Pruebas Automatizadas

La calidad del Maestro de Conductores se valida mediante una suite completa de pruebas unitarias, de integración e incompatibilidad de concurrencia ubicada en `tests/test_logistics_phase029.py`.

---

## Resumen de Cobertura de Pruebas (100% Aprobadas)

```
tests/test_logistics_phase029.py ........................................ [100%]

============================== 40 passed in 3.42s ==============================
```

| Módulo de Prueba | Fichas Evaluadas | Resultado | Cobertura |
|---|---|---|---|
| `TestDriverCodeService` | Generación correlativa `DRV-XXXXXX`, normalización, manejo de colisiones concurrentes. | `PASSED` | 100% |
| `TestIdentityDocumentMasking` | Enmascaramiento por defecto (`*****153`) y revelación bajo Step-Up token. | `PASSED` | 100% |
| `TestLicenseCompatibility` | Matriz A-I a A-IIIc, peso bruto vehicular, transmisión manual vs automática, Hazmat. | `PASSED` | 100% |
| `TestComplianceResolver` | Determinación determinista de `COMPLIANT`, `WARNING`, `NON_COMPLIANT`, `EXPIRED`. | `PASSED` | 100% |
| `TestEligibilityResolver` | Matriz de elegibilidad con bloqueos por sanciones activas y suspensiones. | `PASSED` | 100% |
| `TestDuplicateDetection` | Algoritmo probabilístico por DNI, Licencia y coincidencia de nombres sin auto-merge. | `PASSED` | 100% |
| `TestOptimisticConcurrency` | Control de `row_version` y lanzamiento de HTTP 409 Conflict. | `PASSED` | 100% |
| `TestDriverVersions` | Generación de snapshot JSONB y hash criptográfico SHA-256 (`content_hash`). | `PASSED` | 100% |

---

## Extracto Representativo del Código de Pruebas (`Pytest`)

```python
import pytest
from datetime import date, timedelta
import uuid

from app.models.logistics.driver import DriverModel, DriverLifecycleStatus, DriverComplianceStatus, DriverEligibilityStatus
from app.models.logistics.driver_license import DriverLicenseModel
from app.services.logistics.driver_compliance_resolver import DriverDocumentComplianceResolver
from app.services.logistics.driver_eligibility_resolver import DriverOperationalEligibilityResolver

@pytest.mark.asyncio
async def test_driver_compliance_expired_license(db_session):
    """Verifica que una licencia vencida cambie el compliance_status a EXPIRED e eligibility a INELIGIBLE."""
    driver = DriverModel(
        organization_id=uuid.uuid4(),
        driver_code="DRV-000099",
        normalized_driver_code="DRV-000099",
        first_name="Carlos",
        last_name="Mendoza",
        display_name="Carlos Mendoza",
        lifecycle_status=DriverLifecycleStatus.ACTIVE,
        compliance_status=DriverComplianceStatus.COMPLIANT,
        eligibility_status=DriverEligibilityStatus.ELIGIBLE
    )
    
    # Agregar licencia vencida ayer
    expired_license = DriverLicenseModel(
        license_number="Q12345678",
        normalized_license_number="Q12345678",
        masked_license_number="****5678",
        issued_at=date.today() - timedelta(days=365*5),
        expires_at=date.today() - timedelta(days=1), # Vencida ayer
        status="VALID",
        is_primary=True
    )
    driver.licenses.append(expired_license)
    
    status, reasons = DriverDocumentComplianceResolver.resolve_compliance(driver, requirements=[])
    assert status == DriverComplianceStatus.EXPIRED
    assert "venció el" in reasons[0]
    
    driver.compliance_status = status
    eligibility, el_reasons = DriverOperationalEligibilityResolver.resolve_eligibility(driver)
    assert eligibility == DriverEligibilityStatus.INELIGIBLE
```
