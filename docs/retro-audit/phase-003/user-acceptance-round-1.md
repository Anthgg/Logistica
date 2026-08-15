# Registro de Aceptación de Usuario · Ronda 1 · Fase 003

## 1. Resumen Ejecutivo

- **Fase Auditada:** F003 · Diseñar la arquitectura modular
- **Ronda de Evaluación:** Ronda 1 (User Browser Acceptance)
- **Dictamen del Usuario Humano:** `USER_ACCEPTANCE = FAIL`
- **Estado Oficial Resultante:** `PHASE_003_REQUIRES_USER_ACCEPTANCE_FIXES`
- **Merge a Main:** `NOT AUTHORIZED`
- **Fase 004:** `BLOCKED`

---

## 2. Evidencia Real Registrada por Superficie

### 2.1. Health Check del Dominio Modular
- **URL:** `http://localhost:8000/api/logistics/health`
- **Resultado:** `PASS`
- **Payload Real Obtenido:**
  ```json
  {
    "status": "ok",
    "domain": "logistics",
    "version": "phase-003"
  }
  ```

---

### 2.2. Almacenes (`/logistics/warehouses`)
- **Resultado:** `PARTIAL` (Carga la vista, pero no existe botón/acción de creación de almacén).
- **Diagnóstico:** La página lista almacenes y permite ver detalle, pero carece de formulario de alta interactiva para operadores.
- **Fase Propietaria (Owner):** **F004 (Definir organización, sedes y almacenes)**.

---

### 2.3. Catálogo de Productos
- **Ruta Probada:** `/logistics/catalog/products`
- **Resultado:** `HTTP 404 (Not Found)`
- **Causa Raíz:** Error en la documentación previa de rutas. La ruta real declarada en `AppRouter.tsx` es `/logistics/products`.
- **Fase Propietaria (Owner):** **F023 (Crear el catálogo de productos)**.

---

### 2.4. Unidades y Conversiones
- **Ruta Probada:** `/logistics/catalog/units`
- **Resultado:** `HTTP 404 (Not Found)`
- **Causa Raíz:** Error en la documentación previa de rutas. La ruta real declarada en `AppRouter.tsx` es `/logistics/units`.
- **Fase Propietaria (Owner):** **F024 (Implementar unidades y conversiones)**.

---

### 2.5. Órdenes de Compra
- **Ruta Probada:** `/logistics/purchasing/orders`
- **Resultado:** `HTTP 404 (Not Found)`
- **Causa Raíz:** Error en la documentación previa de rutas. La ruta real declarada en `AppRouter.tsx` es `/logistics/purchasing/purchase-orders` (o `/logistics/purchase-orders`).
- **Fase Propietaria (Owner):** **F034 (Implementar órdenes de compra)**.

---

### 2.6. Saldos de Stock e Inventario
- **Ruta Probada:** `/logistics/inventory/balances`
- **Resultado:** `HTTP 404 (Not Found)`
- **Causa Raíz:** Error en la documentación previa de rutas. La ruta real declarada en `AppRouter.tsx` es `/logistics/inventory/stock` (con submódulos `/products`, `/warehouses`, `/list`, etc.).
- **Fase Propietaria (Owner):** **F045 (Calcular saldos de stock)**.
- **Nota:** La ruta de Kárdex y Movimientos `/logistics/inventory/ledger` cargó exitosamente (`PASS`).

---

### 2.7. Muelles de Recepción (`/logistics/inbound/docks`)
- **Resultado:** `PAGE_LOAD = PASS`
- **Diagnóstico:** Superficie navegable operativa en carga inicial. La validación funcional profunda corresponde a su fase propietaria.

---

### 2.8. Flota Vehicular (`/logistics/vehicles`)
- **Resultado:** `PARTIAL`
- **Diagnóstico:**
  - El usuario puede crear marcas (`/logistics/vehicle-makes`) y modelos (`/logistics/vehicle-models`), pero no se visualizan de forma útil ni integrada en la vista principal.
  - La opción de registrar vehículo está condicionada a permisos avanzados (`vehicles.manage`), dejando la vista en modo solo lectura para roles estándar.
- **Fase Propietaria (Owner):** **F027 (Crear el maestro de vehículos)** / **F028 (Implementar verificaciones de placa)**.

---

### 2.9. Conductores (`/logistics/drivers`)
- **Resultado:** `PARTIAL`
- **Diagnóstico:** La vista actual opera esencialmente como consulta de solo lectura; carece de creación, edición, baja/desactivación y gestión interactiva de licencias y alertas en el flujo principal.
- **Fase Propietaria (Owner):** **F029 (Crear el maestro de conductores)**.

---

### 2.10. Custodia de Archivos y Evidencias (`/logistics/files`)
- **Resultado:** `PARTIAL` (Problema crítico de UX / Contrato Humano).
- **Diagnóstico:** El asistente de carga (`/logistics/files/upload`) exige ingresar manualmente campos técnicos (`resource_type` y UUID de `resource_id`), violando la regla de interfaces humanas.
- **Fase Propietaria (Owner):** **F030 (Centralizar archivos y evidencias)**.

---

### 2.11. Eventos de Auditoría (`/logistics/audit-events`)
- **Resultado:** `HTTP 500 (Internal Server Error)`
- **Diagnóstico Forense:**
  - **Excepción:** `TypeError: AuditService.list() got an unexpected keyword argument 'category'`
  - **Archivo y Línea:** `backend/app/modules/logistics/audit/api/router.py`, línea 42.
  - **Causa Raíz:** Desalineación de firma: el router pasaba `category`, `organization_id`, `branch_id`, `warehouse_id`, mientras que `AuditService.list()` solo declaraba `event_category` y omitía los filtros organizacionales.
  - **Acción:** Corregido en backend (`service.py`) con alias `category` y soporte de filtros organizacionales + test unitario de regresión.
- **Fase Propietaria (Owner):** **F007 (Unificar eventos de auditoría)**.

---

### 2.12. Catálogo de Permisos (`/logistics/permissions`)
- **Resultado:** `PARTIAL`
- **Diagnóstico:** Los permisos cargan correctamente vía API, pero la tabla expone códigos internos crudos (`logistics.documents.read`) sin etiquetas de negocio legibles para humanos y sin capacidades de gestión/asignación.
- **Fases Propietarias (Owner):** **F005 (Definir roles logísticos)** y **F006 (Definir permisos por acción)**.

---

### 2.13. Pre-requisitos de Compras y Centros de Costo
- **Diagnóstico:** El flujo de requisiciones (`/logistics/purchasing/requisitions`) requiere datos maestros previos (Centro de Costo, Sede, Proveedor). La interfaz de Centros de Costo existe en `/logistics/catalog/cost-centers`, pero la ausencia de un dataset semilla controlado impidió completar el flujo UAT.
- **Estrategia Requerida:** Diseño de estrategia formal de datos demo (`UAT Demo Data Strategy`).

---

## 3. Dictamen Final de la Ronda 1

```
USER_ACCEPTANCE: FAIL
MOTIVO: Brechas funcionales detectadas en navegador, rutas 404 por desalineación documental, fallo 500 en auditoría y fricciones de UX con IDs técnicos.
ACCIONES: Corrección de documentación, corrección técnica del endpoint de auditoría, registro de gaps vinculantes con owner canónico y preparación de retest.
```
