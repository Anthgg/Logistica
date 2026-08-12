# 05 — Modelo de Registro de RUC General (`RucRegistryEntryModel`)

## 1. Definición del Modelo ORM

El modelo `RucRegistryEntryModel` mapea la información principal de contribuyentes del Padrón Reducido SUNAT:

```python
class RucRegistryEntryModel(Base):
    __tablename__ = "ruc_registry_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_version_id = Column(UUID(as_uuid=True), ForeignKey("ruc_dataset_versions.id", ondelete="CASCADE"), nullable=False)
    
    ruc = Column(String(11), nullable=False)
    normalized_ruc = Column(String(11), nullable=False, index=True)
    legal_name = Column(String(300), nullable=False)
    normalized_legal_name = Column(String(300), nullable=False, index=True)
    
    taxpayer_status_raw = Column(String(100), nullable=True)
    taxpayer_status_normalized = Column(String(50), nullable=False, default="UNKNOWN")
    domicile_condition_raw = Column(String(100), nullable=True)
    domicile_condition_normalized = Column(String(50), nullable=False, default="UNKNOWN")
    
    ubigeo_code = Column(String(10), nullable=True, index=True)
    source_published_at = Column(DateTime(timezone=True), nullable=True)
    imported_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    record_hash = Column(String(64), nullable=False)
    row_status = Column(String(20), nullable=False, default="ACTIVE")
```

---

## 2. Normalización de Estados y Condición de Domicilio

### Estado del Contribuyente (`taxpayer_status_normalized`):
- **`ACTIVE`**: Activo y habilitado tributariamente (Valores RAW: `ACTIVO`, `BAJA DE OFICIO PREVIO`).
- **`SUSPENDED`**: Suspensión temporal (Valores RAW: `SUSPENSION TEMPORAL`).
- **`CANCELLED`**: Baja definitiva o nulo (Valores RAW: `BAJA DEFINITIVA`, `BAJA PROVISIONAL`, `ANULACION`).
- **`UNKNOWN`**: Estado no reconocido o no provisto.

### Condición del Domicilio Fiscal (`domicile_condition_normalized`):
- **`HABIDO`**: Domicilio fiscal confirmado por inspección SUNAT.
- **`NO_HABIDO`**: No localizado en el domicilio fiscal registrado.
- **`NO_HALLADO`**: Ausente o no ubicado durante verificación.
- **`PENDIENTE`**: Proceso de verificación en curso.
- **`UNKNOWN`**: Sin condición especificada.

---

## 3. Restricciones e Índices

1. **Restricción Única Compuesta**: `uix_ruc_registry_dataset_ruc` sobre `(dataset_version_id, normalized_ruc)`. Garantiza que en una misma versión del dataset no existan duplicados de RUC.
2. **Índice Compuesto de Búsqueda de Riesgo**: `ix_ruc_registry_status_cond` sobre `(taxpayer_status_normalized, domicile_condition_normalized)` para filtrado rápido de proveedores no habidos o cancelados.
