# Runbook — release de base de datos a producción

Sin credenciales en este documento. Todos los valores sensibles viven en Secret Manager.

## PRECHECK

Antes de lanzar nada, comprobar y anotar:

| Comprobación | Cómo | Criterio |
|---|---|---|
| Revisión actual de la base | Workflow en modo `verify-only` | Debe ser conocida |
| Cabezas de Alembic | Salida del Job: `HEADS=` | Exactamente `1` |
| Camino de migración | `CURRENT` → `TARGET` | Todas las revisiones intermedias son conocidas |
| Punto de recuperación | Panel de Supabase → Database → Backups | Existe backup reciente |
| Imagen del Job | `gcloud run jobs describe` | Etiquetada con el SHA del commit a liberar |

Si la revisión de la base **no pertenece al grafo del repositorio**: parar. No se
corrige con `alembic stamp`; eso solo oculta el problema y traslada el daño a la
siguiente migración.

## EXECUTE

1. GitHub → Actions → *Out-of-Band Database Migration Job* → Run workflow.
2. `target_environment`: `production`.
3. `mode`: primero `verify-only`. Leer la salida. Solo entonces repetir con `upgrade`.
4. `expected_alembic_head`: opcional; si se rellena, el Job aborta cuando la imagen no
   corresponde a esa cabeza.
5. Aprobar el environment si tiene revisores configurados.

El workflow espera a que el Job termine (`--wait`) y luego lee `succeededCount` y
`failedCount` de la ejecución. Un Job que arranca y muere no pasa por verde.

## VERIFY

El propio Job ejecuta la verificación al final. Debe verse:

```
FINAL=<revisión objetivo>
  PASS  revisión = <objetivo>
  PASS  F004: 3 tabla(s) presentes
  PASS  F004.5: 3 tabla(s) presentes
  PASS  F005.1: 1 tabla(s) presentes
  PASS  geo_departments: 25
  PASS  geo_provinces: 196
  PASS  geo_districts: 1893
  PASS  RLS entity_code_counters: habilitado
  PASS  colisión organization: next=N > máximo emitido=M
RESULTADO=PASS
```

Los conteos UBIGEO importan más de lo que parece: la migración que los siembra lee un
JSON con `if os.path.exists(...)`. Si ese fichero faltara en la imagen, la migración
**terminaría bien y dejaría las tablas vacías**. El conteo es lo único que distingue
ese caso del éxito.

## FAILURE

| Síntoma | Qué significa | Acción |
|---|---|---|
| Falla la autenticación | Credenciales GCP inválidas o caducadas | Rotar la credencial. El workflow ya no continúa. |
| `HEADS != 1` | El grafo se bifurcó | Linearizar en el repositorio. No forzar en producción. |
| `head de la imagen != esperado` | La imagen no corresponde al release | Reconstruir y reetiquetar |
| Falla a mitad de `upgrade` | Una revisión abortó | Ver logs del Job. La transacción de esa revisión revierte; las anteriores ya están aplicadas. Reejecutar tras corregir. |
| `RESULTADO=FAIL` con conteos geo a 0 | El JSON no viajó en la imagen | Reconstruir la imagen; no insertar datos a mano |
| `colisión ... <= máximo emitido` | El contador reutilizaría códigos | **Parar.** Corregir con una migración adicional, nunca a mano |

## RECOVERY

`ROLLBACK_STRATEGY=CASE_BY_CASE`.

`alembic downgrade -1` **no** es seguro por defecto en producción: los `downgrade()` de
estas revisiones hacen `drop_table` y `drop_column`, y eso destruye datos que la
migración de subida sí creó. Para F004.5 significaría perder el catálogo UBIGEO y la
columna `ubigeo_code` de las sedes.

Orden de preferencia:

1. **Corregir hacia adelante**: nueva migración que arregla lo que quedó mal.
2. **Restaurar desde backup** de Supabase, si el daño es de datos y hay punto de
   recuperación válido.
3. **Downgrade**, solo tras revisar la función `downgrade()` concreta y confirmar que
   no borra nada que importe.

Nunca: editar `alembic_version` a mano, ni `alembic stamp` para simular que la base
está al día.
