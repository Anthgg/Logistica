# F004 · Auditoría de escritores en `warehouses`

Objetivo: que ningún camino de escritura activo pueda crear almacenes huérfanos.

## Antes

| WRITER | ROUTE | SETS_BRANCH_ID | SETS_ORGANIZATION_ID | CAN_CREATE_ORPHAN | OWNER_PHASE |
|---|---|---|---|---|---|
| `organization/service.py::LogisticsWarehouseService.create` | `POST /api/logistics/branches/{id}/warehouses` | sí | **no** | **SÍ** | F004 |
| `warehouses/warehouse_service.py::create_warehouse` | `POST /api/logistics/warehouses` | sí | sí | no | F022 |
| `services/warehouse_service.py::create` | `POST /api/warehouses` | **no** | **no** | **SÍ** | legado |
| `scripts/seed_logistics.py` | — | **no** | **no** | **SÍ** | dev tooling |
| Tests (`phase022`, `phase036`, `phase037`, `pdf_download_audit`) | — | variable | variable | sí | fases propias |

## Después

| WRITER | ROUTE | SETS_BRANCH_ID | SETS_ORGANIZATION_ID | CAN_CREATE_ORPHAN | OWNER_PHASE |
|---|---|---|---|---|---|
| `organization/service.py::LogisticsWarehouseService.create` | `POST /api/logistics/branches/{id}/warehouses` | sí | **sí, derivado de `branch.organization_id`** | **no** | F004 |
| `warehouses/warehouse_service.py::create_warehouse` | `POST /api/logistics/warehouses` | sí | sí | no | F022 — sin tocar |
| `services/warehouse_service.py::create` | `POST /api/warehouses` | **sí, `branch_id` ahora obligatorio** | **sí, derivado** | **no** | legado |
| `scripts/seed_logistics.py` | — | **sí** | **sí** | **no** | dev tooling |
| Tests | — | variable | variable | sí | fases propias |

Los tests siguen pudiendo construir filas arbitrarias con el ORM: son datos de
laboratorio en base de test aislada, no un camino de escritura de producción.

## Cambio de contrato en el legado

`POST /api/warehouses` pasa a exigir `branch_id`. Es un cambio incompatible y se
declara como tal:

- **No hay consumidor en el frontend.** De ese cliente solo se usa `list`, en
  `InventoryPage.tsx:46`. `create`, `update` y `remove` no los llama nadie.
- El único consumidor era `tests/test_inventory.py`, adaptado para crear
  organización y sede primero mediante el helper `create_organization_branch`.
- La alternativa —dejarlo crear huérfanos— contradice el objetivo de la fase.

`WarehouseRead` declara además `branch_id`, `organization_id` y los campos de
dirección como opcionales: heredaba de `WarehouseCreate`, y con `branch_id`
obligatorio el listado de las 3 filas heredadas habría reventado con un 500 de
serialización.

## Filas huérfanas existentes

Ver [database-audit.md](database-audit.md). No se reparan por intuición: no hay
evidencia de a qué organización pertenecen.

| WAREHOUSE_ID | CODE | NAME | CURRENT_ORG | CURRENT_BRANCH | EVIDENCE_FOR_MAPPING | PROPOSED_MAPPING | CONFIDENCE |
|---|---|---|---|---|---|---|---|
| `0b69d6fb-022a-4beb-aab0-5abfca9c6496` | DEMO-LIM | Almacén Demo Lima | NULL | NULL | `is_demo=true`; 7 `inventory_items` de demo; 0 documentos, 0 avisos, 0 asignaciones de rol; creado por `seed_logistics.py` sin organización | ninguno | — |
| `f52867b9-68f4-4c15-802f-9cff9680b9ea` | DEMO-AQP | Almacén Demo Arequipa | NULL | NULL | idem, 7 items | ninguno | — |
| `ea9e4931-491b-4ce8-97e9-359f243c7634` | DEMO-TRU | Almacén Demo Trujillo | NULL | NULL | idem, 6 items | ninguno | — |

Clasificación: **`LEGACY_ORPHAN_REQUIRES_DATA_DECISION`**.

Consecuencia deliberada: `warehouses.organization_id` y `warehouses.branch_id`
**siguen siendo nullable**. Ponerlas NOT NULL exigiría inventar una organización
para estas filas. La deuda queda registrada; las escrituras nuevas ya no la amplían.

Estos tres almacenes son invisibles para `GET /api/logistics/warehouses`, que filtra
por organización, y para la superficie estructural, que lista por sede. Esa
invisibilidad es correcta mientras no pertenezcan a ningún tenant: la alternativa
sería exponerlos a todo el mundo.

## Restricción de unicidad

`warehouses.code` tiene un índice **UNIQUE global** y además existe
`uq_warehouses_branch_code (branch_id, code)`. La global es más estricta y hace
redundante a la otra: el código de almacén es único en todo el sistema, no por sede.

No se elimina ninguna de las dos: no hay evidencia de cuál refleja la regla de
dominio pretendida, y quitar la global podría romper consumidores que asumen
códigos únicos. Para la UAT hay que usar un código globalmente único, por ejemplo
`UAT-F004-WH-001`.

## Consistencia de `status` e `is_active`

`warehouses` guarda las dos. El módulo F022 escribe `status` (texto en mayúsculas),
la estructura F004 escribía solo `is_active`, así que una fila podía quedar diciendo
`status='ACTIVE'` e `is_active=false` a la vez.

Arreglo mínimo: `LogisticsWarehouseRepository.set_active` escribe ambas. No se
rediseña el modelo de estado de F022. Test:
`test_warehouse_status_keeps_status_and_is_active_consistent`.
