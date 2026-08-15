# F003 · Plan de Aceptación en Navegador (Browser Architecture Review)

## 1. Entorno de Ejecución

- **Frontend URL:** `http://localhost:5173`
- **Backend URL:** `http://localhost:8000`
- **Swagger / OpenAPI UI:** `http://localhost:8000/docs`
- **Backend Candidate SHA:** `CANDIDATE_HEAD_SHA` *(Coincidente con el HEAD de PR #8)*
- **Frontend Candidate SHA:** `699cbfbfc86a7378bac2a4d28fdc3f7285a13564`
- **Database:** PostgreSQL `postgres` (Esquema `public`, 339 tablas base)
- **Tipo de Evaluación:** `BROWSER_ARCHITECTURE_REVIEW` (Auditoría de Arquitectura Modular, Navegabilidad y Superficies)

---

## 2. Protocolo de Pruebas en Navegador

### TEST 01 · HEALTH CHECK DEL DOMINIO MODULAR

- **URL:** `http://localhost:8000/api/logistics/health`
- **Método:** `GET`
- **Pasos:**
  1. Abrir en el navegador la URL del endpoint de diagnóstico.
  2. Verificar la respuesta JSON oficial del módulo.
- **Resultado Esperado:** HTTP 200 con payload `{ "status": "ok", "domain": "logistics", "version": "phase-045" }`.
- **Network:** Status 200 OK.
- **Console:** Sin errores.

---

### TEST 02 · SWAGGER / OPENAPI SPECIFICATION

- **URL:** `http://localhost:8000/docs`
- **Método:** `GET`
- **Pasos:**
  1. Acceder a la interfaz interactiva de Swagger UI.
  2. Comprobar que el tag `logistics` y los submódulos están debidamente agrupados bajo el prefijo `/api/logistics/*`.
  3. Verificar que la especificación OpenAPI carga sin advertencias de parseo.
- **Resultado Esperado:** Carga interactiva y fluida de Swagger UI.
- **Network:** `GET /openapi.json` con HTTP 200 OK.
- **Console:** Sin errores de serialización.

---

### TEST 03 · AUTENTICACIÓN Y CONTEXTO DE SESIÓN

- **URL:** `http://localhost:5173/login`
- **Pasos:**
  1. Iniciar sesión con el usuario operador / administrador.
  2. Verificar redirección al área autenticada (`/dashboard`).
  3. Presionar `F5` para validar la persistencia de la cookie de sesión HTTP-only `access_token` y el contexto de seguridad.
- **Resultado Esperado:** Sesión activa y reconocida sin redirecciones en bucle hacia `/login`.
- **Network:** `GET /api/auth/me` con HTTP 200 OK.
- **Console:** Limpia de excepciones.

---

### TEST 04 · NAVEGACIÓN Y DISPONIBILIDAD DE MÓDULOS

- **URL:** `http://localhost:5173`
- **Pasos:**
  1. Navegar a través de la barra lateral (Sidebar) por las vistas de los dominios logísticos:
     - `/logistics/organizations` (Organizaciones y Sedes)
     - `/logistics/warehouses` (Almacenes y Ubicaciones)
     - `/logistics/catalog/products` (Catálogo de Productos)
     - `/logistics/catalog/units` (Unidades y Conversiones)
     - `/logistics/purchasing/requisitions` (Requisiciones de Compra)
     - `/logistics/purchasing/orders` (Órdenes de Compra)
     - `/logistics/inbound/docks` (Muelles de Recepción)
     - `/logistics/inventory/balances` (Saldos de Inventario)
     - `/logistics/inventory/ledger` (Kárdex y Movimientos)
     - `/logistics/vehicles` (Flota Vehicular)
     - `/logistics/drivers` (Conductores)
     - `/logistics/files` (Repositorio de Archivos)
     - `/logistics/audit-events` (Auditoría de Eventos)
     - `/logistics/permissions` (Catálogo de Permisos)
- **Resultado Esperado:** Cada página carga correctamente su vista base sin pantallas en blanco ni `AppErrorBoundary`.
- **Network:** Sin peticiones 404 ni 500 inesperadas.
- **Console:** Sin errores no controlados.

---

### TEST 05 · LOGISTICS PRINCIPAL Y PERMISOS RBAC

- **URL:** `http://localhost:5173/logistics/permissions`
- **Pasos:**
  1. Abrir la página del catálogo de permisos.
  2. Verificar la consulta al endpoint `/api/logistics/me` y la carga de roles del operador.
- **Resultado Esperado:** Listado de permisos categorizados por dominio logístico.
- **Network:** `GET /api/logistics/me` y `GET /api/logistics/rbac/permissions` con HTTP 200 OK.
- **Console:** Sin errores.

---

### TEST 06 · VALIDACIÓN DE RED Y CONSOLA (F12)

- **Pasos:**
  1. Mantener abierta la pestaña `Network` de DevTools (F12).
  2. Verificar que las peticiones a endpoints mutantes autenticados utilizan el flujo de seguridad estándar (CSRF / Step-Up si aplica).
  3. Revisar la pestaña `Console` para descartar `Unhandled TypeError`, `ReferenceError` o fallos de renderizado React.
- **Resultado Esperado:** Peticiones HTTP conformes a la arquitectura, ausencia de errores bloqueantes en consola.

---

## 3. Registro de Resultados del Usuario

| Caso de Prueba | Resultado Esperado | Resultado Usuario | Comentarios / Observaciones |
| :--- | :--- | :---: | :--- |
| **TEST 01 · Health Check** | Status ok, domain logistics, version phase-045 | `[ PASS / FAIL ]` | |
| **TEST 02 · Swagger / OpenAPI** | Carga fluida y tags /api/logistics agrupados | `[ PASS / FAIL ]` | |
| **TEST 03 · Autenticación / F5** | Sesión persistente y cookie reconocida | `[ PASS / FAIL ]` | |
| **TEST 04 · Navegación Modular** | Carga de las 14 rutas principales | `[ PASS / FAIL ]` | |
| **TEST 05 · Permisos RBAC** | Consulta exitosa a `/logistics/me` | `[ PASS / FAIL ]` | |
| **TEST 06 · Consola y Red** | 0 errores 500, 0 caídas de React | `[ PASS / FAIL ]` | |

---

## 4. Dictamen de Aceptación Arquitectónica

```
BROWSER_ARCHITECTURE_REVIEW: [ PASS / FAIL ]
ARCHITECTURE_ACCEPTANCE:    [ PASS / FAIL ]
USER_ACCEPTANCE:            [ PASS / FAIL ]
```
