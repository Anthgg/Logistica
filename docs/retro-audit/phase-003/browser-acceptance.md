# F003 · Plan de Aceptación en Navegador · Protocolo de Retest Ronda 3

## 1. Entorno de Ejecución

- **Frontend URL:** `http://localhost:5173`
- **Backend URL:** `http://localhost:8000`
- **Swagger / OpenAPI UI:** `http://localhost:8000/docs`
- **Backend Runtime Mount:** `backend/app` (direct worktree mount)
- **Frontend Candidate SHA:** `699cbfbfc86a7378bac2a4d28fdc3f7285a13564`
- **Database:** PostgreSQL `postgres` (Esquema `public`)
- **Tipo de Evaluación:** `FOCUSED_RETEST_ROUND_3`

---

## 2. Contexto de Ronda 3

En la Ronda 2, todas las superficies de navegación modular fueron validadas satisfactoriamente (`PASS`). El único fallo reportado fue el retorno de HTTP 500 en `/logistics/audit-events`, originado por una desalineación de runtime (`STALE_RUNTIME`), la cual fue resuelta y verificada.

Por tanto, **la Ronda 3 se enfoca exclusivamente en la confirmación del endpoint corregido y la consola del navegador**, sin requerir la repetición de las 14 pantallas previas.

---

## 3. Casos de Prueba Focalizados (Ronda 3)

### TEST 01 · EVENTOS DE AUDITORÍA (HOTFIX & RUNTIME VERIFIED)

- **URL:** `http://localhost:5173/logistics/audit-events`
- **Pasos:**
  1. Con sesión activa (`usuario@example.com` / `Admin123!`), abrir la vista de eventos de auditoría.
  2. Verificar que la tabla renderiza los eventos de auditoría registrados.
  3. Comprobar en DevTools (F12) Network que la petición `GET /api/logistics/audit-events?page=1&page_size=20` responde `HTTP 200 OK`.
- **Resultado Esperado:** Tabla de eventos visible con paginación, 0 errores 500.
- **Network:** Status 200 OK.
- **Console:** Sin errores no capturados.

---

### TEST 02 · CATÁLOGO DE PERMISOS (PERMISSIONS CATALOG)

- **URL:** `http://localhost:5173/logistics/permissions`
- **Pasos:**
  1. Navegar a la página del catálogo de permisos.
  2. Verificar que la tabla carga los permisos asignados desde `/api/logistics/me`.
- **Resultado Esperado:** Tabla de permisos cargada vía API sin errores.
- **Network:** `GET /api/logistics/me` y `GET /api/logistics/rbac/permissions` con HTTP 200 OK.
- **Console:** Sin errores.

---

### TEST 03 · CONSOLA DEVTOOLS (F12 CONSOLE AUDIT)

- **Pasos:**
  1. Revisar los logs en la pestaña Consola de DevTools.
  2. Confirmar que no existen excepciones de React (`Uncaught Error`, `React Crash`, `AppErrorBoundary`).
- **Resultado Esperado:** 0 errores bloqueantes. *(Avisos de React DevTools o Permissions-Policy unload son informativos y no bloqueantes).*

---

### TEST 04 · RED DEVTOOLS (F12 NETWORK AUDIT)

- **Pasos:**
  1. Revisar la pestaña Red (Network) de DevTools.
  2. Confirmar que todas las peticiones a la API responden con códigos de éxito (200 / 201) y no hay respuestas 500 no controladas.
- **Resultado Esperado:** 0 respuestas HTTP 500 inesperadas.

---

## 4. Registro de Resultados del Retest (Ronda 3)

| Caso de Prueba | Resultado Esperado | Resultado Usuario | Comentarios / Observaciones |
| :--- | :--- | :---: | :--- |
| **TEST 01 · Audit Events** | HTTP 200 OK y tabla de eventos renderizada | `[ PASS / FAIL ]` | |
| **TEST 02 · Permissions** | HTTP 200 OK y permisos cargados | `[ PASS / FAIL ]` | |
| **TEST 03 · Consola F12** | 0 excepciones de React / AppErrorBoundary | `[ PASS / FAIL ]` | |
| **TEST 04 · Red F12** | 0 peticiones 500 no controladas | `[ PASS / FAIL ]` | |

---

## 5. Dictamen de Aceptación

```
BROWSER_ARCHITECTURE_REVIEW: [ PASS / FAIL ]
ARCHITECTURE_ACCEPTANCE:    [ PASS / FAIL ]
USER_ACCEPTANCE:            [ PASS / FAIL ]
```
