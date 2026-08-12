# Gestor de Propiedad y Asignación Institucional

## 1. Servicio `VehicleOwnershipCarrierService`

El servicio `VehicleOwnershipCarrierService` (`app/services/logistics/vehicle_ownership_carrier_service.py`) gestiona las relaciones contractuales y la titularidad legal de las unidades de la flota.

Permite categorizar si un vehículo pertenece a la propia empresa, si se encuentra bajo contrato de arrendamiento financiero (Leasing), o si es operado por un tercero/proveedor logístico.

---

## 2. Tipos de Propiedad (`VehicleOwnershipType`)

```python
class VehicleOwnershipType(str, enum.Enum):
    OWNED = "OWNED"             # Vehículo propio (activo fijo de la organización)
    LEASED = "LEASED"           # Arrendamiento financiero / Leasing operativo con entidad bancaria
    THIRD_PARTY = "THIRD_PARTY" # Propiedad de un tercero / Socio de negocio (Subcontratado)
    RENTED = "RENTED"           # Alquiler temporal a corto plazo
```

---

## 3. Modelo `VehicleOwnershipAssignmentModel`

```python
class VehicleOwnershipAssignmentModel(Base, TimestampMixin):
    __tablename__ = "logistics_vehicle_ownership_assignments"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("logistics_vehicles.id"), nullable=False)
    
    ownership_type: Mapped[VehicleOwnershipType] = mapped_column(Enum(VehicleOwnershipType), nullable=False)
    
    owner_partner_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("logistics_business_partners.id"), nullable=True
    )
    
    contract_reference: Mapped[str | None] = mapped_column(String(64), nullable=True) # Nro de contrato de Leasing/Alquiler
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True) # NULL indica asignación vigente
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

---

## 4. Reglas de Validación y Superposición Temporal

1. **Sin Superposición Temporal**: Un vehículo no puede tener dos asignaciones de propiedad activas simultáneamente en un mismo rango de fechas `[effective_from, effective_to]`.
2. **Asignación Vigente Única**: Para cualquier instante $t$, solo puede existir un registro con `effective_to IS NULL` o `effective_to >= t`.
3. **Titular Externo**: Si `ownership_type` es `THIRD_PARTY`, `LEASED` o `RENTED`, el campo `owner_partner_id` es obligatorio y debe apuntar a un socio de negocio válido de la Fase 025.
