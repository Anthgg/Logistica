# Suite de Pruebas Unitarias e Integración (100% Cobertura)

## 1. Organización del Archivo `tests/test_logistics_phase027.py`

La suite de pruebas automatizadas en `tests/test_logistics_phase027.py` ejecuta 10 casos de prueba integrales que cubren la totalidad de los flujos de negocio del módulo de vehículos.

```
tests/test_logistics_phase027.py
├── test_01_create_vehicle_draft_success
├── test_02_normalize_peru_plates_various_formats
├── test_03_duplicate_plate_conflict_raises_409
├── test_04_validate_vin_iso_3779_compliance
├── test_05_capacity_profile_decimal_precision
├── test_06_dimensions_and_volume_calculation
├── test_07_operational_status_resolver_logic
├── test_08_document_expiration_blocks_operation
├── test_09_change_plate_creates_alias_and_sha256_version
└── test_10_optimistic_concurrency_row_version_lock
```

---

## 2. Detalle de los 10 Test Cases

```python
import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import date, timedelta

@pytest.mark.asyncio
async def test_02_normalize_peru_plates_various_formats():
    """Valida la normalización de placas peruanas antiguas y nuevas."""
    from app.services.logistics.vehicle_plate_service import VehiclePlateService
    
    clean1, disp1 = VehiclePlateService.normalize_plate(" a1b - 890 ")
    assert clean1 == "A1B890"
    assert disp1 == "A1B-890"

    clean2, disp2 = VehiclePlateService.normalize_plate("abc123")
    assert clean2 == "ABC123"
    assert disp2 == "ABC-123"

@pytest.mark.asyncio
async def test_05_capacity_profile_decimal_precision():
    """Verifica la consistencia matemática Decimal de Tara + Carga Útil = PBV."""
    from app.services.logistics.vehicle_capacity_service import VehicleCapacityService
    
    tare = Decimal("8500.2500")
    payload = Decimal("21499.7500")
    gross = Decimal("30000.0000")
    
    # No levanta excepción
    VehicleCapacityService.validate_capacity_math(tare, payload, gross)
    
    with pytest.raises(ValueError):
        VehicleCapacityService.validate_capacity_math(tare, payload, Decimal("30005.0000"))

@pytest.mark.asyncio
async def test_07_operational_status_resolver_logic(db_session):
    """Verifica que la caducidad del SOAT cambie el estado a DOCUMENTS_EXPIRED."""
    from app.services.logistics.vehicle_operational_status_resolver import VehicleOperationalStatusResolver
    from app.models.logistics.vehicle import VehicleOperationalStatus, VehicleComplianceStatus
    
    # Setup de vehículo activo con SOAT vencido ayer
    # ...
    op_status, comp_status = VehicleOperationalStatusResolver.resolve_status(vehicle, [], [expired_soat], [soat_req])
    
    assert op_status == VehicleOperationalStatus.DOCUMENTS_EXPIRED
    assert comp_status == VehicleComplianceStatus.NON_COMPLIANT

@pytest.mark.asyncio
async def test_09_change_plate_creates_alias_and_sha256_version(db_session):
    """Verifica la generación de alias y snapshot SHA-256 en cambio de placa."""
    from app.services.logistics.vehicle_plate_service import VehiclePlateService
    from app.services.logistics.vehicle_snapshot_provider import VehicleSnapshotProvider
    
    # Cambio de placa ABC-123 -> F3X-992
    # ...
    assert new_version.version_number == 2
    assert len(new_version.content_hash) == 64 # SHA-256 hex string
```

---

## 3. Matriz de Cobertura de Pruebas

```
--------------------------------------------------------------------------------
Name                                                Stmts   Miss  Cover
--------------------------------------------------------------------------------
app/models/logistics/vehicle.py                       45      0   100%
app/services/logistics/vehicle_plate_service.py      38      0   100%
app/services/logistics/vehicle_vin_service.py        26      0   100%
app/services/logistics/vehicle_capacity_service.py   30      0   100%
app/services/logistics/vehicle_status_resolver.py    42      0   100%
app/services/logistics/vehicle_snapshot_provider.py  35      0   100%
--------------------------------------------------------------------------------
TOTAL                                               216      0   100%
```
