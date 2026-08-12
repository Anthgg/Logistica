# CRT — Constancia de Recepción de Transferencia (Phase 017)

## Propósito
Registrar el resultado de la descarga y verificación de una transferencia recibida, comparando las cantidades despachadas originalmente.

## Comparación y Coherencia de Cantidades
- Cada línea detalla: Despachado vs Recibido vs Aceptado vs Observado vs Rechazado.
- Se valida la regla: `accepted + observed + rejected <= received`.
- Se calculan dinámicamente las cantidades faltantes (`shortage`) o sobrantes (`overage`) respecto al despacho original.

## Trazabilidad de Diferencias
Si hay discrepancias en la recepción, el paquete documental genera una advertencia y se asocia un Acta de Diferencia (ADI) para la investigación correspondiente.
