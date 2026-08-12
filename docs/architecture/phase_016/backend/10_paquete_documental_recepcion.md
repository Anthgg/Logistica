# 10 — Paquete Documental de Recepción

## Concepto
El **Paquete Documental de Recepción** agrupa los documentos que corresponden a un evento de recepción completo. El endpoint `/api/logistics/inbound/document-package/manifest` evalúa las condiciones de un evento y devuelve qué documentos deben incluirse.

## Schema de Respuesta: `ReceptionPackageManifestResponse`

```python
class ReceptionPackageManifestResponse(BaseModel):
    manifest_version: str          # "1.0.0"
    package_mode: str              # "PREVIEW"
    organization_name: str
    branch_name: str
    warehouse_name: str
    included_documents: list[str]  # Ej: ["CIT", "CPV", "AREC", "NI", "DIF", "NC"]
    missing_documents: list[str]   # Documentos esperados pero no disponibles
    warnings: list[str]            # Alertas especiales (ej: NC requiere inspector)
```

## Reglas de Inclusión

| Condición del Evento | Documento Incluido |
|---|---|
| `has_appointment == True` | **CIT** |
| `has_appointment == False` | CIT → `missing_documents` |
| `has_vehicle_entry == True` | **CPV** |
| Siempre | **AREC** |
| `accepted_quantity > 0` | **NI** |
| `has_differences == True` | **DIF** |
| `has_non_conformity == True` | **NC** |

## Warnings Automáticos
- Si `NC` está incluida: se agrega warning "Requiere revisión de inspector de calidad"

## Modo Preview
En Fase 016 el manifiesto siempre se emite con `package_mode = "PREVIEW"`. No se asignan correlativos ni se crean registros de paquete.
