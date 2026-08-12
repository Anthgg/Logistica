# 09 — Flujo de Ingesta, Staging y Activación Atómica

## 1. Etapa de Staging

El proceso de ingesta inserta los lotes de contribuyentes vinculados a un nuevo `dataset_version_id` con el estado inicial `STAGED`. Durante esta fase, el dataset anterior permanece en estado `ACTIVE` resolviendo todas las consultas en producción sin degradación de servicio.

```python
async def stage_dataset_records(db_session, dataset_version_id: UUID, records_batches):
    for batch in records_batches:
        stmt = insert(RucRegistryEntryModel).values([
            {**rec, "dataset_version_id": dataset_version_id, "row_status": "STAGED"}
            for rec in batch
        ])
        await db_session.execute(stmt)
    await db_session.commit()
```

---

## 2. Activación Atómica del Puntero de Dataset

Una vez completada la fase de staging y superadas las validaciones de anomalía, la conmutación a la nueva versión se realiza en una **única transacción SQL atómica**:

```sql
BEGIN TRANSACTION;

UPDATE ruc_dataset_versions 
SET status = 'SUPERSEDED' 
WHERE dataset_type = 'RUC_GENERAL' AND status = 'ACTIVE';

UPDATE ruc_dataset_versions 
SET status = 'ACTIVE', activated_at = NOW() 
WHERE id = 'new-dataset-uuid-here';

COMMIT TRANSACTION;
```

---

## 3. Invalidación Inmediata de Caché

Tras la confirmación del `COMMIT TRANSACTION`, se invoca `RucLookupCache.flush_namespace("ruc:*")`, lo que fuerza a las siguientes consultas a leer de la base de datos la nueva versión `ACTIVE` e ir repoblando la caché de manera transparente.
