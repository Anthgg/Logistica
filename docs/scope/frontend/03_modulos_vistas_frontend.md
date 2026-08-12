# 03. Módulos y Pantallas del Frontend — Proyecto T1

Inventario de módulos y pantallas/vistas a construir en el frontend:

| Módulo Frontend | Nombre de Pantalla / Vista | Funcionalidad Principal de la Interfaz | Roles Autorizados |
|---|---|---|---|
| **Dashboard** | `DashboardOverview` | Tablero de resumen operativo (Órdenes pendientes, recepciones del día, camiones en ruta). | Todos los roles |
| **Maestros** | `ProductsMasterView` | Catálogo de SKUs, filtro por categoría, formulario de creación con carga de imagen. | `ACT_ADM`, `ACT_CMP` |
| **Maestros** | `WarehousesMasterView` | Configuración de almacenes y creador de mapa de pasillos/racks. | `ACT_ADM` |
| **Maestros** | `BusinessPartnersView` | Gestión de Clientes, Proveedores y Transportistas. Botón de "Consultar RUC SUNAT". | `ACT_ADM`, `ACT_CMP` |
| **Maestros** | `FleetAndDriversView` | Gestión de vehículos y conductores con semáforo de vencimiento SOAT/CITV/Licencia. | `ACT_ADM`, `ACT_PLN` |
| **Compras** | `PurchaseRequestsView` | Lista de requerimientos y creador de solicitudes de cotización. | `ACT_CMP` |
| **Compras** | `PurchaseOrderApprovalView` | Cuadro comparativo de cotizaciones y botón de aprobación de compra. | `ACT_GER`, `ACT_APROB` |
| **Recepción** | `GateControlView` | Registro de ingreso de camiones en garita para el guardia de seguridad. | `ACT_GAR` |
| **Recepción** | `DockReceptionView` | Interfaz de descarga en muelle, conteo de bultos y registro de discrepancias. | `ACT_REC` |
| **Calidad** | `QualityInspectionView` | Formulario de inspección de lotes, muestreo y pase a cuarentena / liberación. | `ACT_CAL` |
| **Inventario** | `StockKardexView` | Consulta de stock por almacén/lote/serie y visor inmutable del Kardex. | `ACT_ALM`, `ACT_AUD` |
| **Inventario** | `InventoryAdjustmentsView` | Formulario de ajustes de inventario con solicitud obligatoria de Step-Up. | `ACT_GER`, `ACT_ADM` |
| **Salidas** | `OutboundOrdersView` | Lista de pedidos de salida, asignación de picking y estado de reserva. | `ACT_DES` |
| **Picking/Packing** | `PickingExecutionView` | Interfaz optimizada de picking paso a paso con ruta de pasillos. | `ACT_PIC` |
| **Picking/Packing** | `PackingStationView` | Estación de empaque, asignación de peso y generación de etiqueta LPN. | `ACT_PAC` |
| **Despacho** | `DispatchConsoleView` | Emisión de Guía de Remisión y previsualizador PDF antes de salida de muelle. | `ACT_DES` |
| **Transporte** | `RoutePlannerView` | Planificador gráfico de viajes, ordenamiento de paradas y cálculo OSRM. | `ACT_PLN` |
| **Transporte** | `LiveGpsMonitorView` | Consola de mapa interactivo (MapLibre) con ubicación de vehículos en tiempo real. | `ACT_PLN`, `ACT_GER` |
| **Devoluciones** | `ReturnsAndIncidentsView` | Registro de incidencias en ruta y gestión de RMA / reingreso a almacén. | `ACT_REC`, `ACT_DES` |
| **Auditoría** | `SecurityAuditView` | Visor de logs de auditoría inmutables y monitoreo de confianza biométrica. | `ACT_AUD`, `ACT_ADM` |
| **KPIs** | `ExecutiveKpiView` | Tablero ejecutivo con gráficos de OTIF, ERI y rotación de inventario. | `ACT_GER` |
