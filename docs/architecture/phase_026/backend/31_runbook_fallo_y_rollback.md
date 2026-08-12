# 31 — Runbook de Contingencia, Diagnóstico de Fallos y Rollback

## 1. Procedimiento de Rollback de Emergencia

Si se detectan inconsistencias graves en la información del nuevo padrón activo en producción:

### Vía Endpoint REST (Requiere Step-Up Token):
```http
POST /api/logistics/ruc/datasets/target-dataset-uuid-here/rollback HTTP/1.1
Host: api.erp.empresa.com
Authorization: Bearer <ADMIN_JWT>
X-Step-Up-Token: <OTP_TOKEN>
```

### Vía CLI de Emergencia:
```bash
python -m app.modules.logistics.ruc.infrastructure.jobs.run_ruc_import_job --rollback-to target-dataset-uuid-here
```

---

## 2. Matriz de Síntomas y Acciones

| Síntoma | Causa Probable | Acción Correctiva |
| :--- | :--- | :--- |
| `RucImportAnomalousRowCountError` | El archivo ZIP descargado estuvo incompleto o la fuente cortó la descarga. | El sistema rechaza automáticamente la versión. Descargar manualmente y ejecutar con `--force`. |
| Latencia de consulta `> 50ms` | Pérdida de índices B-Tree en PostgreSQL tras vacuum masivo. | Ejecutar `REINDEX INDEX ix_ruc_registry_entries_normalized_ruc;`. |
| Error `RucImportUrlNotAllowedError` | El dominio oficial de SUNAT cambió o no está en la lista blanca. | Actualizar la configuración `ALLOWED_HOSTS` en `SafeZipDownloader`. |
