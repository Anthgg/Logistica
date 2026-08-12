# 06 — Gestión de Locales Anexos (`RucRegistryAnnexAddressModel`)

## 1. Definición del Modelo ORM

El padrón de locales anexos de SUNAT registra los establecimientos comerciales, almacenes, sucursales y plantas de un contribuyente adicionales a su domicilio fiscal principal.

```python
class RucRegistryAnnexAddressModel(Base):
    __tablename__ = "ruc_registry_annex_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_version_id = Column(UUID(as_uuid=True), ForeignKey("ruc_dataset_versions.id", ondelete="CASCADE"), nullable=False)
    
    ruc = Column(String(11), nullable=False, index=True)
    ubigeo_code = Column(String(10), nullable=True, index=True)
    address_raw = Column(Text, nullable=False)
    address_normalized = Column(Text, nullable=True)
    
    source_published_at = Column(DateTime(timezone=True), nullable=True)
    imported_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    record_hash = Column(String(64), nullable=False)
    row_status = Column(String(20), nullable=False, default="ACTIVE")
```

---

## 2. Desacoplamiento de Direcciones Fiscales del Socio Comercial

Un contribuyente puede registrar decenas o cientos de locales anexos en el padrón oficial SUNAT. 

### Reglas de Desacoplamiento:
1. **Catálogo de Referencia Oficial**: Las direcciones de `ruc_registry_annex_addresses` se almacenan exclusivamente como catálogo de consulta y validación.
2. **Independencia en `business_partner_addresses`**: Las direcciones operativas del Socio Comercial (puntos de entrega de órdenes de compra, almacenes de despacho) gestionadas en la Fase 025 mantienen sus propios IDs y ciclo de vida.
3. **Validación de Consistencia**: Al asociar una dirección de despacho a un socio comercial, el sistema valida opcionalmente si el Ubigeo y dirección coinciden con algún local anexo verificado del RUC, emitiendo un nivel de coincidencia (*Exact*, *Partial*, *Unverified*).
