# 30 — Runbook de Operación de Importación Masiva de Padrones

## 1. Ejecución Manual Vía CLI

Para ejecutar una importación manual fuera del cron programado (por ejemplo, tras la publicación del nuevo padrón por SUNAT):

```bash
cd /app/backend

python -m app.modules.logistics.ruc.infrastructure.jobs.run_ruc_import_job --source-code SUNAT_REDUCED_REGISTRY --dataset-type RUC_GENERAL

python -m app.modules.logistics.ruc.infrastructure.jobs.run_ruc_import_job --check-status
```

---

## 2. Checklist Post-Importación

- [ ] Verificar que el estado del nuevo dataset sea `ACTIVE` en `ruc_dataset_versions`.
- [ ] Confirmar que `accepted_rows` sea concordante con la cifra publicada por SUNAT.
- [ ] Verificar que el log de auditoría contenga el evento `RUC_DATASET_ACTIVATED`.
- [ ] Ejecutar una consulta de prueba en el endpoint GET `/api/logistics/ruc/lookup/20100070970` y validar que retorne HTTP 200 con `staleness_level: FRESH`.
