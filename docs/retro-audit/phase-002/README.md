# Retro-Auditoría · Fase 002: Definir el Alcance Logístico

---

## 1. Objetivo Oficial
El objetivo de la **Fase 002** es definir, delimitar y formalizar el alcance funcional del **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales**, estableciendo con precisión las fronteras operativas entre los 12 dominios logísticos, identificando las inclusiones del primer lanzamiento (`IN_SCOPE_V1`), las exclusiones oficiales confirmadas por el Plan Maestro (`OFFICIAL_OUT_OF_SCOPE_V1`), las exclusiones aprobadas por el usuario (`APPROVED_OUT_OF_SCOPE_V1`) y asignando el modelo de gobernanza por roles.

---

## 2. Trabajo Oficial
- Delimitación y separación clara de los 12 dominios logísticos:
  1. Compras (Purchasing)
  2. Recepción (Receiving)
  3. Almacenes (Warehousing)
  4. Inventario (Inventory)
  5. Trazabilidad (Traceability)
  6. Salida (Outbound)
  7. Transporte (Transport)
  8. Entrega (Delivery)
  9. Devoluciones (Returns)
  10. Documentos (Documents)
  11. KPIs y Analítica (Analytics)
  12. Integraciones Externas (Integrations)
- Exclusión oficial explícita de la facturación tributaria automática para el primer lanzamiento.
- Ratificación de exclusiones operativas de pasarelas de pago, contabilidad financiera, planillas y mantenimiento mecánico pesado.
- Establecimiento del modelo de responsabilidades en tres niveles: Governance Owner, Current RBAC Mapping y Human Owner.

---

## 3. Criterio de Cierre
- Documento de alcance formalizado que contenga la matriz de 12 dominios, inclusiones oficiales, exclusiones aprobadas y matriz de responsabilidades.
- Verificación en código de que no existe invasión de alcance por facturación tributaria automática de venta.
- Aprobación explícita del alcance por parte del usuario (`SCOPE_ACCEPTANCE: PASS`).

---

## 4. Clasificación de Fase
- **Categoría:** `INFRASTRUCTURE / GOVERNANCE / SCOPE`
- **Modificación de Código Productivo:** `NONE` (0 archivos modificados en `backend/app/`, 0 migraciones).
- **Modificación de Frontend:** `NONE` (0 componentes o páginas modificadas).
- **Alcance de Cambios:** Exclusivamente documental (`docs/retro-audit/**`).

---

## 5. Baselines de Git y Release Gate
- **Repositorio Backend:** `https://github.com/Anthgg/Logistica.git`
  - **Rama Base:** `main` (`46b9c5d3329676efa9f7d9281cb08ad04317936e` — Merge oficial de F001)
  - **Rama de Auditoría:** `audit/retro-phase-002-backend`
  - **Worktree Aislado:** `C:/Users/anthg/Logistica-F002`
- **Repositorio Frontend:** `https://github.com/Anthgg/LogisticaF.git`
  - **Rama Base:** `main` (`699cbfbfc86a7378bac2a4d28fdc3f7285a13564`)
  - **Rama de Auditoría:** `N/A` (Sin modificaciones en frontend)

---

## 6. Inventario Backend por Dominios
- `app/modules/logistics/procurement/*`: Requerimientos, solicitudes de cotización, evaluación de proveedores, órdenes de compra y aprobaciones.
- `app/modules/logistics/inbound/*`: Avisos de llegada, control de garita, muelles, recepción por escaneo y actas de diferencias.
- `app/modules/logistics/warehouses`: Almacenes, zonas, ubicaciones, pasillos, racks y compartimentos.
- `app/modules/logistics/inventory/*`: Libro de inventario (ledger), saldos de stock (balances) y ubicación dirigida (putaway).
- `app/modules/logistics/audit`: Eventos de auditoría unificados y trazabilidad.
- `app/modules/logistics/vehicles`, `drivers`, `vehicle_verifications`, `routes_module`: Flota, conductores, validación de placas y ruteo.
- `app/modules/logistics/documents`, `files`: Motor documental institucional, series, plantillas HTML/PDF y bóveda de evidencias.
- `app/modules/logistics/ruc`, `integrations`: Consulta RUC y conectores externos.

---

## 7. Inventario Frontend por Dominios
- Features: `features/purchase-orders`, `procurement-approvals`, `supplier-evaluation`, `gate-control`, `inbound-docks`, `inbound-receiving`, `reception-differences`, `quality-inspection-plans`, `quarantine`, `inventory-ledger`, `inventory-balances`, `putaway`, `shipments`.
- Páginas: 70 páginas SPA estructuradas por módulos correspondientes a los dominios operativos y de configuración.
- Clientes HTTP: Módulos API dedicados bajo `src/api/*` con inyección de CSRF y tipado TypeScript estricto.

---

## 8. Dominios Incluidos (IN_SCOPE_V1) — APROBADO
1. **Compras:** Requerimientos, cotizaciones, evaluación de proveedores, OCs y aprobaciones.
2. **Recepción:** Avisos de llegada, garita, muelles, recepción física, diferencias y control de calidad/cuarentena.
3. **Almacenes:** Modelado de almacenes, zonificación, ubicaciones jerárquicas y putaway.
4. **Inventario:** Ledger inmutable, cálculo de saldos disponibles/reservados/bloqueados, conteos y transferencias.
5. **Trazabilidad:** Auditoría inmutable de eventos, lotes/series y ciclo de vida documental.
6. **Salida:** Pedidos de salida, reserva preventiva de existencias, picking, packing y autorización de despacho.
7. **Transporte:** Vehículos, conductores, verificación de placas/licencias y rutas de transporte.
8. **Entrega:** Despacho, prueba de entrega (POD), firmas digitales y gestión de rechazos.
9. **Devoluciones:** Logística inversa, solicitudes RMA, inspección de devolución e incidencias.
10. **Documentos:** Series, talonarios, plantillas, PDF/impresión, anulación y archivo con SHA-256.
11. **KPIs:** Dashboards operativos, métricas OTIF, rotación y reportes gerenciales.
12. **Integraciones:** Consulta RUC/SUNAT, validación de placas vehiculares y servicios de mapas.

---

## 9. Dominios Excluidos Oficiales y Aprobados (OUT_OF_SCOPE_V1)

### 9.1. Exclusión Oficial del Plan Maestro (OFFICIAL_OUT_OF_SCOPE_V1)
- **Facturación Tributaria Automática (`AUTOMATIC_TAX_BILLING`):** No se emiten facturas ni boletas fiscales de venta electrónicas ante SUNAT desde el sistema T1. Delegada a ERPs/sistemas contables externos. *(Aprobado)*

### 9.2. Exclusiones Aprobadas por el Usuario (APPROVED_OUT_OF_SCOPE_V1)
1. **Pasarelas de Pago (`PAYMENT_GATEWAY_PROCESSING`):** Cobros directos con tarjetas/transferencias bancarias en línea. *(Aprobado por el usuario)*
2. **Contabilidad General Financiera (`FINANCIAL_ACCOUNTING`):** Libros mayores y balances tributarios. *(Aprobado por el usuario)*
3. **Planillas y Recursos Humanos (`PAYROLL_AND_HR`):** Pago de haberes y nóminas. *(Aprobado por el usuario)*
4. **Mantenimiento Mecánico Pesado (`FLEET_HEAVY_MAINTENANCE`):** Talleres mecánicos y mantenimiento de motores pesados. *(Aprobado por el usuario)*

---

## 10. Facturación Tributaria: Verificación de Fronteras
- **Auditoría de Código:** Análisis estático de términos (`invoice`, `factura`, `billing`, `tax`, `comprobante`, `boleta`) en backend y frontend.
- **Hallazgos:**
  - `tax_id_value` / `tax_total`: Campos informativos en socios de negocio y desglose de impuestos en Órdenes de Compra con proveedores (`LOGISTICS_DOCUMENT`).
  - `comprobante`: Referencias en frontend a "Comprobante de Garita" (slip de control de ingreso) y "Comprobante Step-Up" (prueba de autenticación reforzada).
  - `factura.xml`: Fixture de prueba para validación de subida de archivos XML y prevención de ataques XXE en Phase 030 (`REFERENCE_ONLY`).
- **Conclusión:** **0 código de facturación tributaria automática de venta**. La frontera fiscal se encuentra 100% respetada.

---

## 11. Integraciones Externas
- **Consulta RUC / Razón Social:** SUNAT REST API con fallback a web scraping simulado / cache local.
- **Verificación de Placas Vehiculares:** Validación de formato y consulta a fuentes oficiales (SUNARP/MTC).
- **Mapas y Ruteo:** MapLibre GL / OSRM / OpenStreetMap para visualización de recorridos y geocodificación.
- **Seguridad de Credenciales:** Parámetros configurados mediante variables de entorno protegidas (`pydantic-settings`).

---

## 12. Matriz de Responsabilidades y Gobierno (3 Niveles) — APROBADO

| Dominio | Governance Owner (Conceptual) | Current RBAC Mapping (Real) | Human Owner |
| :--- | :--- | :--- | :--- |
| **Compras** | `PURCHASING_OWNER` | `PURCHASING`, `PURCHASING_APPROVER` | `ROLE_TO_BE_ASSIGNED` |
| **Recepción** | `RECEIVING_OWNER` | `GATE_CONTROL`, `RECEIVING`, `QUALITY` | `ROLE_TO_BE_ASSIGNED` |
| **Almacenes** | `WAREHOUSE_OWNER` | `WAREHOUSE_OPERATOR` | `ROLE_TO_BE_ASSIGNED` |
| **Inventario** | `INVENTORY_OWNER` | `INVENTORY_CONTROLLER`, `INVENTORY_OPERATOR`, `INVENTORY_AUDITOR`, `LEDGER_ADMIN` | `ROLE_TO_BE_ASSIGNED` |
| **Trazabilidad** | `TRACEABILITY_OWNER` | `LOGISTICS_AUDITOR`, `QUALITY` *(Apoyo)* | `ROLE_TO_BE_ASSIGNED` |
| **Salida** | `OUTBOUND_OWNER` | `DISPATCH` | `ROLE_TO_BE_ASSIGNED` |
| **Transporte** | `TRANSPORT_OWNER` | `TRANSPORT_PLANNER`, `TRANSPORT_MONITOR` | `ROLE_TO_BE_ASSIGNED` |
| **Entrega** | `DELIVERY_OWNER` | `DRIVER` | `ROLE_TO_BE_ASSIGNED` |
| **Devoluciones** | `RETURNS_OWNER` | `NO_DIRECT_RBAC_EQUIVALENT` *(Apoyo: `QUALITY`, `LOGISTICS_MANAGER`)* | `ROLE_TO_BE_ASSIGNED` |
| **Documentos** | `DOCUMENT_CONTROL_OWNER` | `DOCUMENT_CONTROLLER` | `ROLE_TO_BE_ASSIGNED` |
| **KPIs** | `ANALYTICS_OWNER` | `NO_DIRECT_RBAC_EQUIVALENT` *(Apoyo: `LOGISTICS_MANAGER`, `LOGISTICS_ADMIN`, `LOGISTICS_VIEWER`)* | `ROLE_TO_BE_ASSIGNED` |
| **Integraciones** | `INTEGRATION_OWNER` | `SYSTEM_INTEGRATION_SERVICE`, `LOGISTICS_ADMIN` | `ROLE_TO_BE_ASSIGNED` |
| **Técnico / Release** | `TECHNICAL_OWNER` | `NO_DIRECT_RBAC_EQUIVALENT` *(Gestión de arquitectura e infraestructura)* | `ROLE_TO_BE_ASSIGNED` |
| **Seguridad / CISO** | `SECURITY_OWNER` | `NO_DIRECT_RBAC_EQUIVALENT` *(Políticas transversales de seguridad)* | `ROLE_TO_BE_ASSIGNED` |

> **Nota:** Los Governance Owners son responsabilidades conceptuales de dominio y NO representan roles RBAC implementados en software a menos que coincidan con el catálogo oficial (`backend/app/modules/logistics/rbac/catalog.py`). Los responsables nominales deberán asignarse durante la parametrización organizacional antes de la entrada a producción.

---

## 13. Dependencias Transversales
- **Autenticación y Sesión:** Tokens JWT, rotación, cookies HttpOnly/SameSite.
- **Autenticación Continua & Biometría:** Evaluación multimodal de riesgo y Step-Up.
- **RBAC y Permisos:** Control de acceso por rol y acción sobre endpoints y vistas.
- **Auditoría Inmutable:** Registro unificado de eventos de auditoría (`audit_logs`).
- **Almacenamiento de Archivos:** Bóveda centralizada con hash SHA-256 (`files`).

---

## 14. Módulos Existentes en Línea Base
- Catálogos maestros (Empresa, Almacenes, Productos, Unidades, Socios de Negocio, Vehículos, Conductores).
- Proceso de Compras (Requerimientos, OCs, Evaluaciones, Aprobaciones).
- Proceso de Recepción (Aviso de llegada, Garita, Muelles, Recepción, Diferencias, Calidad).
- Inventario Central (Ledger inmutable, Saldos de Stock, Ubicación Dirigida).
- Motor Documental institucional y repositorio de archivos.

---

## 15. Módulos Parciales
- Trazabilidad avanzada de lotes, series y unidades logísticas (Programada en detalle para F046).
- Flujo de salida integrado: picking por olas, packing y despacho con Step-Up (Programado para Bloque VI, F051-F060).
- Flujo de entrega en ruta con experiencia móvil del conductor y prueba de entrega POD avanzada (Programado para Bloque VIII, F071-F080).
- RMA y gestión avanzada de devoluciones e inspecciones inversas (Programado para Bloque VIII, F075-F080).

---

## 16. Módulos Futuros (Roadmap Oficial)
- Bloque VII: Rutas y mapas en tiempo real (F061-F070).
- Bloque IX: Capa de KPIs avanzados y modelos analíticos (F081-F090).
- Bloque X: Endurecimiento de seguridad, pruebas de carga y despliegue a producción (F091-F100).

---

## 17. Solapamientos Detectados y Reglas de Desacoplamiento
- **Compras vs Recepción:** Compras emite y autoriza la OC; Recepción registra la llegada física y genera el acta de recepción sin modificar precios ni condiciones comerciales de la OC.
- **Recepción vs Inventario:** Recepción concluye con la liquidación de diferencias y liberación de calidad; el ingreso a saldo disponible ocurre mediante evento formal en el `inventory_ledger`.
- **Salida vs Transporte:** Salida emite la Orden de Salida y prepara los bultos; Transporte asigna el vehículo, conductor y ruta para el traslado físico.
- **Documentos vs Dominios de Negocio:** El motor documental es un servicio transversal de renderizado y archivo; no almacena lógica de negocio sobre estados de inventario o autorizaciones comerciales.

---

## 18. Riesgos de Scope Creep Mitigados
- **Riesgo:** Confundir exclusiones oficiales con propuestas del análisis.
  - **Mitigación:** Separación explícita de `OFFICIAL_OUT_OF_SCOPE_V1` (`AUTOMATIC_TAX_BILLING`) y `APPROVED_OUT_OF_SCOPE_V1` ratificadas por el usuario.
- **Riesgo:** Confundir Governance Owners conceptuales con roles RBAC de software.
  - **Mitigación:** Implementación del modelo en tres niveles (Governance Owner, Current RBAC Mapping, Human Owner).
- **Riesgo:** Refactorizar prematuramente módulos en F002.
  - **Mitigación:** F002 es 100% de gobernanza y definición de alcance (`PRODUCTION_CODE_CHANGES = NONE`). El diseño arquitectónico modular corresponde a F003.

---

## 19. Evidencia Técnica
- `docs/retro-audit/phase-002/scope-matrix.md`: Matriz de los 12 dominios con sus módulos, tablas, rutas, governance owners y mapeo RBAC.
- `docs/retro-audit/phase-002/in-scope.md`: Detalle de inclusiones funcionales del primer lanzamiento.
- `docs/retro-audit/phase-002/out-of-scope.md`: Detalle de exclusiones oficiales y aprobadas.
- `docs/retro-audit/phase-002/responsibility-matrix.md`: Asignación de gobernanza en tres niveles.
- `docs/retro-audit/phase-002/current-module-map.md`: Mapeo granular de componentes existentes.

---

## 20. Tests y CI Aplicables
- **Verificación de Integridad Documental:** Comprobación programática de la matriz de 12 dominios, inclusiones, exclusiones oficiales/aprobadas y responsabilidades.
- **Git Scope Gate:** `git diff --name-only` estrictamente contenido en `docs/retro-audit/**`.
- **CI Pipeline Oficial:** Ejecución y validación remota en GitHub Actions sobre el commit exacto.

---

## 21. Hallazgos
- `INFO-001`: La delimitación de los 12 dominios concuerda al 100% con el Plan Maestro en 100 Fases.
- `INFO-002`: No existe código invasivo de facturación tributaria automática en la base de código auditada.
- `INFO-003`: El catálogo RBAC real contiene 20 roles del sistema que se mapean formalmente contra los 12 Governance Owners.

---

## 22. Correcciones Realizadas
- Registro formal de las decisiones de alcance aprobadas por el usuario (`SCOPE_ACCEPTANCE: PASS`).
- Ratificación de `IN_SCOPE_V1`, `OFFICIAL_OUT_OF_SCOPE_V1` y `APPROVED_OUT_OF_SCOPE_V1`.
- Actualización de estados maestros en `docs/retro-audit/README.md`.

---

## 23. Aceptación por el Usuario
- **Prueba UAT de Navegador:** `N/A` (Fase de gobierno documental sin cambios en UI).
- **Revisión de Alcance:** `SCOPE_ACCEPTANCE: PASS` (Aprobado explícitamente por el usuario).

---

## 24. Estado Final de la Fase 002
```
PHASE_002_APPROVED_FOR_MERGE
SCOPE_ACCEPTANCE: PASS
```
