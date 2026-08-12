# 20 — Tareas Programadas y CLI Job (`run_ruc_import_job.py`)

## 1. Script CLI de Importación

La ingesta periódica del padrón se ejecuta mediante el script CLI desatendido ubicado en `backend/app/modules/logistics/ruc/infrastructure/jobs/run_ruc_import_job.py`:

```python
import argparse
import asyncio
import sys
from app.modules.logistics.ruc.application.services.import_service import RucRegistryImportService

async def main():
    parser = argparse.ArgumentParser(description="Job de Importación Masiva Padrón RUC SUNAT")
    parser.add_argument("--source-code", default="SUNAT_REDUCED_REGISTRY", help="Código de la fuente de datos")
    parser.add_argument("--dataset-type", default="RUC_GENERAL", help="Tipo de dataset (RUC_GENERAL | RUC_ANNEX_ADDRESS)")
    parser.add_argument("--force", action="store_true", help="Fuerza descarga omitiendo validación de hash")
    args = parser.parse_args()

    service = RucRegistryImportService()
    result = await service.execute_import_pipeline(
        source_code=args.source_code,
        dataset_type=args.dataset_type,
        force_download=args.force
    )
    print(f"Importación completada exitosamente. Dataset ID: {result.id}, Filas: {result.accepted_rows}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 2. Despliegue en GCP Cloud Run Jobs / Cron Kubernetes

- **Frecuencia Recomendada**: Semanal (Domingos 02:00 UTC) o Mensual según ciclo de publicación de SUNAT.
- **Advisory Lock en PostgreSQL**: El job solicita un bloqueo explícito `SELECT pg_try_advisory_lock(882601)` al iniciar para evitar ejecuciones concurrentes accidentales.
