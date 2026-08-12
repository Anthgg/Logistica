# 21 — Contrato con Fase 020 (Reimpresión y Anulación)

## Estado Actual
Los documentos CIT, CPV, AREC, NI, DIF y NC están registrados en el catálogo `document_types` con `is_active=True`. Sus plantillas están versionadas en `document_templates` y `document_template_versions`.

## Contrato para Fase 020
La Fase 020 (Reimpresión, Anulación y Archivos ZIP) podrá:

1. **Reimprimir** cualquier documento de recepción buscando en el catálogo por `template_key` y `version`, reconstruyendo el PDF con los datos históricos almacenados.

2. **Anular** documentos emitidos con corrimiento registrado en auditoría inmutable. La anulación no elimina el registro, sino que cambia su `status` a `ANULADO` con justificación.

3. **Generar ZIP** del paquete completo CIT+CPV+AREC+NI+DIF+NC para un evento de recepción dado.

## Prerrequisito para Fase 020
- Los documentos de Fase 016 deben contar con correlativos asignados (deferred a Fase 017 / Fase 041)
- La Fase 020 asume que el módulo de talonarios (Fase 012) ya asignó números oficiales

## Compromiso de Compatibilidad
Las claves de plantilla `inbound.*` y `quality.nc` son estables y **no cambiarán** entre Fase 016 y Fase 020. Cualquier mejora de plantilla generará una nueva versión (ej. `1.1.0`) sin reemplazar `1.0.0`.
