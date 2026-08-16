# F004 · Auditoría PostgreSQL

Base inspeccionada en solo lectura: `continuous_authentication` (desarrollo).

## Tablas reales

| Entidad | Tabla | Modelo |
|---|---|---|
| Organización | `logistics_organizations` | `app/models/organization.py` |
| Sede | `logistics_branches` | `app/models/branch.py` |
| Almacén | `warehouses` | `app/models/warehouse.py` |

## `logistics_organizations`

PK `id uuid`. `code varchar(30)` NOT NULL con índice **único** global.
`name`, `country_code varchar(2)`, `timezone varchar(50)`, `status varchar(20)` NOT NULL.
Auditoría: `created_by`, `updated_by`, `created_at`, `updated_at`.
Índices: `ix_logistics_organizations_code` (UNIQUE), `ix_logistics_organizations_status`.
Referenciada por ~40 tablas del dominio con `ON DELETE RESTRICT`.

Sin borrado lógico: el estado vive en `status ('active'|'inactive')`. 120 filas, todas `active`.

## `logistics_branches`

PK `id`. FK `organization_id → logistics_organizations.id ON DELETE RESTRICT`, NOT NULL, indexada.
`UNIQUE (organization_id, code)` = `uq_branches_org_code` — el código de sede es único
por organización, no globalmente. Correcto.
`latitude/longitude numeric(10,7)`, `address_text varchar(500)`, `status` indexado.
114 filas, todas `active`.

## `warehouses`

PK `id`. Dos FKs estructurales, **ambas nullable**:

- `organization_id → logistics_organizations.id ON DELETE RESTRICT`
- `branch_id → logistics_branches.id ON DELETE RESTRICT`

Constraints: `ix_warehouses_code` **UNIQUE global** sobre `code`, y además
`uq_warehouses_branch_code UNIQUE (branch_id, code)`. La primera hace redundante a la
segunda y es más estricta de lo que el dominio parece querer (dos sedes no pueden
reutilizar el mismo código de almacén).

Doble representación de estado: `status varchar(20) NOT NULL DEFAULT 'ACTIVE'` **y**
`is_active boolean NOT NULL DEFAULT true`. Nada las mantiene sincronizadas: el módulo
`organization` escribe `is_active`, el módulo `warehouses` escribe `status`.

3 filas: `DEMO-LIM`, `DEMO-AQP`, `DEMO-TRU`.

## Drift 1 — `server_default` con comillas dobles

`alembic/versions/a2f27fd9a6c0_add_logistics_organizations_branches.py` declara los
defaults como cadenas Python que ya contienen comillas:

```python
sa.Column("status", sa.String(20), nullable=False, server_default="'active'", index=True)
sa.Column("timezone", sa.String(50), nullable=False, server_default="'America/Lima'")
sa.Column("warehouse_type", ..., nullable=False, server_default="'general'")
```

SQLAlchemy vuelve a citarlas, así que el DDL emitido es `DEFAULT '''active'''`. Es lo que
tiene la base hoy:

```
status        | ... | not null | '''active'''::character varying
timezone      | ... | not null | '''America/Lima'''::character varying
warehouse_type| ... | not null | '''general'''::character varying
```

Los modelos usan `server_default=text("'active'")`, que es la forma correcta → **drift real**
entre modelo y esquema.

En organizaciones y sedes el fallo está latente: el `default=` de Python del ORM siempre
aporta el valor, así que el default del servidor no llega a usarse y los datos están limpios.

En `warehouses` **sí llegó a activarse**. Las 3 filas existentes tienen:

```
DEMO-LIM | type= "'general'" | org= None | branch= None | status= ACTIVE | is_active= True
DEMO-AQP | type= "'general'" | org= None | branch= None | status= ACTIVE | is_active= True
DEMO-TRU | type= "'general'" | org= None | branch= None | status= ACTIVE | is_active= True
```

`warehouse_type` contiene literalmente `'general'`, apóstrofos incluidos. Ese valor no
pertenece al conjunto permitido por `LogisticsWarehouseCreate.normalize_type`
(`{"general","receiving",...}`) ni al `warehouse_type.upper()` con que filtra
`WarehouseService.list_warehouses`.

## Drift 2 — almacenes huérfanos de organización

Las 3 filas tienen `organization_id = NULL` y `branch_id = NULL`.

`WarehouseService.list_warehouses` filtra con
`Warehouse.organization_id == organization_id`. Con `NULL`, la comparación nunca es
verdadera. Verificado en vivo con un principal de la organización que sí tiene sedes:

```
GET /api/logistics/warehouses -> 200   BODY: []
GET /api/logistics/warehouses/0b69d6fb-... -> 404 RESOURCE_NOT_FOUND
```

Los tres almacenes existen en la tabla y son invisibles para toda la API.

## Drift 3 — la creación estructural perpetúa el huérfano

`LogisticsWarehouseService.create` (`organization/service.py`) inserta con `branch_id`
pero **nunca asigna `organization_id`**, y tampoco `created_by`/`updated_by`. Todo almacén
creado por la ruta estructural F004 nace invisible para `GET /logistics/warehouses`.

## Integridad de relaciones

| Relación | Definida | Aplicada en datos |
|---|---|---|
| Branch → Organization | FK NOT NULL, RESTRICT | sí, 114/114 |
| Warehouse → Branch | FK nullable, RESTRICT | **no**, 0/3 |
| Warehouse → Organization | FK nullable, RESTRICT | **no**, 0/3 |

El dominio sí define las tres relaciones; los datos y el camino de escritura no las honran.

## Migraciones

59 revisiones. Tres relevantes: `a2f27fd9a6c0` (organizaciones y sedes),
`m240110022dc` (fase 022 warehouses/locations), `u310110030dc` (address opcional).
Aparte del drift de `server_default` descrito arriba, el esquema físico coincide con los
modelos. **No hace falta una migración vacía**; sí hace falta una que corrija los defaults
y decida el destino de `organization_id`.

## Conteos (solo lectura, sin cambios)

```
logistics_organizations = 120
logistics_branches      = 114
warehouses              =   3
```
