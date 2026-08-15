# Retro-Auditoría · Fase 002: Definir el Alcance Logístico

---

## 1. Objetivo Oficial
El objetivo de la **Fase 002** es definir, delimitar y formalizar el alcance funcional del **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales**, estableciendo con precisión las fronteras operativas entre los 12 dominios logísticos, identificando las inclusiones del primer lanzamiento (`IN_SCOPE_V1`), las exclusiones obligatorias (`OUT_OF_SCOPE_V1`) y asignando los roles responsables de cada área.

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
- Exclusión explícita de la facturación tributaria automática para el primer lanzamiento.
- Establecimiento de la matriz de responsabilidades por rol funcional y técnico.

---

## 3. Criterio de Cierre
- Documento de alcance formalizado que contenga la matriz de 12 dominios, inclusiones oficiales, exclusiones oficiales y matriz de responsabilidades por rol.
- Verificación en código de que no existe invasión de alcance por facturación tributaria automática ni pasarelas de cobro no autorizadas.
- Aprobación conceptual por parte del usuario (`SCOPE_ACCEPTANCE: PENDING_USER_REVIEW`).

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

## 8. Dominios Incluidos (IN_SCOPE_V1)
1. **Compras:** Requerimientos, cotizaciones, evaluación de proveedores, OCs y aprobaciones.
2. **Recepción:** Avisos de llegada, garita, muelles, recepción física, diferencias y control de calidad/cuarentena.
3. **Almacenes:** Modelado de almacenes, zonificación, ubicaciones jerárquicas y putaway.
4. **Inventario:** Ledger inmutable, cálculo de saldos disponibles/reservados/bloqueados, conteos y transferencias.
5. **Trazabilidad:** Auditoría inmutable de eventos, lotes/series y ciclo de vida documental.
6. **Salida:** Pedidos de salida, reserva de existencias, picking, packing y autorización de despacho.
7. **Transporte:** Vehículos, conductores, verificación de placas/licencias y rutas de transporte.
8. **Entrega:** Despacho, prueba de entrega (POD), firmas digitales y gestión de rechazos.
9. **Devoluciones:** Logística inversa, solicitudes RMA, inspección de devolución e incidencias.
10. **Documentos:** Series, talonarios, plantillas, PDF/impresión, anulación y archivo con SHA-256.
11. **KPIs:** Dashboards operativos, métricas OTIF, rotación y reportes gerenciales.
12. **Integraciones:** Consulta RUC/SUNAT, validación de placas vehiculares y servicios de mapas.

---

## 9. Dominios Excluidos (OUT_OF_SCOPE_V1)
1. **Facturación Tributaria Automática (`AUTOMATIC_TAX_BILLING`):** No se emiten facturas ni boletas fiscales de venta electrónicas ante SUNAT.
2. **Pasarelas de Pago (`PAYMENT_GATEWAY_PROCESSING`):** No se procesan pagos directos con tarjeta de crédito/débito.
3. **Contabilidad General (`FINANCIAL_ACCOUNTING`):** No se generan libros mayores ni balances financieros impositivos.
4. **Planillas y Nómina (`PAYROLL_AND_HR`):** No se gestionan pagos salariales ni beneficios laborales.
5. **Mantenimiento Pesado de Motores (`FLEET_HEAVY_MAINTENANCE`):** No se administran talleres mecánicos ni órdenes de reparación compleja.

---

## 10. Facturación Tributaria: Verificación de Fronteras
- **Auditoría de Código:** Se ejecutó un análisis estático exhaustivo de términos (`invoice`, `factura`, `billing`, `tax`, `comprobante`, `boleta`) en backend y frontend.
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

## 12. Matriz de Responsabilidades
- **Compras:** `PURCHASING_OWNER`
- **Recepción:** `RECEIVING_OWNER`
- **Almacenes:** `WAREHOUSE_OWNER`
- **Inventario:** `INVENTORY_OWNER`
- **Trazabilidad:** `TRACEABILITY_OWNER`
- **Salida:** `OUTBOUND_OWNER`
- **Transporte:** `TRANSPORT_OWNER`
- **Entrega:** `DELIVERY_OWNER`
- **Devoluciones:** `RETURNS_OWNER`
- **Documentos:** `DOCUMENT_CONTROL_OWNER`
- **KPIs:** `ANALYTICS_OWNER`
- **Integraciones:** `INTEGRATION_OWNER`
- **Técnico / Arquitectura:** `TECHNICAL_OWNER`
- **Seguridad / Autenticación:** `SECURITY_OWNER`

---

## 13. Dependencias Transversales
Las siguientes capacidades operan como servicios compartidos y de infraestructura:
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
- **Riesgo:** Intentar incorporar emisión de facturas electrónicas a SUNAT en este sistema.
  - **Mitigación:** Exclusión formalizada en `OUT_OF_SCOPE_V1`; emisión delegada a ERPs contables.
- **Riesgo:** Confundir Guías de Remisión (GRE) con Comprobantes de Pago tributarios.
  - **Mitigación:** Definición explícita de GRE como documento de transporte logístico.
- **Riesgo:** Refactorizar prematuramente módulos en F002.
  - **Mitigación:** F002 es 100% de gobernanza y definición de alcance (`PRODUCTION_CODE_CHANGES = NONE`). El diseño arquitectónico modular corresponde a F003.

---

## 19. Evidencia Técnica
- `docs/retro-audit/phase-002/scope-matrix.md`: Matriz de los 12 dominios con sus módulos, tablas, rutas y responsables.
- `docs/retro-audit/phase-002/in-scope.md`: Detalle de inclusiones funcionales del primer lanzamiento.
- `docs/retro-audit/phase-002/out-of-scope.md`: Detalle de exclusiones oficiales.
- `docs/retro-audit/phase-002/responsibility-matrix.md`: Asignación de gobernanza por rol funcional y técnico.
- `docs/retro-audit/phase-002/current-module-map.md`: Mapeo granular de componentes existentes.

---

## 20. Tests y CI Aplicables
- **Verificación de Integridad Documental:** Comprobación programática de la matriz de 12 dominios, inclusiones, exclusiones y responsabilidades.
- **Git Scope Gate:** `git diff --name-only` estrictamente contenido en `docs/retro-audit/**`.
- **CI Pipeline Oficial:** Ejecución y validación remota en GitHub Actions sobre el commit exacto.

---

## 21. Hallazgos
- `INFO-001`: La delimitación de los 12 dominios es coherente con el Plan Maestro en 100 Fases.
- `INFO-002`: No existe código invasivo de facturación tributaria automática en la base de código auditada.
- `INFO-003`: Los módulos documentales operan adecuadamente como servicios transversales de soporte.

---

## 22. Correcciones Realizadas
- Generación del paquete completo de gobernanza y alcance para la Fase 002.
- Actualización de estados maestros en `docs/retro-audit/README.md` (F001: `PASSED`, F002: `IN_PROGRESS`).

---

## 23. Aceptación por el Usuario
- **Prueba UAT de Navegador:** `N/A` (Fase de gobierno/documental sin cambios en UI).
- **Revisión de Alcance:** `SCOPE_ACCEPTANCE: PENDING_USER_REVIEW`.

---

## 24. Estado Final de la Fase 002
```
PHASE_002_READY_FOR_USER_ACCEPTANCE
SCOPE_ACCEPTANCE: PENDING_USER_REVIEW
F003: BLOCKED
```
