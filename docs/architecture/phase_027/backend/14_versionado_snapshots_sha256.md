# Versionado Inmutable con Snapshots y Hashes SHA-256

## 1. Proveedor `VehicleSnapshotProvider` y Modelo `VehicleVersionModel`

Para garantizar la no repudiación, auditoría forense y trazabilidad histórica ante peritajes legales o inspecciones del MTC, la Fase 027 implementa un sistema de snapshots inmutables mediante el proveedor `VehicleSnapshotProvider` (`app/services/logistics/vehicle_snapshot_provider.py`) y la tabla `logistics_vehicle_versions` (`app/models/logistics/vehicle_version.py`).

Cada vez que el estado de un vehículo sufre una modificación estructural (cambio de placa, alteración de capacidades mecánicas, cambio de propietario o actualización documental), se genera una copia JSON completa del estado del vehículo en ese instante y se firma mediante un hash **SHA-256**.

---

## 2. Modelo `VehicleVersionModel`

```python
class VehicleVersionModel(Base, TimestampMixin):
    __tablename__ = "logistics_vehicle_versions"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("logistics_vehicles.id"), nullable=False, index=True)
    
    version_number: Mapped[int] = mapped_column(Integer, nullable=False) # Secuencial incremental por vehículo (1, 2, 3...)
    
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False) # Representación JSON serializada del vehículo completo
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False) # Hash SHA-256 hexadecimal del payload JSON
    
    change_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
```

---

## 3. Algoritmo de Generación de Snapshot SHA-256

El `VehicleSnapshotProvider` serializa el estado del vehículo en un formato JSON canónico determinista (claves ordenadas alfabéticamente) antes de calcular el compendio criptográfico.

```python
import hashlib
import json
from typing import Any

class VehicleSnapshotProvider:
    @classmethod
    def generate_sha256(cls, data: dict[str, Any]) -> str:
        """
        Genera el hash SHA-256 canónico del diccionario JSON.
        """
        canonical_json = json.dumps(data, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @classmethod
    def create_snapshot_payload(
        cls,
        vehicle: VehicleModel,
        capacity: VehicleCapacityProfileModel | None,
        dimensions: VehicleDimensionsModel | None,
        ownership: VehicleOwnershipAssignmentModel | None,
        carrier: VehicleCarrierAssignmentModel | None
    ) -> dict[str, Any]:
        return {
            "vehicle_id": str(vehicle.id),
            "organization_id": str(vehicle.organization_id),
            "vehicle_code": vehicle.vehicle_code,
            "normalized_plate": vehicle.normalized_plate,
            "vin": vehicle.vin,
            "vehicle_type": vehicle.vehicle_type.value if vehicle.vehicle_type else None,
            "body_type": vehicle.body_type.value if vehicle.body_type else None,
            "lifecycle_status": vehicle.lifecycle_status.value,
            "operational_status": vehicle.operational_status.value,
            "compliance_status": vehicle.compliance_status.value,
            "row_version": vehicle.row_version,
            "capacity": {
                "tare_weight": str(capacity.tare_weight) if capacity else None,
                "max_payload_weight": str(capacity.max_payload_weight) if capacity else None,
                "max_gross_weight": str(capacity.max_gross_weight) if capacity else None,
                "max_volume": str(capacity.max_volume) if capacity else None,
            } if capacity else None,
            "dimensions": {
                "overall_length": str(dimensions.overall_length) if dimensions else None,
                "overall_width": str(dimensions.overall_width) if dimensions else None,
                "overall_height": str(dimensions.overall_height) if dimensions else None,
            } if dimensions else None,
        }
```

---

## 4. Verificación de Integridad Físico-Criptográfica

Para validar que un registro en `logistics_vehicle_versions` no ha sido alterado o manipulado maliciosamente direct en la base de datos PostgreSQL:

$$\text{content\_hash} \stackrel{?}{=} \text{SHA256}(\text{CanonicalJSON}(\text{snapshot\_data}))$$

Si la re-evaluación del hash del JSON difiere del `content_hash` almacenado, el sistema levanta una alarma de violación de integridad de datos (`DataTamperingDetectedError`).
