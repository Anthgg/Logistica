# Estructura del Modelo Central `VehicleModel`

## 1. Definición del Modelo ORM

El modelo `VehicleModel` es la entidad raíz del módulo de vehículos en `app/models/logistics/vehicle.py`. Define los campos de identificación física, legal, clasificación tipológica y máquinas de estado para el ciclo de vida y la operación.

```python
class VehicleModel(Base, TimestampMixin, AuditMixin):
    __tablename__ = "logistics_vehicles"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    
    # Identificadores principales
    vehicle_code: Mapped[str] = mapped_column(String(32), nullable=False)
    normalized_vehicle_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    
    display_plate: Mapped[str] = mapped_column(String(16), nullable=False)
    normalized_plate: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    
    vin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    normalized_vin: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    
    chassis_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    engine_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Clasificación y Jerarquía
    make_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("logistics_vehicle_makes.id"), nullable=False)
    model_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("logistics_vehicle_models.id"), nullable=False)
    
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    body_type: Mapped[VehicleBodyType] = mapped_column(Enum(VehicleBodyType), nullable=False)
    
    # Máquinas de Estado
    lifecycle_status: Mapped[VehicleLifecycleStatus] = mapped_column(
        Enum(VehicleLifecycleStatus), nullable=False, default=VehicleLifecycleStatus.DRAFT
    )
    operational_status: Mapped[VehicleOperationalStatus] = mapped_column(
        Enum(VehicleOperationalStatus), nullable=False, default=VehicleOperationalStatus.UNAVAILABLE
    )
    compliance_status: Mapped[VehicleComplianceStatus] = mapped_column(
        Enum(VehicleComplianceStatus), nullable=False, defaultVehicleComplianceStatus.PENDING_REVIEW
    )
    
    # Control Concurrente
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
```

---

## 2. Descripción de Campos Clave

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `vehicle_code` | `String(32)` | NOT NULL | Código interno asignado por la empresa (ej: `FL-001`). |
| `normalized_vehicle_code` | `String(32)` | INDEX | Código limpio en mayúsculas sin guiones ni caracteres especiales para búsqueda rápida. |
| `display_plate` | `String(16)` | NOT NULL | Placa formateada visualmente para impresión/pantalla (ej: `ABC-123`). |
| `normalized_plate` | `String(16)` | INDEX | Placa canonizada en mayúsculas sin espacios/guiones (ej: `ABC123`). Clave de unicidad por organización. |
| `vin` | `String(32)` | NULLABLE | Número de Identificación Vehicular (17 caracteres ISO 3779). |
| `normalized_vin` | `String(32)` | INDEX | VIN canonizado en mayúsculas. Clave de unicidad global cuando está presente. |
| `make_id` | `UUID` | FK | Referencia a la marca del vehículo (`VehicleMakeModel`). |
| `model_id` | `UUID` | FK | Referencia al modelo específico (`VehicleModelModel`). |
| `vehicle_type` | `Enum` | NOT NULL | Clasificación estructural: `RIGID_TRUCK`, `TRACTO_TRUCK`, `SEMI_TRAILER`, `TRAILER`, `VAN`, `PICKUP`. |
| `body_type` | `Enum` | NOT NULL | Tipo de carrocería: `DRY_VAN`, `REFRIGERATED`, `FLATBED`, `TANKER`, `CURTAINSIDER`, `CISTERNA`. |
| `row_version` | `Integer` | NOT NULL | Contador de versión para control de concurrencia optimista. |

---

## 3. Máquinas de Estado y Enums

### 3.1 Status de Ciclo de Vida (`VehicleLifecycleStatus`)
* `DRAFT`: Registro inicial incompleto, en proceso de parametrización.
* `ACTIVE`: Vehículo plenamente habilitado en el maestro operativo.
* `SUSPENDED`: Deshabilitado temporalmente por decisión administrativa.
* `RETIRED`: Dado de baja definitiva de la flota (venta, chatarreo, siniestro total).

### 3.2 Status Operativo (`VehicleOperationalStatus`)
* `AVAILABLE`: Listo para asignación de viajes y maniobras de carga.
* `MAINTENANCE`: En taller por mantenimiento preventivo o correctivo.
* `DOCUMENTS_EXPIRED`: Inhabilitado automáticamente por vencimiento de SOAT/CITV/Permisos.
* `BLOCKED`: Inhabilitado por restricción manual administrativa o sanción de seguridad.
* `UNAVAILABLE`: En viaje activo o fuera de turno operativo.

### 3.3 Status de Cumplimiento (`VehicleComplianceStatus`)
* `COMPLIANT`: Todos los documentos legales exigidos están vigentes y validados.
* `NON_COMPLIANT`: Al menos un documento obligatorio está vencido, rechazado o ausente.
* `WARNING`: Documentos próximos a vencer dentro de la ventana de alerta (ej: 15 días).
* `PENDING_REVIEW`: Expediente documental recién cargado pendiente de revisión por auditoría.
