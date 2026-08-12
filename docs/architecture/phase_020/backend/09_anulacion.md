# 09. Anulación de Documentos

Un documento emitido incorrectamente puede ser anulado en el sistema, pero el registro original permanece intacto.

## Reglas de Negocio
- **No eliminación física**: Se prohibe borrar el registro original de base de datos para mantener la trazabilidad.
- **Correlativo ocupado**: El correlativo reservado en la serie no se libera ni se vuelve a utilizar por otros documentos.
- **Artefacto anulado**: Se genera un nuevo PDF con la marca de agua `ANULADO` en diagonal, el cual reemplaza la descarga por defecto del usuario.
- **Acceso especial**: La descarga del PDF original (sin marca de anulación) queda restringida a perfiles de auditoría avanzados y requiere Step-Up `CRITICAL`.
