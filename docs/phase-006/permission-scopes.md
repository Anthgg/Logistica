# Ámbitos

F006 no crea un modelo de ámbitos: usa el de F005.

## Ámbitos reales

`global`, `organization`, `branch`, `warehouse` — declarados en `ALL_SCOPES` y usados
como `scope_type` de cada asignación de rol.

Por defecto, todo permiso admite los cuatro. La restricción efectiva la impone la
**asignación**, no el permiso: un rol concedido con `scope_type="organization"` y una
`organization_id` limita a su titular a esa organización.

## Cómo se aplica

`LogisticsPrincipal.can_access_organization/branch/warehouse` compara el recurso pedido
contra los ámbitos del principal. Un principal sin ámbitos declarados no está acotado
—contrato preexistente— y uno con ámbitos solo alcanza los suyos.

Desde F006 PR 1 **el rol de plataforma ya no levanta ese filtro**: antes
`is_platform_admin` devolvía `True` en las tres comprobaciones, de modo que un
administrador veía todos los tenants sin que ninguna asignación se lo concediera.

## `X-Org-Id`

La cabecera existe y es legítima, pero es una **preferencia, no una autorización**:
`resolve_organization_id` comprueba que el principal pueda acceder a la organización
pedida y devuelve 403 si no. Antes se devolvía tal cual, así que bastaba enviarla para
operar sobre la organización de otro.

Un principal con ámbito global y sin organización resoluble recibe
`400 LOGISTICS_ORGANIZATION_REQUIRED`. Es deliberado: antes se caía a un UUID fijo y
escribía en una organización por defecto. Negarse es mejor que adivinar el tenant.

## Estado de las asignaciones

El estado canónico es `active`, en minúsculas, y así lo escribe siempre la API.

En producción existe una fila sembrada con `ACTIVE`. La comparación exacta la
descartaba en silencio: el usuario perdía ese rol sin error ni traza. Desde F006 PR 2
la lectura normaliza a minúsculas.

No se modificó el dato ni se añadió una restricción en base: normalizar al leer resuelve
el caso sin tocar producción ni crear una migración. `SILENT_ACTIVE_ASSIGNMENT_IGNORES = 0`.

La normalización no ablanda el resto: una asignación `revoked` sigue sin conceder nada,
y hay una prueba que lo fija.
