# 05. Gestión de Contactos Institucionales

## 📞 Modelo OrganizationContactModel

El modelo `OrganizationContactModel` (`organization_contacts`) gestiona las personas de contacto, áreas funcionales o números de atención institucional de la empresa.

```python
class OrganizationContactModel(Base):
    __tablename__ = "organization_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="SET NULL"), nullable=True
    )
    contact_type: Mapped[str] = mapped_column(String(32), nullable=False)  # GENERAL, COMMERCIAL, PURCHASES, DISPATCH, RECEPTION, BILLING
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    position: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extension: Mapped[str | None] = mapped_column(String(16), nullable=True)
    website: Mapped[str | None] = mapped_column(String(256), nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    show_in_documents: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    document_families: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)  # ["OUTBOUND", "INBOUND", "TRANSPORT"]

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
```

---

## 🗂️ Clasificación por Tipo de Contacto (`contact_type`)

| Tipo | Descripción | Ejemplo de Uso |
|---|---|---|
| `GENERAL` | Central Telefónica / Correo Institucional | Pie de página genérico en PDFs |
| `COMMERCIAL` | Ventas y Atención a Clientes | Presupuestos, Cotizaciones |
| `PURCHASES` | Departamento de Compras / Adquisiciones | Orden de Compra, Recepciones |
| `DISPATCH` | Jefe de Almacén / Despacho Logístico | Guías de Remisión, Pedidos |
| `RECEPTION` | Mesa de Partes / Recepción Documentaria | Actas de Entrega / Conformidad |
| `BILLING` | Facturación y Cobranzas | Comprobantes de Pago |

---

## 👁️ Visibilidad en Documentos (`show_in_documents` & `document_families`)

No todos los contactos deben figurar en la totalidad de los documentos impresos o digitales.

1. **Bandera `show_in_documents`**: Si se establece en `False`, el contacto se mantiene en el directorio interno de la empresa pero el renderizador PDF de la Fase 020 lo omite por completo.
2. **Filtrado por Familias Documentales (`document_families`)**: Campo de tipo `JSONB` que contiene la lista de códigos de familias aprobadas (ej. `["OUTBOUND", "TRANSPORT"]`).
   * Al renderizar un pedido de salida (`OUTBOUND`), el motor de plantillas filtra únicamente los contactos marcados con `show_in_documents = True` cuyo `document_families` sea `null` o incluya `"OUTBOUND"`.
3. **Contacto Primario (`is_primary`)**: Al igual que con las direcciones, se garantiza atómicamente que solo exista un contacto marcado con `is_primary = True` por tipo de contacto u organización, sirviendo de contacto por defecto en los snapshots documentales.
