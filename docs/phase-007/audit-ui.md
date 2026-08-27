# F007 · Especificación de UI Frontend para Auditoría

## 1. Página de Auditoría (`/logistics/audit-events`)
La interfaz de usuario en React proporciona:
- **Barra de Filtros Multidimensional**:
  - Rango de fechas (`date_from`, `date_to`).
  - Categoría del evento (`organization`, `branch`, `warehouse`, `security`, `document`, etc.).
  - Nivel de severidad (`info`, `low`, `medium`, `high`, `critical`).
  - Resultado (`success`, `failure`, `denied`, `error`).
  - Acción (`create`, `update`, `delete`, `export`, etc.).
  - Búsqueda libre por texto (recurso, motivo, actor).
  - Botón de limpieza rápida de filtros.
- **Tabla de Eventos**:
  - Columnas: Fecha/Hora, Categoría, Evento, Actor, Recurso, Severidad, Resultado, Acciones.
  - Indicadores visuales de estado y chips de severidad.
  - Botón de Ver Detalle y Verificación de Integridad.
- **Visor de Diff Before / After**:
  - Modal/Drawer con visualización comparativa de cambios de estado JSON.
  - Resaltado de campos modificados (`changed_fields`).
  - Máscaras de datos redactados.
- **Botón de Exportación CSV**:
  - Protegido por permiso `logistics.audit.export`.
  - Descarga directa con feedback de carga y notificación de finalización.\n