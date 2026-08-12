# 30 — Exportaciones

`InventoryKardexExportJob`:

- Formatos: CSV, XLSX, PDF, JSON.
- Job asincrónico.
- Archivo privado en `INVENTORY_LEDGER_EXPORT_DIR`.
- `manifest_hash` SHA-256.
- `download_url` opcional (no persistido).
- Registra descarga.
- Step-up HIGH.

Reglas:

- Sin permiso, no exporta.
- Saldo corrido no se incluye si el ámbito es ambiguo.
- Sin `signed_url` persistido.
