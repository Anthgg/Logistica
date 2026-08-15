# Contratos Internos y Ownership de Datos · Fase 003

## 1. Definición de Contratos Internos

En la arquitectura del Sistema Logístico, los contratos internos se definen mediante:
1. **Esquemas Pydantic / DTOs:** Interfaces estructuradas de entrada/salida entre capas y clientes.
2. **Servicios de Aplicación:** Clases que exponen métodos públicos con tipos estrictos para ejecutar casos de uso.
3. **Modelos de Entidad SQLAlchemy:** Definición formal de esquemas relacionales, llaves primarias, llaves foráneas e índices.
4. **LogisticsPrincipal / Identity Context:** Contrato de seguridad que transporta identidad de usuario, roles RBAC y atributos de contexto.

---

## 2. Mapa de Contratos entre Dominios de Negocio

| Productor | Consumidor | Recurso / Transacción | Contrato / DTO | Ownership de Persistencia | Boundary de Falla |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Purchasing** (`procurement`) | **Receiving** (`inbound`) | Orden de Compra Aprobada | `PurchaseOrderResponseDTO`, `POLineItemDTO` | `procurement.purchase_orders` | Recepción falla con `PO_NOT_FOUND` o `PO_NOT_APPROVED` si la orden no está liberada. |
| **Receiving** (`inbound`) | **Inventory** (`inventory`) | Mercancía Recibida y Verificada | `InboundReceivingCompletedEvent`, `StockMovementDTO` | `inbound.receptions` | Si la recepción falla en calidad, el stock se aísla en cuarentena y no entra al balance disponible. |
| **Inventory** (`inventory`) | **Outbound** (`shipments`) | Reserva y Despacho de Stock | `InventoryReservationDTO`, `StockLedgerEntryDTO` | `inventory.stock_ledger` | Falla con `INSUFFICIENT_STOCK` si la cantidad solicitada excede el saldo contable. |
| **Outbound** (`shipments`) | **Transport** (`vehicles`, `drivers`) | Asignación de Despacho a Vehículo/Conductor | `DispatchAssignmentDTO`, `VehicleCapacityCheckDTO` | `shipments.shipments` | Falla si el vehículo o conductor tienen restricciones de cumplimiento/documentales. |
| **Transport** (`routes`, `vehicles`) | **Delivery** (`shipments`) | Manifiesto de Ruta y Entrega | `RouteManifestDTO`, `DeliveryProofDTO` | `shipments.shipments` | Registro de POD (Proof of Delivery) y firma del receptor. |
| **Delivery** (`shipments`) | **Returns** (`incidents`) | Reporte de No Entrega o Rechazo | `DeliveryIncidentDTO`, `ReturnAuthorizationDTO` | `incidents.incidents` | Generación de diferencia de recepción / cuarentena de retorno. |
| **Todos los Dominios** | **Documents** (`documents`) | Generación y Foliado de Documentos | `DocumentGenerationRequestDTO`, `DocumentArtifactDTO` | `documents.document_catalog` | El dominio envía el payload; el motor documental asigna serie/código y renderiza HTML/PDF. |
| **Todos los Dominios** | **Audit** (`audit`) | Registro de Eventos de Auditoría | `AuditEventCreateDTO`, `AuditContextDTO` | `audit.audit_events` | Fallback asíncrono o transaccional; sanitiza payloads antes de guardar. |
| **Todos los Dominios** | **Files** (`files`) | Adjunto de Evidencias / Binarios | `FileUploadResponseDTO`, `FileHashDTO` | `files.file_metadata` | Almacenamiento seguro, cálculo de SHA-256 y control de acceso. |
| **Dominios de Maestros** | **Integrations** (`ruc`, `partners`) | Validación de RUC / Socios | `RucLookupResponseDTO`, `ProviderVerificationDTO` | `ruc.ruc_cache` | Consulta a APIs externas con fallback a cache local y modo offline. |

---

## 3. Matriz de Ownership de Datos y Entidades

| Entidad / Recurso | Dominio Propietario | Tabla Principal | Módulos con Acceso de Lectura | Módulos con Acceso de Escritura |
| :--- | :--- | :--- | :--- | :--- |
| **Company Profile** | `company_profile` | `company_profiles`, `company_addresses` | Todos | `company_profile` |
| **Organization / Sede** | `organization` | `organizations`, `branches` | Todos | `organization` |
| **Warehouse / Location** | `warehouses` | `warehouses`, `warehouse_locations` | `inventory`, `inbound`, `procurement` | `warehouses` |
| **Product / Category / Unit** | `products`, `units` | `products`, `units_of_measure` | `procurement`, `inbound`, `inventory` | `products`, `units` |
| **Business Partner / Supplier**| `partners` | `business_partners` | `procurement`, `inbound`, `ruc` | `partners` |
| **Cost Center** | `cost_centers` | `cost_centers` | `procurement` | `cost_centers` |
| **Purchase Requisition** | `procurement` | `purchase_requisitions` | `procurement.approvals` | `procurement.requisitions` |
| **Purchase Order** | `procurement` / `purchase_orders` | `purchase_orders` | `inbound`, `procurement` | `procurement.purchase_orders` |
| **Inbound Gate / Reception** | `inbound` | `warehouse_gates`, `receptions` | `inventory`, `documents` | `inbound` |
| **Stock Ledger / Balance** | `inventory` | `inventory_ledger_entries`, `inventory_balances` | `procurement`, `shipments` | `inventory` |
| **Vehicle / Driver** | `vehicles`, `drivers` | `vehicles`, `drivers` | `inbound`, `shipments` | `vehicles`, `drivers` |
| **Document Artifact / Series**| `documents` | `document_catalog`, `document_series` | Todos | `documents` |
| **File / Binary Evidence** | `files` | `file_metadata`, `evidence_attachments` | Todos | `files` |
| **Audit Event** | `audit` | `audit_events` | Auditoría / Seguridad | `audit` |
| **RBAC Roles / Permissions** | `rbac` | `roles`, `permissions`, `role_assignments` | Seguridad / Todos | `rbac` |
