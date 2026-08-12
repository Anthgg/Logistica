# Artefactos de integración

Esta carpeta no contiene valores iniciales inventados.

`score_normalization.json` se genera exclusivamente con:

```powershell
python backend/scripts/calibrate_score_normalization.py `
  --dataset-version pilot-v0.1.0
```

`fusion_config.json` se genera exclusivamente con:

```powershell
python backend/scripts/calibrate_fusion.py `
  --dataset-version pilot-v0.1.0
```

Ambos scripts rechazan filas `test`, exigen datos `validation`, registran el
dataset de procedencia y calculan un checksum canónico excluyendo el propio
campo `checksum`.
