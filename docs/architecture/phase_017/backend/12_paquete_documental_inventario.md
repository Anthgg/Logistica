# Paquete Documental de Inventario (Phase 017)

## Propósito
El manifiesto (`InventoryDocumentPackageManifest`) consolida y valida el conjunto de documentos necesarios para una operación de inventario de acuerdo al modo seleccionado.

## Reglas de Inclusión por Modo
- **LOCATION**: Incluye `EUB`. Puede incluir `PUT` opcionalmente.
- **PUTAWAY**: Incluye `PUT`. Puede incluir `EUB` referencial.
- **MOVEMENT**: Incluye `MOV`.
- **ADJUSTMENT**: Incluye `AJI`. Incluye `ADI` si proviene de un conteo, y `MOV` si tiene movimiento compensatorio.
- **COUNT**: Incluye `CNT`. Si hay discrepancias, incluye obligatoriamente `ADI`. Puede incluir `AJI` si hay ajuste pre-aprobado.
- **TRANSFER**: Incluye `TRA`.
- **TRANSFER_RECEIPT**: Incluye `CRT`. Si hay discrepancias internas, incluye `ADI`.

## Modo Preview
En esta fase el manifiesto opera al 100% en modo previsualización, arrojando advertencias si se incluyen tipos documentales en estado propuesto (`EUB`, `ADI`, `CRT`).
