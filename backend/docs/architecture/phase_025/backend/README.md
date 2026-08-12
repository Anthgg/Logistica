# Fase 025 — Socios de Negocio (Business Partners) — Backend

## Objetivo

Implementar el **Maestro Único y Versionado de Socios de Negocio** para Proyecto T1.

Una sola entidad `BusinessPartner` representa proveedores, clientes y transportistas sin duplicar registros por cada rol.

## Estructura del Módulo

```
app/modules/logistics/partners/
├── __init__.py
├── models.py                # 13 modelos ORM SQLAlchemy 2.0
├── ruc_validator.py         # Validador sintáctico Módulo 11 (PE)
├── code_service.py          # Generador de códigos BP-000001
├── compliance_resolver.py   # Resolutor de riesgo y cumplimiento
├── snapshot_provider.py     # Generador de snapshots SHA-256
├── duplicate_detector.py    # Motor de detección de duplicados
├── partner_service.py       # Servicio de aplicación CRUD
├── schemas.py               # Esquemas Pydantic v2
└── router.py                # Endpoints REST FastAPI
```

## Migración

`p270110025dc_phase_025_business_partners.py` — 16 tablas, índices, restricciones únicas y FK.

## Decisiones Clave

1. **Entidad Única**: `BusinessPartnerModel` es el maestro. No existen `SupplierModel`, `CustomerModel` o `CarrierModel` independientes.
2. **Roles Múltiples**: `BusinessPartnerRoleModel` con `role_type ∈ {SUPPLIER, CUSTOMER, CARRIER}`. Un socio puede tener 3 roles activos simultáneamente.
3. **Perfiles Especializados**: `SupplierProfileModel`, `CustomerProfileModel`, `CarrierProfileModel` como 1:1 por rol para datos específicos.
4. **RUC Perú**: Validación sintáctica Módulo 11. Estado `FORMAT_VALID`. **SIN** consulta a SUNAT (→ Fase 026).
5. **Código Estable**: `BP-000001`, único por organización, generado de forma segura.
6. **Snapshots Inmutables**: SHA-256 sobre JSONB canónico para congelar identidad al emitir documentos.
7. **Evaluaciones con Decimal**: Cálculo exacto de `weighted_score = weight × score / 100` usando `Decimal`.
8. **Aislamiento de Organización**: Ningún socio de otra organización es accesible.

## Prohibiciones Confirmadas

- ❌ No se crearon Supplier/Customer/Carrier como entidades desconectadas.
- ❌ No se consultó SUNAT.
- ❌ No se crearon vehículos ni conductores.
- ❌ No se creó repositorio general de archivos.
- ❌ No se modificó el frontend.
- ❌ No se comenzó la Fase 026.
