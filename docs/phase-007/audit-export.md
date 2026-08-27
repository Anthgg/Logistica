# F007 · Exportación de Auditoría

## 1. Especificación del Exportador CSV
- **Endpoint**: `GET /api/logistics/audit-events/export`
- **Permiso**: `logistics.audit.export`
- **Formato**: CSV codificado en UTF-8 con Byte Order Mark (`﻿`) para total compatibilidad con Microsoft Excel, LibreOffice y herramientas analíticas.
- **Cabeceras**:
  - `ID`, `Fecha (UTC)`, `Código Evento`, `Categoría`, `Acción`, `Resultado`, `Severidad`, `Actor`, `Email`, `IP`, `Tipo Recurso`, `ID Recurso`, `Organización`, `Sede`, `Almacén`, `Motivo / Descripción`, `Campos Modificados`
- **Auto-Auditoría**: Cada petición de exportación registra un evento inmutable `logistics.audit.exported` con el número de filas exportadas y los parámetros de filtro empleados.\n