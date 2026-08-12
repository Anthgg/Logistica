# 11 — Control de Anomalías en Importaciones (`RucImportAnomalousRowCountError`)

## 1. Detección de Caída Brusca de Registros (>20%)

Un riesgo operacional mayor en la ingesta automática de padrones masivos es la descarga de un archivo ZIP truncado o incompleto emitido por la fuente externa. Para evitar que un padrón parcial reemplace al padrón completo activo, el sistema ejecuta una validación estricta pre-activación:

```python
class RucRegistryImportService:
    MAX_ALLOWED_DROP_PERCENTAGE = 20.0  # Umbral máximo de caída de filas (20%)

    async def _validate_anomaly_thresholds(self, db_session, new_dataset: RucDatasetVersionModel):
        active_version = await self.get_active_dataset_version(db_session, new_dataset.dataset_type)
        if not active_version:
            return  # Primera importación

        previous_rows = active_version.accepted_rows
        new_rows = new_dataset.accepted_rows

        if previous_rows > 0:
            drop_percentage = ((previous_rows - new_rows) / previous_rows) * 100.0
            if drop_percentage > self.MAX_ALLOWED_DROP_PERCENTAGE:
                new_dataset.status = "REJECTED_ANOMALOUS"
                await db_session.commit()
                
                raise RucImportAnomalousRowCountError(
                    f"Importación abortada por caída anómala de registros: "
                    f"Anterior={previous_rows}, Nuevo={new_rows} (Caída de {drop_percentage:.2f}%)."
                )
```

---

## 2. Acciones ante Anomalía Detectada

1. **Rechazo del Dataset**: El estado de la versión en staging cambia inmediatamente a `REJECTED_ANOMALOUS`.
2. **Preservación del Dataset Activo**: La versión previa `ACTIVE` no sufre ninguna modificación y continúa sirviendo las consultas de producción.
3. **Registro de Auditoría y Alerta**: Se emite el evento de auditoría `RUC_ANOMALY_DETECTED` notificando al equipo de operaciones y registrando el log de error crítico.
