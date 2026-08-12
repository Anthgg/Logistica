# Evaluación final controlada

Este paquete ejecuta la evaluación final del sistema sin entrenamiento ni
recalibración. Los scripts de componente solo consumen predicciones ya
autorizadas. La única entrada que puede abrir el conjunto test real es
`run_final_evaluation.py`, después de validar la aprobación, crear el lock y
crear el marcador de inicio.

## Compuertas

La ejecución requiere:

- `models/registry/model_registry.json` y todos sus artefactos.
- `models/fusion/fusion_config.json`.
- `models/fusion/score_normalization.json`.
- `models/registry/integration_approval.json` con estado
  `approved_for_final_evaluation`.
- Hashes SHA-256 de todos los artefactos aprobados.
- Configuraciones de ablación e histéresis aprobadas.
- Manifiesto test, sidecar SHA-256 y metadatos congelados.

El archivo de aprobación presente en el repositorio está deliberadamente
bloqueado hasta que existan artefactos reales. No debe cambiarse a aprobado por
conveniencia.

## Dry-run seguro

```powershell
python evaluation/scripts/run_final_evaluation.py `
  --config evaluation/configs/final_evaluation.yaml `
  --dry-run
```

El dry-run lee configuración, aprobación, sidecars y metadatos, pero no abre el
Parquet test, no crea `evaluation_lock.json`, no crea marcadores y no genera
resultados.

## Ejecución definitiva

```powershell
python evaluation/scripts/run_final_evaluation.py `
  --config evaluation/configs/final_evaluation.yaml `
  --device auto
```

Una repetición accidental queda bloqueada. Una repetición excepcional requiere
simultáneamente `--authorized-rerun` y `--rerun-reason`, y conserva el motivo en
los metadatos.

Las pruebas en `evaluation/tests` usan únicamente datos sintéticos y
directorios temporales.
