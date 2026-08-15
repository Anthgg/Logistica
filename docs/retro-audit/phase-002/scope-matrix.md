# Matriz de Alcance Logístico · Fase 002

Esta matriz consolida la delimitación oficial de los 12 dominios funcionales del **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales**, conforme al Plan Maestro de Implementación en 100 Fases.

---

## 1. Matriz General de Dominios Logísticos

| Dominio | Backend | Frontend | DB | API | Responsable | Estado de Implementación |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Compras (Purchasing)** | `app/modules/logistics/procurement/*` | `features/purchase-orders`, `features/procurement-approvals`, `features/supplier-evaluation` | `purchase_requisitions`, `purchase_orders`, `supplier_evaluations` | `/api/logistics/purchase-orders`, `/api/logistics/requisitions` | `PURCHASING_OWNER` | `EXISTS` |
| **2. Recepción (Receiving)** | `app/modules/logistics/inbound/*` | `features/gate-control`, `features/inbound-docks`, `features/inbound-receiving`, `features/reception-differences` | `arrival_notices`, `gate_entries`, `dock_assignments`, `receptions`, `reception_differences` | `/api/logistics/inbound/*`, `/api/logistics/gate-control/*` | `RECEIVING_OWNER` | `EXISTS` |
| **3. Almacenes (Warehousing)** | `app/modules/logistics/warehouses`, `app/services/warehouse_service.py` | `pages/WarehousesPage.tsx`, `pages/WarehouseDetailPage.tsx`, `features/putaway` | `warehouses`, `warehouse_zones`, `warehouse_locations`, `storage_bins` | `/api/warehouses`, `/api/logistics/warehouses/*` | `WAREHOUSE_OWNER` | `EXISTS` |
| **4. Inventario (Inventory)** | `app/modules/logistics/inventory/*`, `app/services/inventory_service.py` | `features/inventory-ledger`, `features/inventory-balances`, `pages/InventoryPage.tsx` | `inventory_ledger_entries`, `inventory_balances`, `inventory_snapshots` | `/api/inventory`, `/api/logistics/inventory/*` | `INVENTORY_OWNER` | `EXISTS` |
| **5. Trazabilidad (Traceability)** | `app/modules/logistics/audit`, `app/services/audit_service.py` | `pages/AuditEventsPage.tsx` | `audit_logs`, `audit_events` | `/api/audit/*` | `TRACEABILITY_OWNER` | `PARTIAL` |
| **6. Salida (Outbound)** | `app/services/shipment_service.py` | `features/shipments`, `pages/ShipmentsPage.tsx` | `shipments`, `shipment_items` | `/api/shipments` | `OUTBOUND_OWNER` | `PARTIAL` |
| **7. Transporte (Transport)** | `app/modules/logistics/vehicles`, `drivers`, `vehicle_verifications`, `routes_module` | `pages/VehiclesPage.tsx`, `pages/DriversPage.tsx`, `pages/RoutesPage.tsx`, `pages/VehicleVerificationsPage.tsx` | `vehicles`, `drivers`, `vehicle_verifications`, `logistic_routes` | `/api/logistics/vehicles/*`, `/api/logistics/drivers/*`, `/api/logistics/routes/*` | `TRANSPORT_OWNER` | `EXISTS` |
| **8. Entrega (Delivery)** | `app/services/shipment_service.py` | `pages/ShipmentDetailPage.tsx`, `pages/EvidencePage.tsx` | `shipments`, `stored_files` | `/api/shipments/*` | `DELIVERY_OWNER` | `PARTIAL` |
| **9. Devoluciones (Returns)** | `app/services/incident_service.py` | `pages/IncidentsPage.tsx` | `incidents`, `incident_evidence` | `/api/incidents/*` | `RETURNS_OWNER` | `PARTIAL` |
| **10. Documentos (Documents)** | `app/modules/logistics/documents`, `app/modules/logistics/files` | `pages/DocumentsPage.tsx`, `pages/FilesRepositoryPage.tsx`, `components/company/InstitutionalDocumentPreview.tsx` | `document_types`, `document_series`, `document_templates`, `document_instances`, `stored_files` | `/api/logistics/documents/*`, `/api/logistics/files/*` | `DOCUMENT_CONTROL_OWNER` | `EXISTS` |
| **11. KPIs y Analítica (Analytics)** | `app/services/dashboard_service.py`, `app/services/report_service.py` | `pages/DashboardPage.tsx`, `pages/ReportsPage.tsx` | Vistas agregadas y queries de métricas en tiempo real | `/api/dashboard`, `/api/reports` | `ANALYTICS_OWNER` | `EXISTS` |
| **12. Integraciones Externas** | `app/modules/logistics/ruc`, `integrations`, `vehicle_verifications` | `pages/RucIntegrationPage.tsx`, `pages/VehicleVerificationSourcesPage.tsx` | `external_integrations`, `ruc_consultation_cache`, `vehicle_verification_sources` | `/api/logistics/ruc/*`, `/api/logistics/integrations/*` | `INTEGRATION_OWNER` | `EXISTS` |

---

## 2. Descripción de Estados de Implementación

- `EXISTS`: Módulo con modelos, servicios, endpoints y vistas correspondientes implementados en la base de código.
- `PARTIAL`: Módulo con cimientos funcionales o preliminares implementados, cuya completitud avanzada está programada en bloques posteriores del Plan Maestro (ej. F046 para unidades logísticas avanzadas, F051-F060 para picking/packing completo, F071-F080 para prueba de entrega móvil integral).
- `NOT_IMPLEMENTED`: Funcionalidad que no cuenta con código productivo en la línea base actual.
- `OUT_OF_SCOPE`: Funcionalidad formalmente excluida del alcance del primer lanzamiento (ej. Facturación tributaria automática).
- `MIXED_RESPONSIBILITY`: Módulos con solapamiento de dependencias que han sido identificados para su clara separación de responsabilidades.
