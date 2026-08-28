# Roles heredados: `ADMIN_LOGISTICA` y `operator`

Estado: **congelados por decisión del usuario**. No son deuda accidental que quede
pendiente de limpiar por olvido; son una anomalía conocida cuya resolución se aplazó
deliberadamente.

## Qué son

Dos roles presentes en la base de datos que no pertenecen a `SYSTEM_ROLES`:

| Rol | Anomalía |
|---|---|
| `ADMIN_LOGISTICA` | Código en español; anterior a la convención `LOGISTICS_*` |
| `operator` | Código en minúsculas; no sigue ninguna convención vigente |

## Instrucción vigente

El usuario declaró estos roles `LEGACY_ROLE_ANOMALY` con la siguiente restricción
explícita:

> DO NOT RENAME / DO NOT DELETE / DO NOT MERGE / DO NOT NORMALIZE / DO NOT REASSIGN
> AUTOMATICALLY

F005 la respetó: no se renombraron, no se eliminaron, no se fusionaron con roles
canónicos, no se normalizaron sus códigos y no se reasignaron sus usuarios.

## Por qué importa antes de tocarlos

Renombrar o borrar un rol al que hay asignaciones vivas deja usuarios sin permisos de
forma silenciosa. Fusionarlo con un rol canónico puede en cambio **ampliar** los
permisos de esos usuarios sin que nadie lo pida. Ninguna de las dos consecuencias es
aceptable sin una decisión de negocio previa que diga qué debe pasar con cada usuario
afectado.

## Qué haría falta para resolverlos

1. Inventario de usuarios asignados a cada uno de los dos roles.
2. Decisión de negocio: para cada usuario, a qué rol canónico corresponde.
3. Migración de asignaciones con auditoría, no renombrado del rol.
4. Desactivación (no borrado) del rol heredado una vez sin asignaciones.

Nada de esto está autorizado todavía.
