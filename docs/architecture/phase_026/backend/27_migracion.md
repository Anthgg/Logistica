# 27 — Migración de Base de Datos Alembic (`q280110026dc_phase_026_ruc_lookup.py`)

## 1. Fichero de Migración

La migración se ubica en `backend/alembic/versions/q280110026dc_phase_026_ruc_lookup.py` y depende de la versión previa `p270110025dc`.

## 2. DDL SQL Generado (Resumen de Tablas Creadas)

```sql
CREATE TABLE ruc_data_sources (
    id UUID PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    authority VARCHAR(100) NOT NULL DEFAULT 'SUNAT',
    source_reference VARCHAR(500) NOT NULL,
    base_domain VARCHAR(200) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER NOT NULL DEFAULT 10,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ruc_dataset_versions (
    id UUID PRIMARY KEY,
    data_source_id UUID NOT NULL REFERENCES ruc_data_sources(id) ON DELETE CASCADE,
    dataset_type VARCHAR(40) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'DISCOVERED',
    archive_hash VARCHAR(64),
    content_hash VARCHAR(64),
    total_rows BIGINT NOT NULL DEFAULT 0,
    accepted_rows BIGINT NOT NULL DEFAULT 0,
    rejected_rows BIGINT NOT NULL DEFAULT 0,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMPTZ
);

CREATE INDEX ix_ruc_dataset_versions_type_status ON ruc_dataset_versions(dataset_type, status);

CREATE TABLE ruc_registry_entries (
    id UUID PRIMARY KEY,
    dataset_version_id UUID NOT NULL REFERENCES ruc_dataset_versions(id) ON DELETE CASCADE,
    ruc VARCHAR(11) NOT NULL,
    normalized_ruc VARCHAR(11) NOT NULL,
    legal_name VARCHAR(300) NOT NULL,
    normalized_legal_name VARCHAR(300) NOT NULL,
    taxpayer_status_normalized VARCHAR(50) NOT NULL DEFAULT 'UNKNOWN',
    domicile_condition_normalized VARCHAR(50) NOT NULL DEFAULT 'UNKNOWN',
    ubigeo_code VARCHAR(10),
    record_hash VARCHAR(64) NOT NULL
);

CREATE UNIQUE INDEX uix_ruc_registry_dataset_ruc ON ruc_registry_entries(dataset_version_id, normalized_ruc);
CREATE INDEX ix_ruc_registry_entries_normalized_ruc ON ruc_registry_entries(normalized_ruc);
```
