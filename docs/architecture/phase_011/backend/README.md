# Fase 011 — Crear el Catálogo de Documentos (Backend)

## Objetivo
Implementar un catálogo documental central, validado, versionado y persistido que enumere y estandarice todos los tipos de documentos internos y externos utilizados en los procesos logísticos de **Proyecto T1**.

## Alcance
* **Catálogo Central SemVer (1.0.0):** Definición unificada de 13 familias documentales, 28 tipos internos principales (REQ a DEV) y tipos externos referenciales.
* **Modelo de Datos:** Tablas `document_families`, `document_types`, `document_type_versions`, `document_retention_policies` y `document_catalog_versions`.
* **Motor de Validación & Seed Idempotente:** Script de seeding idempotente con `dry_run` y validación automática de contratos.
* **Endpoints de Solo Lectura:** API REST bajo `/api/logistics/document-catalog` protegida por permisos RBAC.
* **Sin Emisión ni Renderizado:** En cumplimiento estricto con las fronteras de la fase, NO se generan archivos PDF, NO se emiten correlativos ni series, y NO se renderizan plantillas HTML.

## Estado
* **Estado General:** `IMPLEMENTADO` / `COMPROBADO`
* **Pruebas Automatizadas:** 142/142 pasadas exitosamente en Pytest.
