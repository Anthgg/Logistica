# Contratos Internos y Ownership de Datos · Fase 003

## 1. Definición y Mecanismos de Contratos Internos

En la arquitectura del Sistema Logístico, los contratos internos entre submódulos no se basan en un bus de eventos distribuido global ni en DTOs ficticios, sino en los siguientes mecanismos verificables en el código fuente:

1. **Esquemas Pydantic / DTOs Explícitos (`EXPLICIT_PYDANTIC_SCHEMA`):** Clases Pydantic en capas `presentation/schemas` o `application/dto` utilizadas para validar transferencias de datos entre módulos y capas.
2. **Métodos de Servicios de Aplicación (`SERVICE_METHOD`):** Métodos fuertemente tipados en clases de servicio que orquestan operaciones de dominio.
3. **Modelos Persistidos SQLAlchemy (`PERSISTED_RESOURCE`):** Entidades de base de datos utilizadas como contrato de persistencia e integridad referencial (Foreign Keys).
4. **Contexto de Seguridad (`LogisticsPrincipal`):** Contrato transversal que transporta la identidad del operador y permisos RBAC.

> **Nota Metodológica:** En los flujos donde no existe un DTO o evento desacoplado formal, se documenta explícitamente como `NO_EXPLICIT_INTERNAL_CONTRACT` o `PERSISTED_RESOURCE` para reflejar la realidad del código y evitar supuestos arquitectónicos.

---

## 2. Matriz de Contratos entre Dominios de Negocio

| Flujo | Productor | Consumidor | Contrato Real | Tipo | Evidencia (Ruta y Símbolo) | Ownership de Persistencia | Boundary de Falla |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Purchasing → Receiving** | `procurement.purchase_orders` | `inbound.arrival_notices` | `PurchaseOrderDetailResponse` / `PurchaseOrderModel` | `PERSISTED_RESOURCE` + `EXPLICIT_PYDANTIC_SCHEMA` | `backend/app/modules/logistics/procurement/purchase_orders/application/dto/schemas.py` (`PurchaseOrderDetailResponse`) y `models.py` (`PurchaseOrderModel`) | `procurement` (`purchase_orders`, `purchase_order_lines`) | Recepción valida estado de la orden; falla si `purchase_order_id` no existe o no está en estado liberado. |
| **Receiving → Inventory** | `inbound.receiving` | `inventory.ledger` | `PostInventoryMovementRequest` / `InventoryMovementResponse` | `SERVICE_METHOD` + `EXPLICIT_PYDANTIC_SCHEMA` | `backend/app/modules/logistics/inventory/ledger/presentation/schemas/schemas.py` (`PostInventoryMovementRequest`) y `ledger_service.py` (`post_movement`) | `inventory` (`inventory_ledger_entries`, `inventory_balances`) | No existe evento de dominio desacoplado (`NO_EXPLICIT_EVENT`). La comunicación ocurre mediante llamada directa al servicio contable del ledger. |
| **Inventory → Outbound** | `inventory` | `shipments` *(Módulo raíz)* | `ShipmentCreate` / `Shipment` | `PERSISTED_RESOURCE` | `backend/app/schemas/shipment.py` (`ShipmentCreate`) y `backend/app/models/shipment.py` (`Shipment`) | `shipments` (`shipments`) | `PARTIAL / ROOT_API_MODULE`. La integración de reserva de stock se realiza a nivel de endpoints raíz (Fase F051-F060 pendiente de retro-auditoría). |
| **Outbound → Transport** | `shipments` *(Módulo raíz)* | `vehicles`, `drivers` | `VehicleModel` / `DriverModel` | `PERSISTED_RESOURCE` | `backend/app/modules/logistics/vehicles/infrastructure/persistence/models.py` (`VehicleModel`) y `modules/logistics/drivers/infrastructure/persistence/models.py` (`DriverModel`) | `vehicles` (`vehicles`), `drivers` (`drivers`) | Asignación de vehículos y conductores mediante llaves foráneas directas. Falla si el recurso está bloqueado o con documentación vencida. |
| **Transport → Delivery** | `routes_module` / `vehicles` | `shipments` *(Módulo raíz)* | `DeliveryDocumentRenderRequest` / `DeliverySignatureSnapshot` | `EXPLICIT_PYDANTIC_SCHEMA` + `PERSISTED_RESOURCE` | `backend/app/modules/logistics/documents/rendering/delivery_schemas.py` (`DeliveryDocumentRenderRequest`) | `shipments` (`shipments`), `documents` (`document_catalog`) | Emisión y renderizado de comprobante de entrega (POD) con captura de firma y coordenadas de entrega. |
| **Delivery → Returns** | `shipments` *(Módulo raíz)* | `incidents` *(Módulo raíz)* / `inbound.reception_differences` | `IncidentCreate` / `Incident` | `PERSISTED_RESOURCE` | `backend/app/schemas/incident.py` (`IncidentCreate`) y `backend/app/models/incident.py` (`Incident`) | `incidents` (`incidents`) | No entrega o rechazo en destino genera incidencia en módulo raíz o diferencia de recepción en almacén. |
| **Todos los Dominios → Documents** | *Cualquier dominio logístico* | `documents` | `DocumentLifecycleService` / `DocumentCreateRequestSchema` | `SERVICE_METHOD` + `EXPLICIT_PYDANTIC_SCHEMA` | `backend/app/modules/logistics/documents/application/lifecycle_service.py` (`DocumentLifecycleService`) y `schemas.py` (`DocumentCreateRequestSchema`) | `documents` (`document_catalog`, `document_series`, `document_talonarios`) | El dominio invoca el servicio con metadatos; el motor asigna código/serie correlativa, valida talonario y renderiza el artefacto. |
| **Todos los Dominios → Audit** | *Cualquier dominio logístico* | `audit` | `AuditContextProvider` / `AuditAction` / `AuditEventService` | `SERVICE_METHOD` + `PERSISTED_RESOURCE` | `backend/app/modules/logistics/audit/domain/contracts.py` (`AuditContextProvider`, `AuditAction`) y `service.py` (`AuditEventService`) | `audit` (`audit_events`) | Registro de eventos no bloqueante con sanitización de datos sensibles (`sanitizer.py`). *(Unificación formal en F007)*. |
| **Todos los Dominios → Files** | *Cualquier dominio logístico* | `files` | `FileStorageService` / `FileUploadResponse` / `FileMetadataResponse` | `SERVICE_METHOD` + `EXPLICIT_PYDANTIC_SCHEMA` | `backend/app/modules/logistics/files/application/services/file_service.py` (`FileStorageService`) y `presentation/schemas/schemas.py` (`FileUploadResponse`) | `files` (`file_metadata`, `evidence_attachments`) | Custodia segura de binarios, cálculo de hash criptográfico SHA-256 y control de acceso. |
| **Maestros / Dominios → Integrations** | `partners` / `company_profile` | `ruc` / `integrations` | `RucLookupService` / `RucLookupResponseSchema` | `SERVICE_METHOD` + `EXPLICIT_PYDANTIC_SCHEMA` | `backend/app/modules/logistics/ruc/application/services/lookup_service.py` (`RucLookupService`) y `presentation/schemas/dto.py` (`RucLookupResponseSchema`) | `ruc` (`ruc_data_sources`, `ruc_data_conflicts`) | Consulta a APIs externas con fallback a cache local offline y registro de procedencia de campos. |

---

## 3. Matriz de Ownership de Datos y Entidades

| Entidad / Recurso | Dominio Propietario | Tabla Principal | Módulos con Acceso de Lectura | Módulos con Permiso de Modificación |
| :--- | :--- | :--- | :--- | :--- |
| **Company Profile** | `company_profile` | `company_profiles`, `company_addresses` | Todos | `company_profile` |
| **Organization / Sedes** | `organization` | `organizations`, `branches` | Todos | `organization` |
| **Warehouse / Ubicaciones** | `warehouses` | `warehouses`, `warehouse_locations` | `inventory`, `inbound`, `procurement` | `warehouses` |
| **Productos / Unidades** | `products`, `units` | `products`, `units_of_measure` | `procurement`, `inbound`, `inventory` | `products`, `units` |
| **Business Partners** | `partners` | `business_partners` | `procurement`, `inbound`, `ruc` | `partners` |
| **Centros de Costos** | `cost_centers` | `cost_centers` | `procurement` | `cost_centers` |
| **Requisiciones de Compra** | `procurement` | `purchase_requisitions` | `procurement.approvals` | `procurement.requisitions` |
| **Órdenes de Compra** | `procurement` / `purchase_orders` | `purchase_orders` | `inbound`, `procurement` | `procurement.purchase_orders` |
| **Garitas y Recepciones** | `inbound` | `warehouse_gates`, `receptions` | `inventory`, `documents` | `inbound` |
| **Kárdex y Saldos** | `inventory` | `inventory_ledger_entries`, `inventory_balances` | `procurement`, `shipments` | `inventory` |
| **Vehículos y Conductores** | `vehicles`, `drivers` | `vehicles`, `drivers` | `inbound`, `shipments` | `vehicles`, `drivers` |
| **Artefactos Documentales** | `documents` | `document_catalog`, `document_series` | Todos los dominios | `documents` |
| **Archivos y Evidencias** | `files` | `file_metadata`, `evidence_attachments` | Todos los dominios | `files` |
| **Eventos de Auditoría** | `audit` | `audit_events` | Seguridad / Auditoría | `audit` |
| **Roles y Permisos RBAC** | `rbac` | `roles`, `permissions`, `role_assignments` | Seguridad / Todos | `rbac` |
