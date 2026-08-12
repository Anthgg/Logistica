# AJI — Acta de Ajuste de Inventario (Phase 017)

## Propósito
Ajustar de manera justificada el saldo lógico de un producto en una ubicación específica debido a mermas, pérdidas o hallazgos.

## Cálculo y Coherencia
El documento requiere el cumplimiento de la fórmula:
`adjustment_quantity = verified_quantity - recorded_quantity`
Cualquier desviación en la solicitud es rechazada en la validación del esquema.

## Privacidad e Impacto Económico
- **Clasificación CONFIDENTIAL**: Información restringida bajo el permiso `logistics.inventory_documents.read_sensitive`.
- Si el usuario no tiene dicho permiso, el impacto económico y el valor unitario se ocultan visualmente bajo una etiqueta de aviso de sensibilidad.

## Autenticación Continua
- Muestra un bloque referencial de verificación biométrica / step-up requerido para la ejecución de ajustes de alto impacto (PENDING_PHASE_047).
