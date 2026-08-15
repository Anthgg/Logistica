# F003 · Plan de Aceptación en Navegador · Retest Ronda 2 (Browser Architecture Review)

## 1. Entorno de Ejecución

- **Frontend URL:** `http://localhost:5173`
- **Backend URL:** `http://localhost:8000`
- **Swagger / OpenAPI UI:** `http://localhost:8000/docs`
- **Backend Candidate SHA:** `CANDIDATE_HEAD_SHA` *(Coincidente con el HEAD de PR #8)*
- **Frontend Candidate SHA:** `699cbfbfc86a7378bac2a4d28fdc3f7285a13564`
- **Database:** PostgreSQL `postgres` (Esquema `public`, 339 tablas base)
- **Tipo de Evaluación:** `BROWSER_ARCHITECTURE_REVIEW` (Auditoría de Arquitectura Modular, Navegabilidad y Superficies Reales)

---

## 2. Protocolo de Pruebas en Navegador (Rutas Reales Verificadas)

### TEST 01 · HEALTH CHECK DEL DOMINIO MODULAR

- **URL:** `http://localhost:8000/api/logistics/health`
- **Método:** `GET`
- **Pasos:**
  1. Abrir en el navegador la URL del endpoint.
  2. Verificar la respuesta JSON oficial del runtime logístico.
- **Resultado Esperado:** HTTP 200 con payload `{ "status": "ok", "domain": "logistics", "version": "phase-003" }`.
- **Network:** Status 200 OK.
- **Console:** Sin errores.

---

### TEST 02 · SWAGGER / OPENAPI SPECIFICATION

- **URL:** `http://localhost:8000/docs`
- **Método:** `GET`
- **Pasos:**
  1. Acceder a Swagger UI.
  2. Verificar que los tags del dominio logístico `/api/logistics/*` están agrupados y documentados.
- **Resultado Esperado:** Carga interactiva y fluida de Swagger UI sin errores en `GET /openapi.json`.
- **Network:** `GET /openapi.json` con HTTP 200 OK.
- **Console:** Sin errores de serialización.

---

### TEST 03 · AUTENTICACIÓN Y CONTEXTO DE SESIÓN

- **URL:** `http://localhost:5173/login`
- **Pasos:**
  1. Iniciar sesión con el usuario operador / administrador.
  2. Verificar redirección al área autenticada (`/dashboard`).
  3. Presionar `F5` para validar la persistencia de la cookie de sesión HTTP-only `access_token` y el contexto de seguridad.
- **Resultado Esperado:** Sesión activa y persistente tras recarga.
- **Network:** `GET /api/auth/me` con HTTP 200 OK.
- **Console:** Limpia de excepciones.

---

### TEST 04 · NAVEGACIÓN MODULAR POR RUTAS REALES (APP ROUTER)

- **URL Base:** `http://localhost:5173`
- **Pasos:**
  1. Navegar por las rutas reales registradas en `AppRouter.tsx`:
     - `/logistics/warehouses` (Almacenes y Sedes)
     - `/logistics/products` (Catálogo de Productos - Ruta Real)
     - `/logistics/units` (Unidades y Conversiones - Ruta Real)
     - `/logistics/catalog/cost-centers` (Centros de Costo - Ruta Real)
     - `/logistics/purchasing/requisitions` (Requisiciones de Compra)
     - `/logistics/purchasing/purchase-orders` (Órdenes de Compra - Ruta Real)
     - `/logistics/inbound/docks` (Muelles de Recepción)
     - `/logistics/inventory/ledger` (Kárdex y Movimientos)
     - `/logistics/inventory/stock` (Saldos de Stock - Ruta Real)
     - `/logistics/vehicles` (Flota Vehicular)
     - `/logistics/drivers` (Conductores)
     - `/logistics/files` (Repositorio de Archivos)
     - `/logistics/audit-events` (Eventos de Auditoría - Hotfix 500 Aplicado)
     - `/logistics/permissions` (Catálogo de Permisos)
- **Resultado Esperado:** Las 14 rutas cargan sus vistas base sin pantallas en blanco (`White Screen`), sin errores 404 ni caídas de React.
- **Network:** Sin peticiones 404 ni 500 no controladas.
- **Console:** Sin excepciones no capturadas.

---

### TEST 05 · LOGISTICS PRINCIPAL Y PERMISOS RBAC

- **URL:** `http://localhost:5173/logistics/permissions`
- **Pasos:**
  1. Abrir la página del catálogo de permisos.
  2. Verificar la consulta al endpoint `/api/logistics/me` y el renderizado de permisos activos.
- **Resultado Esperado:** Tabla de permisos cargada vía API sin errores.
- **Network:** `GET /api/logistics/me` y `GET /api/logistics/rbac/permissions` con HTTP 200 OK.
- **Console:** Sin errores.

---

### TEST 06 · VALIDACIÓN DE RED Y CONSOLA (F12) TRAS HOTFIX DE AUDITORÍA

- **Pasos:**
  1. Abrir `/logistics/audit-events` con la consola DevTools (F12) abierta.
  2. Verificar que `GET /api/logistics/audit-events?page=1&page_size=20` responde HTTP 200 OK (sin error 500).
- **Resultado Esperado:** Petición HTTP 200 OK y tabla de eventos renderizada.
- **Network:** 0 errores 500.
- **Console:** 0 errores bloqueantes.

---

## 3. Registro de Resultados del Retest (Ronda 2)

| Caso de Prueba | Resultado Esperado | Resultado Usuario | Comentarios / Observaciones |
| :--- | :--- | :---: | :--- |
| **TEST 01 · Health Check** | Status ok, domain logistics, version phase-003 | `[ PASS / FAIL ]` | |
| **TEST 02 · Swagger / OpenAPI** | Carga fluida y tags agrupados | `[ PASS / FAIL ]` | |
| **TEST 03 · Autenticación / F5** | Sesión persistente y cookie reconocida | `[ PASS / FAIL ]` | |
| **TEST 04 · Navegación Modular (14 Rutas Reales)** | 0 errores 404 en las 14 rutas auditadas | `[ PASS / FAIL ]` | |
| **TEST 05 · Permisos RBAC** | Consulta exitosa a `/logistics/me` | `[ PASS / FAIL ]` | |
| **TEST 06 · Eventos Auditoría (Hotfix 500)** | Status 200 OK en `/api/logistics/audit-events` | `[ PASS / FAIL ]` | |

---

## 4. Dictamen de Aceptación Arquitectónica

```
BROWSER_ARCHITECTURE_REVIEW: [ PASS / FAIL ]
ARCHITECTURE_ACCEPTANCE:    [ PASS / FAIL ]
USER_ACCEPTANCE:            [ PASS / FAIL ]
```
