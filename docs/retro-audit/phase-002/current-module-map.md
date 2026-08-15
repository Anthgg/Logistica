# Mapeo de Módulos Existentes en Backend y Frontend · Fase 002

Este documento mapea la implementación existente en el repositorio respecto a la delimitación de dominios de la Fase 002.

---

## 1. Mapeo Backend (`Anthgg/Logistica`)

| Dominio | Módulos y Paquetes Backend | Tablas Relacionales (PostgreSQL) | Rutas API y Routers |
| :--- | :--- | :--- | :--- |
| **Compras** | `app/modules/logistics/procurement/*`, `app/modules/logistics/purchase_orders` | `purchase_requisitions`, `purchase_orders`, `purchase_order_lines`, `supplier_evaluations`, `procurement_approvals` | `/api/logistics/purchase-orders`, `/api/logistics/requisitions`, `/api/logistics/evaluations` |
| **Recepción** | `app/modules/logistics/inbound/*`, `app/modules/logistics/gate_control` | `arrival_notices`, `gate_entries`, `dock_assignments`, `receptions`, `reception_differences`, `quality_inspection_plans` | `/api/logistics/inbound/*`, `/api/logistics/gate-control/*` |
| **Almacenes** | `app/modules/logistics/warehouses`, `app/services/warehouse_service.py` | `warehouses`, `warehouse_zones`, `warehouse_locations`, `storage_bins` | `/api/warehouses`, `/api/logistics/warehouses/*` |
| **Inventario** | `app/modules/logistics/inventory/*`, `app/services/inventory_service.py` | `inventory_ledger_entries`, `inventory_balances`, `inventory_snapshots`, `inventory_adjustments` | `/api/inventory`, `/api/logistics/inventory/*` |
| **Trazabilidad** | `app/modules/logistics/audit`, `app/services/audit_service.py` | `audit_logs`, `audit_events` | `/api/audit/*` |
| **Salida** | `app/services/shipment_service.py` | `shipments`, `shipment_items` | `/api/shipments` |
| **Transporte** | `app/modules/logistics/vehicles`, `drivers`, `vehicle_verifications`, `routes_module` | `vehicles`, `drivers`, `vehicle_verifications`, `logistic_routes` | `/api/logistics/vehicles/*`, `/api/logistics/drivers/*`, `/api/logistics/routes/*` |
| **Entrega** | `app/services/shipment_service.py` | `shipments`, `stored_files` | `/api/shipments/*` |
| **Devoluciones** | `app/services/incident_service.py` | `incidents`, `incident_evidence` | `/api/incidents/*` |
| **Documentos** | `app/modules/logistics/documents`, `app/modules/logistics/files` | `document_types`, `document_series`, `document_templates`, `document_instances`, `stored_files` | `/api/logistics/documents/*`, `/api/logistics/files/*` |
| **KPIs** | `app/services/dashboard_service.py`, `app/services/report_service.py` | Vistas y agregaciones | `/api/dashboard`, `/api/reports` |
| **Integraciones** | `app/modules/logistics/ruc`, `integrations`, `vehicle_verifications` | `external_integrations`, `ruc_consultation_cache`, `vehicle_verification_sources` | `/api/logistics/ruc/*`, `/api/logistics/integrations/*` |

---

## 2. Mapeo Frontend (`Anthgg/LogisticaF`)

| Dominio | Features / Componentes React | Páginas SPA | Clientes API |
| :--- | :--- | :--- | :--- |
| **Compras** | `features/purchase-orders`, `features/procurement-approvals`, `features/supplier-evaluation` | `PurchaseRequisitionsPage.tsx`, `PurchaseOrdersPage.tsx`, `PurchaseOrderDetailPage.tsx` | `purchaseOrdersApi.ts`, `requisitionsApi.ts` |
| **Recepción** | `features/gate-control`, `features/inbound-docks`, `features/inbound-receiving`, `features/reception-differences`, `features/quality-inspection-plans` | `InboundCalendarPage.tsx`, `GateControlPage.tsx`, `DocksPage.tsx`, `QualityPlansPage.tsx` | `gateControlApi.ts`, `inboundReceivingApi.ts`, `receptionDifferencesApi.ts` |
| **Almacenes** | `features/putaway` | `WarehousesPage.tsx`, `WarehouseDetailPage.tsx` | `warehousesApi.ts` |
| **Inventario** | `features/inventory-ledger`, `features/inventory-balances`, `features/putaway` | `InventoryPage.tsx` | `inventoryApi.ts`, `inventoryBalancesApi.ts` |
| **Trazabilidad** | - | `AuditEventsPage.tsx` | `auditEventsApi.ts` |
| **Salida** | `features/shipments` | `ShipmentsPage.tsx`, `ShipmentDetailPage.tsx` | `shipmentsApi.ts` |
| **Transporte** | - | `VehiclesPage.tsx`, `DriversPage.tsx`, `RoutesPage.tsx`, `VehicleVerificationsPage.tsx` | `vehiclesApi.ts`, `driversApi.ts`, `routesApi.ts` |
| **Entrega** | - | `ShipmentDetailPage.tsx`, `EvidencePage.tsx` | `shipmentsApi.ts`, `filesApi.ts` |
| **Devoluciones** | - | `IncidentsPage.tsx` | `incidentsApi.ts` |
| **Documentos** | `components/company/InstitutionalDocumentPreview.tsx`, `SecurePdfViewer.tsx`, `NumberingPoliciesPanel.tsx` | `DocumentsPage.tsx`, `FilesRepositoryPage.tsx`, `FileUploadPage.tsx` | `documentsApi.ts`, `filesApi.ts`, `pdfClient.ts` |
| **KPIs** | - | `DashboardPage.tsx`, `ReportsPage.tsx` | `dashboardApi.ts`, `reportsApi.ts` |
| **Integraciones** | - | `RucIntegrationPage.tsx`, `VehicleVerificationSourcesPage.tsx` | `rucApi.ts`, `integrationsApi.ts` |
