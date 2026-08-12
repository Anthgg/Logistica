# 22. Contrato de Integración Futura con Fase 061 (Despacho Logístico y Transportistas)

## Asignación de Transportistas y Puntos de Entrega de Clientes

La **Fase 061 (Gestión de Despachos y Ruta)** administra la generación de Guías de Remisión Remitente (GRR) y Guías de Remisión Transportista (GRT), así como la asignación de flotas de carga.

---

## Servicios Consumidos por la Fase 061

```python
class CarrierDispatchEligibilityDTO(BaseModel):
    is_eligible: bool
    mtc_registration_code: str
    max_payload_tonnage: Decimal
    permits_hazardous_materials: bool
    rejection_reason: Optional[str] = None

class CarrierDispatchValidationService:
    async def validate_carrier_for_dispatch(
        self, 
        carrier_partner_id: uuid.UUID,
        requires_matpel: bool,
        cargo_weight_tons: Decimal
    ) -> CarrierDispatchEligibilityDTO:
        partner = await self.repo.get_by_id(carrier_partner_id)
        if not partner or partner.status != "ACTIVE":
            return CarrierDispatchEligibilityDTO(
                is_eligible=False, 
                mtc_registration_code="", 
                max_payload_tonnage=Decimal("0.00"), 
                permits_hazardous_materials=False,
                rejection_reason="El transportista no está activo."
            )

        carrier_role = next((r for r in partner.roles if r.role_type == "CARRIER"), None)
        if not carrier_role or carrier_role.status != "ACTIVE":
            return CarrierDispatchEligibilityDTO(
                is_eligible=False, 
                mtc_registration_code="", 
                max_payload_tonnage=Decimal("0.00"), 
                permits_hazardous_materials=False,
                rejection_reason="El socio no cuenta con el rol de Transportista (CARRIER) activo."
            )

        profile = carrier_role.carrier_profile
        
        # Validar Matpel
        if requires_matpel and not profile.permits_hazardous_materials:
            return CarrierDispatchEligibilityDTO(
                is_eligible=False,
                mtc_registration_code=profile.mtc_registration_code,
                max_payload_tonnage=profile.max_payload_tonnage,
                permits_hazardous_materials=False,
                rejection_reason="La carga requiere permisos de Materiales Peligrosos (MATPEL) y el transportista no cuenta con autorización."
            )

        # Validar capacidad de carga
        if cargo_weight_tons > profile.max_payload_tonnage:
            return CarrierDispatchEligibilityDTO(
                is_eligible=False,
                mtc_registration_code=profile.mtc_registration_code,
                max_payload_tonnage=profile.max_payload_tonnage,
                permits_hazardous_materials=profile.permits_hazardous_materials,
                rejection_reason=f"El peso de la carga ({cargo_weight_tons} ton) excede la capacidad máxima del transportista ({profile.max_payload_tonnage} ton)."
            )

        return CarrierDispatchEligibilityDTO(
            is_eligible=True,
            mtc_registration_code=profile.mtc_registration_code,
            max_payload_tonnage=profile.max_payload_tonnage,
            permits_hazardous_materials=profile.permits_hazardous_materials
        )
```

---

## Matriz de Datos compartidos para Guías de Remisión

Para la emisión de la **Guía de Remisión Electrónica (GRE)** ante la SUNAT, la Fase 061 extrae de la Fase 025:

1. **Datos del Destinatario (Cliente):** `tax_id_type`, `tax_id_value`, `legal_name` y la dirección primaria de tipo `DELIVERY` con su correspondiente `ubigeo_code`.
2. **Datos del Transportista:** `tax_id_type`, `tax_id_value`, `legal_name` y `mtc_registration_code`.
