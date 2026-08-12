# Permisos y Step-Up Referencial (Phase 017)

## Control de Acceso
- **Acceso a Endpoints**: Protegido con `require_permission("logistics.documents.read")`.
- **Datos de Costos**: Requiere el permiso específico de lectura de datos confidenciales.

## Step-Up en Ajustes (AJI)
- El acta de ajuste de inventario (AJI) incluye un bloque visual de Step-Up Authentication que simula el requerimiento de una verificación biométrica o pin reforzado antes de poder aplicar el ajuste operativo en la base de datos (Fase 047).
