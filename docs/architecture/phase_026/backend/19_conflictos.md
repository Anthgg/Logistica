# 19 — Gestión de Conflictos de Datos de RUC (`RucDataConflictModel`)

## 1. Detección Automática de Discrepancias

Cuando el servicio `BusinessPartnerRucIntegrationService` contrasta los datos declarados de un Socio Comercial contra el Padrón Reducido SUNAT activo, cualquier discrepancia genera automáticamente un registro en `ruc_data_conflicts`:

```python
class RucDataConflictModel(Base):
    __tablename__ = "ruc_data_conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    business_partner_id = Column(UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=True)
    ruc = Column(String(11), nullable=False, index=True)
    
    conflict_type = Column(String(50), nullable=False)
    source_a = Column(String(50), nullable=False)
    value_a = Column(Text, nullable=True)
    source_b = Column(String(50), nullable=False)
    value_b = Column(Text, nullable=True)
    
    status = Column(String(30), nullable=False, default="OPEN")
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
```

---

## 2. Flujo de Resolución de Conflictos

1. **`RESOLVED_ACCEPTED_OFFICIAL`**: El usuario gestor de compras acepta reemplazar el dato del socio comercial con el valor oficial de SUNAT.
2. **`RESOLVED_KEPT_DECLARED`**: El usuario confirma mantener el dato ingresado manualmente (requiere justificación en `resolution_notes`).
