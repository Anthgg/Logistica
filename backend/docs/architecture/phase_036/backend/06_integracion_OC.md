# Integración con órdenes de compra

Sólo se aceptan OC del mismo tenant, proveedor y almacén, en estados `ISSUED`, `SENT` o `ACKNOWLEDGED`. Se toma la revisión emitida; si no existe, se rechaza la solicitud.

Cada referencia conserva código, moneda, proveedor y hash del snapshot. No se altera la OC ni se recrean sus líneas. La validación usa `po_purchase_orders`, `po_purchase_order_revisions` y `po_purchase_order_lines`.

