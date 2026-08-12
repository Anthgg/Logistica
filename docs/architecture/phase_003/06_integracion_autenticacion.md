# 06. Integración con Autenticación

## Reutilización exacta

| Componente | Origen | Cómo se reutiliza |
|-----------|--------|-------------------|
| Usuario autenticado | `app.dependencies.auth.get_current_user` | `get_logistics_current_user` lo envuelve |
| Sesión | `app.dependencies.auth.get_current_session` | `get_logistics_current_session` lo envuelve |
| CSRF | `app.dependencies.csrf.verify_csrf` | Se importa directamente en `dependencies.py` |
| Cookies HTTP-only | Config existente | Sin cambios |
| `/auth/me` | Router existente | Sin cambios |
| 401/403 | `ApplicationError` existente | Sin cambios |

## Lo que NO se creó

- No se creó `LogisticsUser` ni `LogisticsSession`.
- No hay segundo login, segundo token JWT, ni segunda cookie.
- No hay middleware CSRF separado.
- No hay tabla de usuarios logísticos.

## Permisos

La dependencia `require_logistics_permission(*permissions)` envuelve `require_active_user`. En Phase 003 el check siempre pasa — el hook está listo para que Phase 005 wire el RBAC real.