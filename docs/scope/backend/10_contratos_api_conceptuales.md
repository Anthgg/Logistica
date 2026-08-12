# 10. Contratos API Conceptuales — `/api/logistics`

Inventario conceptual de recursos futuros del backend logístico under `/api/logistics`. **Nota:** Ningún endpoint está programado en esta fase.

## 1. Maestros Logísticos (`/api/logistics/...`)

### Productos
- `GET /api/logistics/products`: Lista paginada con filtros (`category_id`, `sku`, `is_active`).
- `POST /api/logistics/products`: Crear SKU. Requiere rol `ACT_ADM` o `ACT_CMP`.
- `GET /api/logistics/products/{id}`: Detalle de producto y conversiones de unidad.
- `PUT /api/logistics/products/{id}`: Actualizar catálogo.

### Almacenes y Ubicaciones
- `GET /api/logistics/warehouses`: Lista de almacenes por sede.
- `GET /api/logistics/warehouses/{id}/locations`: Mapa jerárquico de pasillos/racks.
- `POST /api/logistics/locations`: Crear ubicación interna con capacidad volumétrica.

### Socios de Negocio, Transportistas y Flota
- `GET /api/logistics/business-partners`: Filtros por tipo (`SUPPLIER`, `CUSTOMER`, `CARRIER`).
- `POST /api/logistics/business-partners/lookup-ruc`: Consulta RUC a SUNAT/Padrón local.
- `GET /api/logistics/vehicles`: Lista de unidades de transporte con SOAT/CITV.
- `GET /api/logistics/drivers`: Lista de conductores habilitados con categoría de brevete.

---

## 2. Abastecimiento y Recepción

### Compras
- `GET /api/logistics/purchase-requests`: Requerimientos de compra.
- `POST /api/logistics/purchase-requests`: Crear requerimiento.
- `POST /api/logistics/purchase-orders/{id}/approve`: Aprobar orden (Requiere Step-up OTP si > $5,000).

### Inbound y Recepción
- `GET /api/logistics/inbound-appointments`: Citas programadas en muelle.
- `POST /api/logistics/gate-entries`: Registro de ingreso en garita (Guardia).
- `POST /api/logistics/receptions`: Crear acta de recepción y conteo físico.
- `POST /api/logistics/receptions/{id}/quality-inspection`: Enviar lote a inspección de calidad.

---

## 3. Inventario y Control de Stock

- `GET /api/logistics/stock/balances`: Consultar stock disponible por producto, almacén y lote.
- `GET /api/logistics/inventory/kardex`: Reporte de movimientos inmutables (Kardex).
- `POST /api/logistics/inventory/transfers`: Crear orden de traslado inter-almacén.
- `POST /api/logistics/inventory/adjustments`: Ajuste manual de inventario (Acción Sensible -> Step-Up).

---

## 4. Salida, Despacho y Transporte

- `POST /api/logistics/outbound-orders`: Registrar pedido de salida.
- `POST /api/logistics/picking/tasks/{id}/complete`: Confirmar recolección en pasillo.
- `POST /api/logistics/packing/units`: Consolidar empaque y asignar LPN.
- `POST /api/logistics/dispatches`: Generar despacho y emitir Guía de Remisión PDF.
- `POST /api/logistics/trips`: Crear viaje y asignar ruta/vehículo/conductor.
- `POST /api/logistics/gps-positions`: Recepción de coordenadas GPS desde App Móvil Conductor.
- `POST /api/logistics/deliveries/{id}/complete`: Registrar Prueba de Entrega (POD: Foto, Firma, OTP).
- `POST /api/logistics/returns`: Registrar solicitud de devolución (RMA).

---

## 5. Respuestas de Error Estándar

Todas las respuestas de error utilizarán el formato Pydantic/FastAPI estandarizado del backend:

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Saldo insuficiente en la ubicación PASILLO-01-RACK-02. Stock disponible: 15.00, Solicitado: 20.00",
    "details": {
      "product_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "location_id": "4a2c1b3d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"
    },
    "timestamp": "2026-07-26T05:00:00Z"
  }
}
```
