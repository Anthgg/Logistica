# 12 — Motor de Validación y Seed Idempotente

## Flujo del Seeder (Mermaid)

```mermaid
graph TD
    JSON[catalog_v1_0_0.json] --> Load[loader.load_catalog_json]
    Load --> Validate[validator.validate_catalog_data]
    Validate -->|Válido| Checksum[Calcular SHA256 Checksum]
    Checksum -->|Dry Run True| Report[Devolver Reporte de Validación]
    Checksum -->|Dry Run False| Seed[Insertar/Actualizar Familias, Políticas y Tipos]
    Seed --> Commit[db.commit()]
```

## Idempotencia Garantizada
El script `seed_document_catalog(db)` busca por código antes de crear nuevos registros, permitiendo su ejecución segura múltiples veces sin duplicar familias ni tipos documentales.
