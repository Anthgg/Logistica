# Fase 005.1 — Normalización de formularios, catálogos y códigos automáticos

Estado: **cerrada**. Backend y frontend en `main`.

F005.1 no añadió funcionalidad de negocio: quitó del formulario todo lo que el usuario
no debería estar escribiendo. El principio que la ordena, formulado por el usuario:

> No permitas UUID, IDs internos o códigos técnicos escritos manualmente por el usuario
> si pueden derivarse o generarse automáticamente.

## Documentos

| Documento | Contenido |
|---|---|
| [`automatic-codes.md`](automatic-codes.md) | Generación de códigos y seguridad ante concurrencia |
| [`reference-catalogs.md`](reference-catalogs.md) | País, zona horaria y tipo de almacén |
| [`warehouse-location.md`](warehouse-location.md) | Estrategia B: geografía derivada de la sede |

## Las tres normalizaciones

1. **Códigos**: `ORG…`, `SED…`, `ALM…` los genera el backend. El campo de código
   desapareció del formulario de alta.
2. **Catálogos**: país, zona horaria y tipo de almacén pasaron de texto libre / listas
   duplicadas en frontend a catálogos servidos por el backend.
3. **Ubicación de almacén**: distrito, provincia y departamento ya no se escriben; se
   derivan del UBIGEO de la sede.

## Alcance de esquema

Una sola migración: `jl480110048dk_phase_005_1_entity_code_counters`. Crea
`entity_code_counters`, habilita RLS y siembra los contadores desde el `COUNT(*)+1` de
las filas existentes, de modo que ningún código nuevo colisiona con los ya emitidos.

Ninguna columna existente cambió de tipo ni se borró.
