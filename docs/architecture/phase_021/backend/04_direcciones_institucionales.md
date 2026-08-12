# 04. Gestión de Direcciones Institucionales

## 🏢 Modelo OrganizationAddressModel

El modelo `OrganizationAddressModel` (`organization_addresses`) gestiona las múltiples direcciones físicas, fiscales y operativas asociadas a la organización o a sedes específicas (`branch_id`).

```python
class OrganizationAddressModel(Base):
    __tablename__ = "organization_addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="SET NULL"), nullable=True
    )
    address_type: Mapped[str] = mapped_column(String(32), nullable=False)  # LEGAL, FISCAL, COMMERCIAL, OPERATIONS, BILLING
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    address_line: Mapped[str] = mapped_column(String(512), nullable=False)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    province: Mapped[str | None] = mapped_column(String(128), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), default="PE", server_default=text("'PE'"), nullable=False)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    is_document_address: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="FORMAT_VALID", server_default=text("'FORMAT_VALID'"), nullable=False)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
```

---

## 🏷️ Tipos de Dirección Institucional (`address_type`)

* `LEGAL`: Domicilio Legal registrado ante Registros Públicos (SUNARP).
* `FISCAL`: Domicilio Fiscal declarado ante la Administración Tributaria (SUNAT).
* `COMMERCIAL`: Oficina Comercial o Administrativa para recepción de clientes/proveedores.
* `OPERATIONS`: Centro de Operaciones / Almacén Central de Despacho.
* `BILLING`: Dirección documental para envío de facturación y cobranzas.

---

## 👑 Regla de Unicidad del Marcador `is_primary`

Una organización solo puede tener **una única dirección marcada como principal (`is_primary = True`)** a la vez.

El servicio `AddressContactService` garantiza esta regla en la base de datos de manera atómica: cuando una dirección se marca como principal (ya sea durante la creación, edición o invocando el endpoint `/addresses/{id}/set-primary`), el servicio desmarca automáticamente (`is_primary = False`) todas las demás direcciones activas pertenecientes a la misma organización dentro de la transacción actual.

```python
def set_primary_address(self, organization_id: UUID, address_id: UUID, actor_id: UUID | None = None) -> OrganizationAddressModel:
    address = self.get_address(organization_id, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Dirección institucional no encontrada.")

    # Desmarcar otras direcciones principales de la organización
    self.db.execute(
        update(OrganizationAddressModel)
        .where(
            and_(
                OrganizationAddressModel.organization_id == organization_id,
                OrganizationAddressModel.id != address_id,
                OrganizationAddressModel.is_primary == True,
            )
        )
        .values(is_primary=False, updated_by=actor_id, updated_at=utc_now())
    )

    address.is_primary = True
    address.updated_by = actor_id
    address.updated_at = utc_now()
    self.db.flush()

    self._write_audit(
        event_code="logistics.company_address.primary_changed",
        organization_id=organization_id,
        actor_id=actor_id,
        resource_type="organization_addresses",
        resource_id=address.id,
        details={"label": address.label, "address_type": address.address_type},
    )

    return address
```

---

## 📄 Direcciones Documentales por Sede (`is_document_address` & `branch_id`)

Al emitir un documento logístico en una sede específica (ej. Sede Arequipa):

1. **Resolución por Sede**: El sistema busca primero una dirección activa asociada explícitamente a dicha sede (`branch_id = X` y `is_document_address = True`).
2. **Fallback Institucional**: Si la sede no posee una dirección propia asignada, el sistema utiliza la dirección principal de la organización (`is_primary = True`).
3. **Resguardo de Ubigeo y Coordenadas**: Se soporta la inclusión de ubigeo (Distrito, Provincia, Departamento), código postal y coordenadas geográficas (`latitude`, `longitude`) que serán utilizadas por la Fase 022 (Almacenes y Ubicaciones) y la Fase 026 (Guías de Remisión Electrónicas SUNAT).
