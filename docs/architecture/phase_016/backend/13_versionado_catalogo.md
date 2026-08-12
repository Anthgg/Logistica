# 13 — Versionado de Catálogo de Plantillas

## Registro en Base de Datos

Cada plantilla de ingreso/calidad se registra en dos modelos al hacer seed:

### `DocumentTemplateModel` (una fila por tipo)
```python
DocumentTemplateModel(
    template_key="inbound.cit",
    document_family_code="INBOUND",
    document_type_code="CIT",
    name="CITA DE RECEPCIÓN",
    description="Plantilla especializada de recepción para CIT",
    status="ACTIVE",
    is_system=True,
)
```

### `DocumentTemplateVersionModel` (una fila por versión)
```python
DocumentTemplateVersionModel(
    template_id=tpl.id,
    version="1.0.0",
    engine="Jinja2+WeasyPrint/Fallback",
    html_path="inbound/cit_v1.html",
    css_paths={"print": "shared/print.css", "inbound": "inbound/shared/inbound.css"},
    content_hash="inbound_cit_v1_hash",
    status="ACTIVE",
)
```

## Seed Automático
`InboundRenderingService.seed_inbound_templates()` se llama al inicio de cada preview/pdf. Usa `get_by_key()` del repositorio — si la plantilla ya existe no la duplica.

## Plantillas Registradas en Fase 016

| `template_key` | Versión | Familia |
|---|---|---|
| `inbound.cit` | 1.0.0 | INBOUND |
| `inbound.cpv` | 1.0.0 | INBOUND |
| `inbound.arec` | 1.0.0 | INBOUND |
| `inbound.ni` | 1.0.0 | INBOUND |
| `inbound.dif` | 1.0.0 | INBOUND |
| `quality.nc` | 1.0.0 | QUALITY |
