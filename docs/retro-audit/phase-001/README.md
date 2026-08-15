# Retro-Auditoría · Fase 001: Congelar la Línea Base del Proyecto

---

## 1. Objetivo de la Fase 001 y Declaración de Congelamiento de Línea Base
El objetivo primordial de la **Fase 001** es auditar exhaustivamente, verificar en tiempo de ejecución, corregir defectos fundacionales y congelar de manera inmutable la línea base del sistema logístico con autenticación continua. Esta fase establece la infraestructura de pruebas, contratos de seguridad, modelos de persistencia y canales de comunicación entre el frontend (React 19) y el backend (FastAPI), garantizando que las fases subsiguientes (F002 a F100 del Plan Maestro) se construyan sobre cimientos estables y verificados.

---

## 2. SHAs de Git Oficiales Auditados y Release Gate
- **Repositorio Backend:** `https://github.com/Anthgg/Logistica.git`
  - **Rama Base:** `origin/main`
  - **Commit SHA Base:** `d55e7f2b64ea6d8ce278fb626046c12d3dab1286`
  - **Rama de Auditoría:** `audit/retro-phase-001-backend`
  - **Snapshot de Implementación de Auditoría:** `101b5b783651e73bf7ffd01ff15dfebef431cd2c`
  - **HEAD Final de Rama & CI:** Gestionados y rastreados en tiempo real en la metadata del PR y GitHub Actions.
  - **Pull Request:** [#5](https://github.com/Anthgg/Logistica/pull/5)
- **Repositorio Frontend:** `https://github.com/Anthgg/LogisticaF.git`
  - **Rama Base:** `origin/main`
  - **Commit SHA Base:** `699cbfbfc86a7378bac2a4d28fdc3f7285a13564`
  - **Rama de Auditoría:** `N/A`
  - **Pull Request:** `N/A`
  - **Cambios Requeridos en Frontend:** `NONE` (Suite local 100% verde sobre el baseline).

---

## 3. Topología de Infraestructura y Servicios Verificados en Runtime
- **Contenedor Backend:** `continuous-authentication-backend-1` (FastAPI 0.115.6 / Uvicorn / Python 3.11.15)
  - **Puerto Host/Contenedor:** `8000:8000`
  - **Estado:** Running & Healthy
- **Contenedor Base de Datos:** `continuous-authentication-postgres-1` (PostgreSQL 16.4 Alpine)
  - **Puerto Host/Contenedor:** `5432:5432`
  - **Base de Datos:** `continuous_authentication`
  - **Estado:** Running & Healthy
- **Frontend SPA:** Node.js / Vite Dev Server en `http://localhost:5173`

---

## 4. Resumen Ejecutivo del Estado del Backend (FastAPI, Python, Uvicorn)
- **Arquitectura:** Modular por dominios bajo `app/modules/logistics/*`, `app/api/routes/*`, `app/services/*`.
- **Inyección de Dependencias:** FastAPI `Depends` para base de datos (`get_db`), autenticación (`get_current_session`), CSRF (`verify_csrf`) y RBAC.
- **Manejo de Ciclo de Vida:** FastAPI Lifespan para precarga controlada de modelos de inferencia y registro de servicios.
- **Middleware Stack:** Logging con inyección de `X-Request-ID`, manejo de excepciones centralizado, resolución de localización `Accept-Language` y CORS restrictivo.

---

## 5. Resumen Ejecutivo del Estado del Frontend (React, TypeScript, Vite)
- **Framework:** React 19 SPA con TypeScript 5.7 y Vite 6.
- **Enrutamiento:** React Router DOM 7 con layouts estructurados y guardias de autenticación.
- **Estado Global:** Zustand stores para sesión de usuario, telemetría y estado de navegación.
- **Cliente HTTP:** `api-client.ts` centralizado con inyección automática de CSRF, refresco transparente de sesión en 401 y anti-double-prefix (`buildUrl`).

---

## 6. Inventario Completo de Endpoints y Operaciones HTTP
- **Total de Rutas Registradas:** 828 rutas (Paths).
- **Total de Operaciones HTTP:** 973 operaciones.
  - **GET:** 399
  - **POST:** 513
  - **PATCH:** 40
  - **DELETE:** 13
  - **PUT:** 8
- Inventario detallado archivado en [`backend-endpoints.md`](./backend-endpoints.md).

---

## 7. Análisis de Seguridad y Autenticación (Cookies, JWT, Argon2id, CSRF)
- **Hashing de Contraseñas:** Argon2id (`argon2-cffi`) con dummy password verification en tiempo constante contra ataques de enumeración de usuarios.
- **Protección CSRF:** Double Submit Cookie pattern (`csrf_token` cookie + header `X-CSRF-Token` en métodos mutables `POST`, `PUT`, `PATCH`, `DELETE`).
- **Seguridad de Cookies:**
  - `session_token`: `HttpOnly=True`, `SameSite=Lax`, Max-Age=15m (`ACCESS_TOKEN_EXPIRE_MINUTES`).
  - `refresh_token`: `HttpOnly=True`, `SameSite=Lax`, Max-Age=30d (`REMEMBER_SESSION_EXPIRE_DAYS`) / 480 min (8h estándar `SESSION_EXPIRE_MINUTES`).
  - `device_token`: `HttpOnly=True`, `SameSite=Lax`, Max-Age=30d (`REMEMBER_SESSION_EXPIRE_DAYS`).
  - `csrf_token`: `HttpOnly=False`, `SameSite=Lax`, Max-Age=1h (3600 s).
- **Detección de Reutilización de Refresh Tokens:** Revocación inmediata de sesión ante detección de replay attack.

---

## 8. Análisis de Base de Datos, Motor PostgreSQL y Estado de Alembic
- **Motor:** PostgreSQL 16.4 Alpine.
- **Esquema:** `public` con 390 tablas relacionales.
- **Alembic Version:** `gi450410045dk (head)` — 1 sola cabeza lineal sincronizada, 0 migraciones pendientes.
- **Pool de Conexiones:** SQLAlchemy pool con pre-ping y timeouts controlados.

---

## 9. Inventario de Tablas, Entidades y Esquema de Persistencia
- **Entidades Núcleo F001:** `users`, `sessions`, `devices`, `audit_logs`, `organizations`, `branches`, `warehouses`, `continuous_auth_evaluations`, `experimental_sessions`.
- **Dominios Logísticos:** Inventario, almacenes, órdenes de compra, control de accesos/garita, transporte, flotas, conductores, liquidaciones, calidad y firmas digitales.
- Inventario detallado archivado en [`database-inventory.md`](./database-inventory.md).

---

## 10. Verificación de Probes de Salud y Disponibilidad
Pruebas ejecutadas en vivo contra el backend:
- `GET /health` -> `200 OK` (`{"status":"ok","environment":"development","version":"0.9.1"}`)
- `GET /live` -> `200 OK` (`{"status":"ok"}`)
- `GET /ready` -> `200 OK` (`{"status":"ok"}`)
- `GET /api/health` -> `200 OK` (`{"status":"ok","environment":"development","version":"0.9.1","database":{"status":"connected"}}`)

**Parámetros de Versión:**
- `CODE_DEFAULT_APP_VERSION`: `0.9.8` (`backend/app/core/config.py`)
- `COMPOSE_DEVELOPMENT_DEFAULT`: `0.9.1` (`compose.yaml`)
- `VERIFIED_RUNTIME_VERSION`: `0.9.1` (Configuración inyectada en entorno de desarrollo)

---

## 11. Inspección de CORS, Orígenes Permitidos y Manejo de Credenciales
- **Petición Preflight OPTIONS:** Verificada desde `http://localhost:5173`.
- **Headers Verificados:**
  - `Access-Control-Allow-Origin: http://localhost:5173`
  - `Access-Control-Allow-Credentials: true`
  - `Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS`
  - `Access-Control-Allow-Headers: Authorization, Content-Type, X-CSRF-Token, X-Request-ID, Accept-Language`

---

## 12. Validación de Contratos de API, Envelope y Formato de Errores
- Todos los errores retornan el envelope canónico:
  `{"error": {"code": str, "message": str, "request_id": str, "timestamp": str, "details": null | dict}}`
- El header `X-Request-ID` se propaga en el 100% de las respuestas HTTP.
- Documentación completa en [`protected-contracts.md`](./protected-contracts.md).

---

## 13. Auditoría de Seguridad de Frontend (Protección de Rutas, Anti-Double-Prefix)
- **Guardián de Rutas:** Verificación de sesión en store Zustand antes de renderizar vistas privadas.
- **Anti-Double-Prefix:** `buildUrl` en `api-client.ts` bloquea cualquier ruta que comience con `/api/` evitando errores de ruta doble.
- **Gestión de Credenciales:** `credentials: 'include'` en todas las peticiones `fetch`.

---

## 14. Auditoría de Internacionalización (i18n) y Catálogos de Mensajes
- Middleware de i18n intercepta errores y traduce códigos de error en base a catálogos centralizados (`es`, `en`, `pt`).
- Respuestas con formato uniforme y traducción contextual.

---

## 15. Hallazgos y Defectos Detectados durante la Retro-Auditoría
1. **Defecto de Fixture SQLite (`backend/tests/conftest.py`):**
   - *Descripción:* La lista `allowed_prefixes` en el fixture de SQLite en memoria omitía `"devices"`, `"clients"`, `"incidents"`, `"continuous_"`, `"facial_"`, `"behavioral_"`, `"consent_"`, `"research_"`.
   - *Impacto:* Fallo con `OperationalError: no such table: devices` durante las pruebas de login de autenticación.
2. **Defecto de Comparación de Datetimes con Zona Horaria:**
   - *Descripción:* Comparación directa entre objetos `datetime` offset-naive (retornados por SQLite) y `utc_now()` offset-aware en `session_service.py`, `auth_service.py` y `auth.py`.
   - *Impacto:* `TypeError: can't compare offset-naive and offset-aware datetimes` y `can't subtract offset-naive and offset-aware datetimes`.
3. **Inconsistencia de Aserción en `test_auth_flow.py`:**
   - *Descripción:* Aserción de mensaje literal en vez de código de error canónico `INVALID_CREDENTIALS`.

---

## 16. Correcciones Aplicadas en la Fase 001 (Backend)
- **`backend/tests/conftest.py`:** Incorporados los prefijos faltantes a `allowed_prefixes` en los fixtures de base de datos de prueba.
- **`backend/app/database/base.py`:** Creada y exportada la función de normalización temporal `ensure_utc(dt)`.
- **`backend/app/services/session_service.py`:** Aplicada normalización `ensure_utc` a `expires_at`, `last_activity_at` y `refresh_expires_at`.
- **`backend/app/services/auth_service.py`:** Aplicada normalización `ensure_utc` a `user.locked_until`.
- **`backend/app/api/routes/auth.py`:** Aplicada normalización `ensure_utc` en el cálculo de tiempo restante del refresh token.
- **`backend/tests/test_auth_flow.py`:** Corregida la aserción de error para validar `response.json()["error"]["code"] == "INVALID_CREDENTIALS"`.

---

## 17. Correcciones Aplicadas en la Fase 001 (Frontend)
- El repositorio frontend `Anthgg/LogisticaF` se encuentra en perfecto estado, con 0 errores de compilación, 0 errores de linter y el 100% de las pruebas pasando limpiamente (`FRONTEND_PHASE001_CHANGES: NONE`).

---

## 18. Resultados de la Suite de Pruebas del Backend (Pytest)
- **Pruebas de Línea Base F001:**
  - `tests/test_health.py`: 5 passed
  - `tests/test_auth_flow.py`: 8 passed
  - `tests/test_auth_security.py`: 8 passed
  - `tests/test_continuous_auth_api.py`: 9 passed
- **Total Pruebas F001:** **30 passed / 0 failed / 100% verde** (Tiempo de ejecución: 14.85s).

---

## 19. Resultados de la Suite de Pruebas del Frontend (Typecheck, Oxlint, Vitest, Build)
- **TypeScript Typecheck:** `npm run typecheck` -> **0 errores**
- **Oxlint Linter:** `npm run lint` -> **0 errores**
- **Vitest Unit & Integration:** `npm run test:run` -> **91 test files passed, 603 tests passed, 0 failed** (Duración: 97.43s)
- **Vite Production Build:** `npm run build` -> **Build exitoso en 10.83s, bundle generado en `dist/`**

---

## 20. Plan de Verificación y Pruebas de Aceptación de Usuario (UAT)
El usuario realizará una verificación manual funcional de los flujos críticos de la Fase 001 utilizando el navegador web y las herramientas de desarrollo.

---

## 21. Procedimiento Paso a Paso para la Prueba Funcional del Usuario
1. **Verificar Estado de Contenedores:**
   ```powershell
   docker ps --filter "name=continuous-authentication"
   ```
2. **Consultar Probes de Salud:**
   Abrir navegador en `http://localhost:8000/health` y `http://localhost:8000/api/health`.
3. **Iniciar Frontend:**
   ```powershell
   cd "c:\Users\anthg\OneDrive\Escritorio\proyecto tesis front\frontend"
   npm run dev
   ```
4. **Prueba de Autenticación en UI:**
   - Navegar a `http://localhost:5173`.
   - Abrir DevTools (F12) -> pestaña Network y pestaña Application -> Cookies.
   - Iniciar sesión con credenciales de prueba.
   - Comprobar la presencia de las cookies `session_token` (HttpOnly), `refresh_token` (HttpOnly) y `csrf_token`.
   - Navegar entre módulos y cerrar sesión verificando la revocación de cookies.

---

## 22. Matriz de Trazabilidad y Verificación de Requisitos
| Requisito F001 | Estado | Evidencia |
| :--- | :--- | :--- |
| Health & Readiness Probes | `CUMPLIDO` | `/health`, `/live`, `/ready`, `/api/health` retornan 200 OK |
| Autenticación Segura Argon2id | `CUMPLIDO` | `test_auth_flow.py` (30/30 passed) |
| Protección CSRF Double Submit | `CUMPLIDO` | Header `X-CSRF-Token` + Cookie `csrf_token` verificado |
| Rotación de Refresh Tokens | `CUMPLIDO` | Detección de reuso y revocación probada |
| Esquema PostgreSQL & Alembic | `CUMPLIDO` | Head `gi450410045dk`, 390 tablas |
| Frontend Typecheck & Vitest | `CUMPLIDO` | 603/603 tests pasando, 0 lint/type errors |

---

## 23. Registro de Auditoría de Código y Calidad Estática
- Cumplimiento de estándares PEP 8, anotaciones de tipos estrictas (mypy/pydantic v2) en Backend.
- Tipado estricto en TypeScript sin uso de `any` descontrolado en Frontend.

---

## 24. Riesgos Identificados y Deuda Técnica Documentada
- Los módulos posteriores (Fases 037+ que utilizan renderizado PDF o canvas) requieren librerías de soporte que serán auditadas y garantizadas en sus respectivas fases.
- Se mantiene el principio de no introducir dependencias ajenas a F001.

---

## 25. Directrices de Regresión y Políticas para Fases Futuras
- Ninguna fase futura puede modificar los contratos de seguridad de sesión ni debilitar las protecciones CSRF.
- Toda modificación de esquema debe pasar por migraciones lineales de Alembic.

---

## 26. Estado de Ramas Git y Estrategia de Merge
- **Rama Backend:** `audit/retro-phase-001-backend`
- **Rama Frontend:** `N/A` (Sin modificaciones)
- La rama de backend queda lista con los cambios de auditoría y documentación archivada para revisión y merge por parte del usuario.

---

## 27. Checklist de Cierre y Puerta de Calidad (Quality Gate)
- [x] Backend Docker Containers saludables
- [x] PostgreSQL 16.4 y Alembic sincronizados
- [x] 828 rutas y 973 operaciones inventariadas
- [x] Contratos CSRF, Cookies y Envelope validados
- [x] Defectos F001 corregidos en backend
- [x] Pytest baseline suite: 30/30 PASSED
- [x] Frontend Typecheck, Lint, Vitest (603/603) y Build: PASSED
- [x] Documentación de 28 secciones generada
- [ ] Validación UAT por el usuario (`PENDING_USER_TEST`)

---

## 28. Declaración Final de la Fase 001 y Bloqueo Formal de la Fase 002
La **Fase 001** se declara en estado:
```
PHASE_001_READY_FOR_USER_ACCEPTANCE
USER_ACCEPTANCE: PENDING_USER_TEST
```

> **BLOQUEO ESTRICTO:** La **Fase F002** y todas las fases posteriores (F003 a F100) permanecen en estado **`BLOCKED`**. Queda terminantemente prohibido iniciar trabajos o auditorías de la Fase F002 hasta que el usuario complete la prueba de aceptación funcional, otorgue su aprobación formal y se realice el merge de la Fase 001.
