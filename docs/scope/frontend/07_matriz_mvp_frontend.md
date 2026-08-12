# 07. Matriz de Fases y Distribución Frontend por MVP — Proyecto T1

## 1. Distribución de Pantallas por Etapa

### MVP 1 — Base UI, Layout, Maestros y Consulta RUC
- **Vistas Incluidas:**
  - `AppLayout` (Navbar, Sidebar, Footer, Token/Score Monitor).
  - `ProductsMasterView` (CRUD SKUs).
  - `WarehousesMasterView` (Configuración Almacenes/Ubicaciones).
  - `BusinessPartnersView` (Clientes/Proveedores con botón "Consultar RUC SUNAT").
  - `FleetAndDriversView` (Vehículos, Conductores, Vencimiento SOAT/Licencia).
  - `SecurityAuditView` (Visor de logs de seguridad).

### MVP 2 — Operación de Almacén, Compras e Inventario
- **Vistas Incluidas:**
  - `PurchaseRequestsView` & `PurchaseOrderApprovalView` (Compras).
  - `GateControlView` & `DockReceptionView` (Garita y Recepción en Muelle).
  - `QualityInspectionView` (Cuarentena / Liberación).
  - `StockKardexView` & `InventoryAdjustmentsView` (Saldos, Kardex, Ajustes).
  - `PickingExecutionView` & `PackingStationView` (Picking y Packing LPN).
  - `DispatchConsoleView` (Generación de Guías y Visor PDF).

### MVP 3 — Transporte, Monitoreo GPS y App Conductor
- **Vistas Incluidas:**
  - `RoutePlannerView` (Planificador de rutas).
  - `LiveGpsMonitorView` (Consola de mapa interactivo MapLibre GL).
  - `/driver/app` (App Móvil para conductor con GPS offline y POD).
  - `ReturnsAndIncidentsView` (Devoluciones e incidencias).

### Consolidación — KPIs, Exportaciones y Cierre
- **Vistas Incluidas:**
  - `ExecutiveKpiView` (Gráficos ejecutivos OTIF, ERI).
  - Modales de exportación masiva a Excel/CSV.
  - Pulido de micro-animaciones y accesibilidad.
