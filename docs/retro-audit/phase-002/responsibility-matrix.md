# Matriz de Responsabilidades y Gobierno · Fase 002

Este documento formaliza el modelo de responsabilidades del **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales**, estableciendo una estricta separación conceptual entre los tres niveles de responsabilidad:

1. **Governance Owner:** Responsable funcional/conceptual del dominio de negocio.
2. **Current RBAC Mapping:** Roles técnicos de software realmente implementados en el catálogo RBAC del backend (`backend/app/modules/logistics/rbac/catalog.py`).
3. **Human Owner:** Asignación nominal humana (`ROLE_TO_BE_ASSIGNED`).

> **Regla de Gobernanza:** Los Governance Owners son responsabilidades conceptuales de dominio y NO deben confundirse con roles técnicos de RBAC. Cuando existe correspondencia funcional, se documentan los roles RBAC técnicos actualmente implementados por separado. Los responsables nominales deberán asignarse durante la parametrización organizacional antes de la entrada a producción.

---

## 1. Matriz de Responsabilidad por Dominio Logístico

| Dominio | Governance Owner (Conceptual) | Current RBAC Mapping (Implementado en Software) | Human Owner | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **1. Compras** | `PURCHASING_OWNER` | `PURCHASING`, `PURCHASING_APPROVER` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |
| **2. Recepción** | `RECEIVING_OWNER` | `GATE_CONTROL`, `RECEIVING`, `QUALITY` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |
| **3. Almacenes** | `WAREHOUSE_OWNER` | `WAREHOUSE_OPERATOR` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |
| **4. Inventario** | `INVENTORY_OWNER` | `INVENTORY_CONTROLLER`, `INVENTORY_OPERATOR`, `INVENTORY_AUDITOR`, `LEDGER_ADMIN` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |
| **5. Trazabilidad** | `TRACEABILITY_OWNER` | Roles de apoyo: `LOGISTICS_AUDITOR`, `QUALITY` *(Sin rol RBAC único exclusivo)* | `ROLE_TO_BE_ASSIGNED` | `SUPPORTING_ROLES` |
| **6. Salida** | `OUTBOUND_OWNER` | `DISPATCH` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |
| **7. Transporte** | `TRANSPORT_OWNER` | `TRANSPORT_PLANNER`, `TRANSPORT_MONITOR` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |
| **8. Entrega** | `DELIVERY_OWNER` | `DRIVER` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |
| **9. Devoluciones** | `RETURNS_OWNER` | `NO_DIRECT_RBAC_EQUIVALENT` *(Roles de apoyo: `QUALITY`, `LOGISTICS_MANAGER`)* | `ROLE_TO_BE_ASSIGNED` | `NO_DIRECT_RBAC` |
| **10. Documentos** | `DOCUMENT_CONTROL_OWNER` | `DOCUMENT_CONTROLLER` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |
| **11. KPIs** | `ANALYTICS_OWNER` | `NO_DIRECT_RBAC_EQUIVALENT` *(Roles de apoyo: `LOGISTICS_MANAGER`, `LOGISTICS_ADMIN`, `LOGISTICS_VIEWER`)* | `ROLE_TO_BE_ASSIGNED` | `NO_DIRECT_RBAC` |
| **12. Integraciones** | `INTEGRATION_OWNER` | `SYSTEM_INTEGRATION_SERVICE`, `LOGISTICS_ADMIN` | `ROLE_TO_BE_ASSIGNED` | `ACTIVE_MAPPING` |

---

## 2. Responsabilidades Técnicas y de Seguridad Transversales

| Rol Transversal | Governance Owner | Current RBAC Mapping | Human Owner | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Arquitectura y Release** | `TECHNICAL_OWNER` | `NO_DIRECT_RBAC_EQUIVALENT` *(Gestión de infraestructura, DevOps y repositorio Git fuera de RBAC logístico)* | `ROLE_TO_BE_ASSIGNED` | `INFRASTRUCTURE` |
| **Seguridad de la Información** | `SECURITY_OWNER` | `NO_DIRECT_RBAC_EQUIVALENT` *(Políticas de CISO, autenticación continua y criptografía fuera de RBAC logístico)* | `ROLE_TO_BE_ASSIGNED` | `INFRASTRUCTURE` |

---

## 3. Catálogo Real de Roles RBAC en Backend (`SYSTEM_ROLES`)

Los 20 roles del sistema implementados en `backend/app/modules/logistics/rbac/catalog.py` son:

1. `LOGISTICS_ADMIN` — Administrador logístico
2. `LOGISTICS_MANAGER` — Gerencia logística
3. `PURCHASING` — Compras
4. `PURCHASING_APPROVER` — Aprobador de compras
5. `GATE_CONTROL` — Control de puerta
6. `RECEIVING` — Recepción
7. `QUALITY` — Control de calidad
8. `WAREHOUSE_OPERATOR` — Operador de almacén
9. `INVENTORY_CONTROLLER` — Control de inventario
10. `INVENTORY_OPERATOR` — Operador del libro de inventario
11. `INVENTORY_AUDITOR` — Auditor del libro de inventario
12. `SYSTEM_INTEGRATION_SERVICE` — Servicio de integración logística
13. `LEDGER_ADMIN` — Administrador del libro de inventario
14. `DISPATCH` — Despacho
15. `TRANSPORT_PLANNER` — Planificador de transporte
16. `TRANSPORT_MONITOR` — Monitor de transporte
17. `DRIVER` — Conductor
18. `DOCUMENT_CONTROLLER` — Control documental
19. `LOGISTICS_AUDITOR` — Auditor logístico
20. `LOGISTICS_VIEWER` — Consulta logística
