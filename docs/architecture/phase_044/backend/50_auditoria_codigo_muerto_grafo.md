# 50 — Auditoría de “código muerto” del grafo

## Resultado reproducido

Después de indexar explícitamente este repositorio con modo `moderate`, el grafo
contiene 13 038 nodos y 75 497 aristas. La consulta de símbolos Python bajo
`backend/app`, no-entry-point y con grado máximo cero devuelve 411 candidatos:

- 22 funciones.
- 197 métodos.
- 192 clases.

Esto reproduce el aviso de “más de 300”, pero **grado cero no equivale a código
muerto confirmado**.

## Falsos positivos observados

- Callbacks usados por SQLAlchemy como `default=_utcnow` y `default=_uuid`.
- Validadores y modelos descubiertos por Pydantic mediante decoradores.
- Dependencias y handlers registrados dinámicamente por FastAPI.
- Métodos mágicos (`__init__`, `__eq__`) invocados por el runtime.
- Enums, Protocols y contratos consumidos por reflexión, anotaciones o fases
  futuras explícitamente deshabilitadas.

Por eso no se eliminó ningún símbolo sólo por la métrica. Hacerlo habría podido
romper migraciones, defaults ORM, OpenAPI o contratos reservados.

## Hallazgos reales corregidos

- Los marcadores RBAC/step-up/CSRF no tenían consumidor de enforcement.
- Faltaban los 22 permisos del router en el catálogo.
- El payload HTTP podía incluir `base_quantity` aunque se documentaba como
  server-derived.
- Faltaban registry/ingestion/line service explícitos y adaptadores futuros
  deshabilitados.
- Los jobs declaraban éxito antes de publicar y confundían IDs de dominio con
  `inventory_positions`.
- `detect_missing_movements` retornaba eventos ya materializados.
- Alembic tenía dos heads y la migración no preservaba físicamente la tabla
  legacy antes de crear `inventory_movements`.

## Criterio de limpieza futura

Un candidato sólo puede eliminarse si se confirman simultáneamente: cero uso
estático, cero registro/reflexión/framework, ausencia de contrato público o de
migración, pruebas de import/OpenAPI y pruebas funcionales del consumidor. El
conteo del grafo se conserva como señal de auditoría, no como lista automática
de borrado.
