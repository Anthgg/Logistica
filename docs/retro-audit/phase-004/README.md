# F004 · Retro-auditoría · Definir organización, sedes y almacenes

Estado: **PHASE_004_REQUIRES_ADDITIONAL_FIXES** (primera corrida — solo auditoría).

## Alcance

Estructura organizacional básica: organización, sede (branch), almacén (warehouse)
como entidad estructural, sus relaciones, persistencia, contratos API e integración
real desde navegador.

Fuera de alcance, no tocado: racks / posiciones / ubicaciones internas / QR masivo /
mapa interno (F022); editor de roles y catálogo de permisos (F005/F006).

## Aislamiento

| | |
|---|---|
| Backend worktree | `C:/Users/anthg/Logistica-F004` |
| Backend branch | `audit/retro-phase-004-backend` desde `origin/main` `c421dcc` |
| Frontend worktree | `C:/Users/anthg/LogisticaF-F004` |
| Frontend branch | `audit/retro-phase-004-frontend` desde `origin/main` `8dcf23b` |

Sin cambios de código en esta corrida. `git diff origin/main` vacío en ambos, por lo que
todo lo observado en el runtime activo corresponde byte a byte al head F004.

## Resultado en una línea

Organizaciones y sedes están razonablemente integradas. **Almacenes no lo están**: la
lista siempre sale vacía por dos causas independientes y comprobadas, no existe UI de
creación, y el DTO TypeScript describe un contrato que el backend nunca emitió.

## Índice

- [capability-matrix.md](capability-matrix.md) — matriz por capacidad
- [backend-contract.md](backend-contract.md) — endpoints reales y sus contratos
- [frontend-coverage.md](frontend-coverage.md) — rutas, páginas y clientes API
- [database-audit.md](database-audit.md) — tablas, FKs, constraints y drift de migraciones
- [browser-acceptance.md](browser-acceptance.md) — preparación de superficies para UAT
- [user-acceptance.md](user-acceptance.md) — pendiente de prueba humana

## Deudas ajenas, no tocadas

- `DEV_TEST_FIXTURE_CLEANUP` (5 documentos fixture contaminados).
- `C:/Users/anthg/Logistica-F003/scripts/verify_runtime_identity.py` (untracked, de otra sesión).
- Worktrees históricos F002 / F002-Closeout / F003.
