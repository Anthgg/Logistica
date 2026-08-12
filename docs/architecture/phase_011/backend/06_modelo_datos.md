# 06 — Modelo de Datos del Catálogo Documental

## Relaciones Entidad-Relación (Mermaid)

```mermaid
erDiagram
    DOCUMENT_FAMILIES ||--o{ DOCUMENT_TYPES : contains
    DOCUMENT_TYPES ||--o{ DOCUMENT_TYPE_VERSIONS : versioned_by
    DOCUMENT_RETENTION_POLICIES ||--o{ DOCUMENT_TYPE_VERSIONS : applies_to
    DOCUMENT_CATALOG_VERSIONS ||--o{ DOCUMENT_TYPES : releases

    DOCUMENT_FAMILIES {
        uuid id PK
        string code UK
        string name
        string owner_module
    }

    DOCUMENT_TYPES {
        uuid id PK
        string code UK
        string name
        uuid family_id FK
        uuid active_version_id
    }

    DOCUMENT_TYPE_VERSIONS {
        uuid id PK
        uuid document_type_id FK
        string version
        jsonb required_fields_schema
        jsonb allowed_statuses
    }
```

## Definición de Tablas Principales
* `document_families`: Almacena las 13 familias de clasificación.
* `document_types`: Almacena los tipos documentales del catálogo (28 tipos activos).
* `document_type_versions`: Contratos inmutables de esquema y reglas por versión de tipo documental.
* `document_retention_policies`: Reglas de conservación legal y operativa.
* `document_catalog_versions`: Historial de liberaciones del catálogo global (SemVer).
