# 10. Decisiones Pendientes

## D01 — Proveedor de rutas

**Estado**: PENDIENTE  
**Alternativas**: OSRM (self-hosted), openrouteservice (cloud), Mapbox API, Google Maps  
**Impacto**: Determina la implementación de `DirectionsProvider` en infraestructura  
**Decisión esperada**: Fase 004

## D02 — Proveedor de almacenamiento de archivos

**Estado**: PENDIENTE  
**Alternativas**: Google Cloud Storage, AWS S3, almacenamiento local  
**Impacto**: Determina la implementación de `FileStorage`  
**Decisión esperada**: Fase 004

## D03 — Motor de generación de PDF

**Estado**: PENDIENTE  
**Alternativas**: WeasyPrint, ReportLab, Jinja2 + Playwright, wkhtmltopdf  
**Impacto**: Determina la implementación de `DocumentRenderer`  
**Decisión esperada**: Fase 004

## D04 — Asignación de permisos a roles

**Estado**: PENDIENTE  
**Alternativas**: Tabla de permisos en DB, mapping estático en código, RBAC basado en claims  
**Impacto**: Determina cómo `require_logistics_permission` valida permisos  
**Decisión esperada**: Fase 005

## D05 — Estrategia de auditoría logística

**Estado**: PENDIENTE  
**Alternativas**: Reutilizar `audit_logs` existente con `event_metadata`, crear tabla separada `logistics_audit_events`  
**Impacto**: Determina el adaptador de `AuditEventWriter`  
**Decisión esperada**: Fase 004  
**Recomendación**: Reutilizar tabla existente con metadata adicional.

## D06 — Cache para integraciones

**Estado**: PENDIENTE  
**Alternativas**: Redis, caché en memoria, sin caché  
**Impacto**: Determina la implementación de `IntegrationCache`  
**Decisión esperada**: Fase 005