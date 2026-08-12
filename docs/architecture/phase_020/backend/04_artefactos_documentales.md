# 04. Artefactos Documentales

Los PDFs generados y archivos ZIP exportados se modelan como entidades de tipo `DocumentArtifactModel`.

## Características
- **storage_key**: La ruta física en el almacenamiento de objetos local o Cloud Storage.
- **file_hash**: Hash SHA-256 del contenido binario para verificar su integridad.
- **is_authoritative**: Flag que indica si el archivo representa el documento oficial emitido.
- **is_sensitive**: Restringe el acceso de lectura al personal sin permisos adecuados.
