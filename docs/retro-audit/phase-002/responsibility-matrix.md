# Matriz de Responsabilidades por Rol · Fase 002

Este documento formaliza los roles funcionales, técnicos y de seguridad que ejercen gobernanza sobre cada uno de los 12 dominios del **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales**.

---

## 1. Matriz de Responsables de Dominio Funcional

| Dominio Logístico | Código de Rol Responsable | Definición del Rol Funcional | Atribuciones y Responsabilidades Clave |
| :--- | :--- | :--- | :--- |
| **1. Compras** | `PURCHASING_OWNER` | Jefe / Responsable de Compras y Aprovisionamiento | Definición de flujos de requerimientos, evaluación de proveedores, aprobación de OCs y políticas de precios de compra. |
| **2. Recepción** | `RECEIVING_OWNER` | Supervisor de Recepción y Control de Muelles | Control de garita, citas de descarga, asignación de muelles, conteo por escaneo y resolución de diferencias de llegada. |
| **3. Almacenes** | `WAREHOUSE_OWNER` | Jefe de Almacén y Distribución | Modelado físico de almacenes, zonificación, jerarquía de racks/bins y reglas de ubicación dirigida (putaway). |
| **4. Inventario** | `INVENTORY_OWNER` | Responsable de Control de Inventarios | Integridad del libro de movimientos (ledger), conciliación de saldos de stock, conteos cíclicos y ajustes justificados. |
| **5. Trazabilidad** | `TRACEABILITY_OWNER` | Oficial de Calidad y Trazabilidad | Gobierno de lotes, series, unidades logísticas, eventos de auditoría inmutables y cadena de custodia de mercancías. |
| **6. Salida** | `OUTBOUND_OWNER` | Supervisor de Despacho y Preparación de Pedidos | Asignación de pedidos de salida, consolidación de olas de picking, control de packing y liberación de órdenes con Step-Up. |
| **7. Transporte** | `TRANSPORT_OWNER` | Jefe de Transporte y Gestión de Flota | Mantenimiento del maestro de vehículos y conductores, verificación de placas/licencias y asignación de rutas. |
| **8. Entrega** | `DELIVERY_OWNER` | Coordinador de Última Milla y Entregas | Supervisión de rutas en tránsito, validación de pruebas de entrega (POD), firmas digitales y resolución de entregas fallidas. |
| **9. Devoluciones** | `RETURNS_OWNER` | Responsable de Logística Inversa y Reclamos | Gestión de solicitudes RMA, inspección técnica de devoluciones, clasificación de destino y planes de acción correctiva. |
| **10. Documentos** | `DOCUMENT_CONTROL_OWNER` | Administrador de Control Documental | Catálogo de tipos documentales, correlatividad de talonarios, plantillas institucionales, firmas digitales y repositorio seguro. |
| **11. KPIs** | `ANALYTICS_OWNER` | Analista de Inteligencia de Negocios y Operaciones | Definición de fórmulas de cálculo de KPIs, dashboards gerenciales, reportes de rendimiento y exportaciones operativas. |
| **12. Integraciones** | `INTEGRATION_OWNER` | Ingeniero de Integraciones y Servicios Externos | Mantenimiento de conectores con SUNAT/RUC, servicios de placas, proveedores de mapas/ruteo y gestión de fallbacks. |

---

## 2. Responsabilidades Técnicas y de Seguridad Transversales

| Rol Transversal | Código de Rol | Responsabilidades |
| :--- | :--- | :--- |
| **Arquitectura y Release** | `TECHNICAL_OWNER` | Arquitectura del backend (FastAPI) y frontend (React), diseño de modelos relacionales, migraciones Alembic y pipelines de CI/CD. |
| **Seguridad de la Información** | `SECURITY_OWNER` | Gobernanza de autenticación continua, RBAC granular, políticas de tokens/cookies, protección anti-CSRF y encriptación de datos. |

---

## 3. Estado de Asignación Organizacional

> **Nota de Gobernanza:** En la línea base de desarrollo actual, las atribuciones de los roles funcionales están mapeadas a los catálogos de permisos y roles del sistema RBAC (`ROLE_LOGISTICS_ADMIN`, `ROLE_WAREHOUSE_SUPERVISOR`, `ROLE_PURCHASER`, `ROLE_DRIVER`, `ROLE_AUDITOR`, etc.). Los responsables nominales humanos específicos serán asignados por la administración de la organización durante la etapa de parametrización de producción (Fases F097-F100).
