# 03. Módulos Backend Propuestos — `/api/logistics`

## Architecture Layout

Los módulos futuros del backend se estructurarán en `backend/app/api/routes/logistics/` respetando los principios de Domain-Driven Design (DDD) y manteniendo un desacoplamiento estricto con los módulos de autenticación continua.

```text
backend/app/
├── api/
│   └── routes/
│       └── logistics/
│           ├── configuration/
│           ├── organizations/
│           ├── branches/
│           ├── warehouses/
│           ├── locations/
│           ├── products/
│           ├── units/
│           ├── business_partners/
│           ├── suppliers/
│           ├── customers/
│           ├── carriers/
│           ├── vehicles/
│           ├── drivers/
│           ├── purchases/
│           ├── purchase_orders/
│           ├── inbound/
│           ├── receptions/
│           ├── quality/
│           ├── inventory/
│           ├── stock/
│           ├── transfers/
│           ├── outbound/
│           ├── picking/
│           ├── packing/
│           ├── dispatches/
│           ├── trips/
│           ├── routes/
│           ├── gps/
│           ├── deliveries/
│           ├── returns/
│           ├── incidents/
│           ├── documents/
│           ├── files/
│           ├── audit/
│           ├── kpis/
│           ├── integrations/
│           └── notifications/
```

---

## Especificación Detallada por Módulo

### 1. `logistics/configuration` & `organizations` & `branches`
- **Propósito:** Administración de datos de la empresa, sedes operativas y variables globales.
- **Servicios:** `OrganizationService`, `BranchService`.
- **Dependencias Permitidas:** `core.database`, `dependencies.auth`.
- **Fase:** MVP 1.

### 2. `logistics/warehouses` & `locations`
- **Propósito:** Configuración de la estructura física del almacén y zonificación.
- **Servicios:** `WarehouseService`, `LocationService`.
- **Dependencias Permitidas:** `organizations`, `branches`.
- **Fase:** MVP 1.

### 3. `logistics/products` & `units`
- **Propósito:** Gestión del maestro de artículos, SKUs, categorías y factores de conversión UOM.
- **Servicios:** `ProductService`, `UnitConversionService`.
- **Dependencias Permitidas:** `core.database`.
- **Fase:** MVP 1.

### 4. `logistics/business_partners` (Suppliers, Customers, Carriers, Vehicles, Drivers)
- **Propósito:** Registro y verificación de entidades de negocio externas, conductores y vehículos.
- **Servicios:** `PartnerService`, `VehicleService`, `DriverService`.
- **Dependencias Permitidas:** `logistics/integrations` (para validación RUC/MTC/SOAT).
- **Fase:** MVP 1.

### 5. `logistics/purchases` & `purchase_orders`
- **Propósito:** Gestión del ciclo de abastecimiento: requerimientos, cotizaciones y órdenes de compra.
- **Servicios:** `PurchaseRequestService`, `PurchaseOrderService`.
- **Dependencias Permitidas:** `products`, `suppliers`, `documents`.
- **Fase:** MVP 2.

### 6. `logistics/inbound` & `receptions` & `quality`
- **Propósito:** Recepción física en garita/muelle, actas de recepción e inspecciones de calidad.
- **Servicios:** `ReceptionService`, `QualityService`.
- **Dependencias Permitidas:** `purchase_orders`, `warehouses`, `locations`, `inventory`.
- **Fase:** MVP 2.

### 7. `logistics/inventory` & `stock` & `transfers`
- **Propósito:** Motor transaccional de stock: saldos, kardex, reservas, lotes, series y transferencias.
- **Servicios:** `StockTransactionService`, `KardexService`, `TransferService`.
- **Dependencias Permitidas:** `products`, `locations`, `warehouses`.
- **Dependencias Prohibidas:** No importar directamente lógica de interfaz web o presentación.
- **Fase:** MVP 2.

### 8. `logistics/outbound` & `picking` & `packing` & `dispatches`
- **Propósito:** Preparación y salida de mercadería de almacén.
- **Servicios:** `OutboundOrderService`, `PickingService`, `PackingService`, `DispatchService`.
- **Dependencias Permitidas:** `inventory`, `customers`, `documents`, `carriers`.
- **Fase:** MVP 2.

### 9. `logistics/trips` & `routes` & `gps` & `deliveries` & `returns` & `incidents`
- **Propósito:** Logística de transporte, monitoreo de ruta en tiempo real, prueba de entrega digital (POD) y devoluciones.
- **Servicios:** `TripService`, `GpsTrackingService`, `DeliveryService`, `ReturnService`, `IncidentService`.
- **Dependencias Permitidas:** `dispatches`, `vehicles`, `drivers`, `files`, `integrations`.
- **Fase:** MVP 3.

### 10. `logistics/documents` & `files` & `audit` & `kpis` & `notifications` & `integrations`
- **Propósito:** Servicios transversales del sistema (PDF, Cloud Storage, Audit Log, KPIs, SMS/Email, RUC/MTC APIs).
- **Servicios:** `DocumentEngineService`, `StorageService`, `AuditLogService`, `KpiCalculatorService`, `NotificationService`, `ExternalApiService`.
- **Dependencias Permitidas:** `core.config`, Google Cloud Storage Client, HTTPX.
- **Fase:** MVP 1 a Consolidación.
