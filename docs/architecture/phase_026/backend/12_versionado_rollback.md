# 12 — Versionado de Datasets y Procedimiento de Rollback

## 1. Servicio de Rollback Transaccional (`rollback_dataset`)

En caso de detectarse un problema de calidad de datos en el padrón activo en producción, el sistema permite revertir de inmediato la activación a una versión previa en estado `SUPERSEDED`.

```python
class RucRegistryImportService:
    async def rollback_dataset(self, db_session, organization_id: UUID, target_version_id: UUID, requested_by: UUID):
        target_version = await db_session.get(RucDatasetVersionModel, target_version_id)
        if not target_version or target_version.status != "SUPERSEDED":
            raise RucImportError("Solo se puede revertir a un dataset en estado SUPERSEDED.")

        current_active = await self.get_active_dataset_version(db_session, target_version.dataset_type)
        
        async with db_session.begin():
            if current_active:
                current_active.status = "ROLLED_BACK"
            target_version.status = "ACTIVE"
            target_version.activated_at = datetime.now(timezone.utc)

        await RucLookupCache.flush_namespace(f"ruc:{current_active.id if current_active else '*'}")
        await RucLookupCache.flush_namespace(f"ruc:{target_version.id}")
        
        await self.audit_service.log_event(
            event_type="RUC_DATASET_ROLLED_BACK",
            details={"previous_version": str(current_active.id), "restored_version": str(target_version_id)}
        )
```

---

## 2. Preservación del Historial de Versiones

Ninguna versión de dataset ingestada es eliminada de la base de datos durante un rollback. El cambio de estado a `ROLLED_BACK` o `SUPERSEDED` conserva la trazabilidad histórica de todas las descargas e ingestas realizadas.
