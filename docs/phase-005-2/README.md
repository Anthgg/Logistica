# Fase 005.2 — Pipeline de release de base de datos (Supabase)

Estado: **cerrada**. Pipeline operativo y migración productiva ejecutada el 17 de agosto de 2026.

## El problema que resuelve

El workflow `database-migration.yml` existía desde hacía meses y no había migrado
nunca nada. Hacía dos cosas mal, y las dos producían verde:

```yaml
- name: Authenticate to GCP
  uses: google-github-actions/auth@v2
  continue-on-error: true          # (1) un fallo de credenciales seguía adelante

- name: Execute Cloud Run Migration Job
  run: |
    echo "Executing: gcloud run jobs execute ..."   # (2) imprimía el comando
```

Es decir: `REAL_MIGRATION_EXECUTION=FALSE`. El pipeline informaba de éxito sin haber
tocado la base.

## Documentos

| Documento | Contenido |
|---|---|
| [`architecture.md`](architecture.md) | Flujo completo y por qué la migración va fuera de banda |
| [`runbook.md`](runbook.md) | Procedimiento manual: precheck, ejecución, verificación, fallo, recuperación |
| [`supabase-state.md`](supabase-state.md) | Estado real auditado de la base productiva |
| [`infra-audit.md`](infra-audit.md) | Inventario GCP real frente al documentado, y hallazgos de seguridad |

## Qué entrega esta fase

1. **Ejecución real** del Cloud Run Job con `--wait`, y verificación del resultado
   leyendo el recurso de ejecución — lanzar no es completar.
2. **Autenticación que falla en seco**: sin `continue-on-error`.
3. **`scripts/run_migration_job.sh`**: comprueba revisión y head, aborta con más de una
   cabeza, y admite `verify-only` que no escribe nada.
4. **`scripts/verify_production_schema.py`**: verificación de solo lectura (revisión,
   tablas, conteos UBIGEO, RLS y riesgo de colisión de códigos), con el destino
   enmascarado.
5. **14 pruebas estáticas** que fallan si vuelve el `echo` o el `continue-on-error`.

## Qué NO entrega

- No despliega el servicio web. `INFRA_DEPLOYMENT_PIPELINE` sigue abierto.
- No modifica ninguna migración histórica.
- No toca lógica de dominio.
- No usa `alembic stamp` para disimular drift.
