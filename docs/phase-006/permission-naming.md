# Nomenclatura

Convención vigente, verificada por CI sobre los 555 permisos:

```
<dominio>.<recurso>.<accion>
```

Todo en minúsculas, separado por puntos. 100% de los códigos la cumplen; ninguno tiene
mayúsculas y no hay colisiones al ignorarlas.

El prefijo real es `logistics.` para el dominio logístico; `<recurso>` es el sustantivo
en plural (`drivers`, `warehouses`, `role_assignments`) y `<accion>` el verbo
(`read`, `create`, `approve`).

Unos pocos usan cuatro segmentos cuando el recurso tiene subrecurso:
`logistics.inventory.adjustments.approve`, `logistics.files.evidence.accept`. Es
deliberado: `inventory.approve` no diría qué se aprueba.

## Acciones observadas

`read`, `create`, `update`, `delete`, `approve`, `reject`, `cancel`, `submit`,
`activate`, `revoke`, `export`, `verify`, `reconcile`, `archive`, `restore`.

## Acciones vagas

`manage` sobrevive en unos pocos códigos heredados
(`logistics.supplier_evaluation_templates.manage`,
`logistics.quality_quarantine.manage_zones`). Concede más de lo que su nombre
transparenta y no se puede saber qué autoriza sin leer el endpoint.

**No se renombran**: el código es un identificador estable y cambiarlo rompe
asignaciones vivas. Para permisos nuevos no se usa `manage`: F006 PR 2 declaró
`files.update`, `files.archive`, `files.restore`, `files.legal_hold` y
`files.evidence.accept` por separado en lugar de un `files.manage`, precisamente porque
archivar y aceptar custodia son potestades distintas.

## Lo que no existe, y no debe existir

Ni `*`, ni `all`, ni `full_access`, ni `superuser`. `WILDCARD_PERMISSION_SUPPORT=FALSE`.
La autorización es siempre una pertenencia explícita al conjunto de permisos efectivos.
