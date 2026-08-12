# 18 — Integración con el Maestro de Socios Comerciales (`BusinessPartnerRucIntegrationService`)

## 1. Desacoplamiento y Confirmación de NO Sobrescritura Automática

Una premisa fundamental de arquitectura en el ERP es que **la ingesta de datos del padrón SUNAT NUNCA sobrescribe de manera automática los datos declarados del Socio Comercial (`business_partners`)**.

### Razones de Negocio:
1. **Razón Social Comercial vs Razón Social Tributaria**: Un socio comercial puede operar bajo un nombre comercial registrado en sus contratos distintos a la razón social tributaria.
2. **Control de Cambios Contractuales**: Modificaciones tributarias no deben alterar silenciosamente órdenes de compra o facturas históricas en estado borrador.

---

## 2. Modelo `BusinessPartnerRucVerificationModel`

Registra el resultado inmutable de la verificación de RUC aplicada a un socio comercial específico:

```python
class BusinessPartnerRucVerificationModel(Base):
    __tablename__ = "business_partner_ruc_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    business_partner_id = Column(UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False)
    ruc = Column(String(11), nullable=False, index=True)
    
    verification_method = Column(String(50), nullable=False)
    verification_result = Column(String(30), nullable=False, default="VERIFIED")
    
    verified_legal_name = Column(String(300), nullable=True)
    verified_taxpayer_status = Column(String(50), nullable=True)
    verified_domicile_condition = Column(String(50), nullable=True)
    
    snapshot_payload = Column(JSONB, nullable=False)
    snapshot_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="CURRENT")
```
