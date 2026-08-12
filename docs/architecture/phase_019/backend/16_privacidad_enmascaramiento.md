# Privacidad y Enmascaramiento (Phase 019)

## Enmascaramiento de Datos
Si el usuario carece del permiso `read_sensitive`, se enmascaran:
- DNI/Licencia del conductor (ej. `******34`).
- Teléfono y email del cliente receptor.
- Firmas y fotos (muestran aviso de "Protegido").

## Flujo de Enmascaramiento
```mermaid
flowchart TD
    Data[Datos Completos] --> AuthCheck{¿Tiene Permiso Sensitive?}
    AuthCheck -->|No| Mask[Aplicar mask_sensitive_val]
    AuthCheck -->|Sí| Reveal[Mostrar Datos Reales]
```
