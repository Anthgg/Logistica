# 06. Vista Previa y Descarga

El motor documental soporta la generación de PDF en tiempo real para previsualización dinámica y descarga oficial.

## Vista Previa (Preview Mode)
- Se renderiza el PDF agregando la marca de agua `VISTA PREVIA`.
- El correlativo o número oficial se muestra como `PREVIEW-XXXXXX`.
- No consume secuencia de serie.

## Descarga (Download Mode)
- Recupera el artefacto PDF oficial desde el almacenamiento de objetos.
- Valida la coincidencia del hash del archivo con el registro de base de datos antes de transferirlo al usuario.
