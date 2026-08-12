# 05. Catálogo Conceptual de Entidades — Proyecto T1

Catálogo conceptual del modelo de dominio logístico. **Nota:** No se han definido modelos de SQLAlchemy ni tablas de base de datos en esta fase.

| Entidad | Propósito de Dominio | Identificador Sugerido | Módulo Propietario | Fase Futura |
|---|---|---|---|---|
| `Organization` | Empresa o entidad legal propietaria. | `organization_id` (UUID) | `logistics/organizations` | MVP 1 |
| `Branch` | Sede física u operativa. | `branch_id` (UUID) | `logistics/branches` | MVP 1 |
| `Warehouse` | Instalación o centro de distribución. | `warehouse_id` (UUID) | `logistics/warehouses` | MVP 1 |
| `WarehouseLocation` | Pasillo, rack, posición física. | `location_id` (UUID) | `logistics/locations` | MVP 1 |
| `Product` | Artículo/SKU del catálogo logístico. | `product_id` (UUID) | `logistics/products` | MVP 1 |
| `ProductCategory` | Clasificación jerárquica de productos. | `category_id` (UUID) | `logistics/products` | MVP 1 |
| `UnitOfMeasure` | Unidad física (UND, KG, M3). | `unit_id` (UUID) | `logistics/units` | MVP 1 |
| `UnitConversion` | Factor de conversión entre UOMs. | `conversion_id` (UUID) | `logistics/units` | MVP 1 |
| `BusinessPartner` | Entidad comercial (Cliente/Proveedor). | `partner_id` (UUID) | `logistics/business-partners` | MVP 1 |
| `Supplier` | Proveedor homologado de bienes. | `supplier_id` (UUID) | `logistics/suppliers` | MVP 1 |
| `Customer` | Cliente o destinatario final. | `customer_id` (UUID) | `logistics/customers` | MVP 1 |
| `Carrier` | Empresa transportista contratada. | `carrier_id` (UUID) | `logistics/carriers` | MVP 1 |
| `Vehicle` | Camión, furgón o remolque. | `vehicle_id` (UUID) | `logistics/vehicles` | MVP 1 |
| `Driver` | Conductor certificado con licencia. | `driver_id` (UUID) | `logistics/drivers` | MVP 1 |
| `PurchaseRequest` | Requerimiento interno de compra. | `request_id` (UUID) | `logistics/purchases` | MVP 2 |
| `QuotationRequest` | Solicitud de cotización a proveedor. | `quotation_req_id` (UUID) | `logistics/purchases` | MVP 2 |
| `SupplierQuotation` | Cotización recibida de proveedor. | `quotation_id` (UUID) | `logistics/purchases` | MVP 2 |
| `PurchaseComparison` | Cuadro comparativo de ofertas. | `comparison_id` (UUID) | `logistics/purchases` | MVP 2 |
| `PurchaseOrder` | Orden de compra oficial a proveedor. | `po_id` (UUID) | `logistics/purchase-orders` | MVP 2 |
| `InboundAppointment` | Cita programada de entrega en muelle. | `appointment_id` (UUID) | `logistics/inbound` | MVP 2 |
| `GateEntry` | Registro de ingreso de vehículo a garita. | `entry_id` (UUID) | `logistics/inbound` | MVP 2 |
| `Reception` | Acta y proceso de recepción en muelle. | `reception_id` (UUID) | `logistics/receptions` | MVP 2 |
| `ReceptionItem` | Detalle físico contado en recepción. | `reception_item_id` (UUID) | `logistics/receptions` | MVP 2 |
| `QualityInspection` | Protocolo de inspección de calidad. | `inspection_id` (UUID) | `logistics/quality` | MVP 2 |
| `NonConformity` | Registro de rechazo o falla de calidad. | `non_conformity_id` (UUID) | `logistics/quality` | MVP 2 |
| `InventoryMovement` | Transacción inmutable del Kardex. | `movement_id` (UUID) | `logistics/inventory` | MVP 2 |
| `StockBalance` | Saldo actual (Disponible/Reservado). | `balance_id` (UUID) | `logistics/stock` | MVP 2 |
| `InventoryLot` | Lote de fabricación y vencimiento. | `lot_id` (UUID) | `logistics/inventory` | MVP 2 |
| `SerialNumber` | Serie única por ítem/unidad. | `serial_id` (UUID) | `logistics/inventory` | MVP 2 |
| `LogisticUnit` | Contenedor / Pallet / LPN. | `lpn_id` (UUID) | `logistics/inventory` | MVP 2 |
| `StockReservation` | Reserva temporal para pedido de salida. | `reservation_id` (UUID) | `logistics/stock` | MVP 2 |
| `TransferOrder` | Orden de traslado entre almacenes. | `transfer_id` (UUID) | `logistics/transfers` | MVP 2 |
| `OutboundOrder` | Pedido de salida de cliente o interna. | `outbound_id` (UUID) | `logistics/outbound` | MVP 2 |
| `PickingTask` | Tarea asignada de recolección. | `picking_id` (UUID) | `logistics/picking` | MVP 2 |
| `PackingUnit` | Caja empaquetada lista para envío. | `packing_unit_id` (UUID) | `logistics/packing` | MVP 2 |
| `Dispatch` | Despacho de carga de almacén. | `dispatch_id` (UUID) | `logistics/dispatches` | MVP 2 |
| `Trip` | Viaje / Ruta de distribución programada. | `trip_id` (UUID) | `logistics/trips` | MVP 3 |
| `RoutePlan` | Secuencia planificada de paradas. | `route_plan_id` (UUID) | `logistics/routes` | MVP 3 |
| `RouteStop` | Parada individual en un cliente. | `stop_id` (UUID) | `logistics/routes` | MVP 3 |
| `GpsPosition` | Lectura de telemetría (Lat/Lng/Speed). | `position_id` (UUID) | `logistics/gps` | MVP 3 |
| `GeofenceEvent` | Evento de entrada/salida de zona. | `geofence_event_id` (UUID) | `logistics/gps` | MVP 3 |
| `Delivery` | Proceso de entrega al cliente. | `delivery_id` (UUID) | `logistics/deliveries` | MVP 3 |
| `ProofOfDelivery` | POD (Firma, foto, coordenadas, OTP). | `pod_id` (UUID) | `logistics/deliveries` | MVP 3 |
| `ReturnAuthorization` | RMA / Autorización de devolución. | `rma_id` (UUID) | `logistics/returns` | MVP 3 |
| `LogisticIncident` | Evento no deseado en ruta o almacén. | `incident_id` (UUID) | `logistics/incidents` | MVP 3 |
| `Document` | Documento logístico impreso/emitido. | `document_id` (UUID) | `logistics/documents` | MVP 1 |
| `DocumentSeries` | Serie y número correlativo. | `series_id` (UUID) | `logistics/documents` | MVP 1 |
| `DocumentSnapshot` | Snapshot inmutable JSON del documento. | `snapshot_id` (UUID) | `logistics/documents` | MVP 1 |
| `FileEvidence` | Archivo adjunto (PDF, JPG, PNG). | `file_id` (UUID) | `logistics/files` | MVP 1 |
| `AuditEvent` | Log inmutable de auditoría de seguridad. | `audit_id` (UUID) | `logistics/audit` | MVP 1 |
| `Notification` | Alerta enviada a usuario. | `notification_id` (UUID) | `logistics/notifications` | MVP 3 |
| `KpiDefinition` | Definición de fórmula e indicador. | `kpi_id` (UUID) | `logistics/kpis` | Consolidación |
