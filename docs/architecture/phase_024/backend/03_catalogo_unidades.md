# 03. Maestro de Unidades de Medida (`UnitOfMeasureModel`)

## 1. Especificación del Modelo `UnitOfMeasureModel`

El modelo `UnitOfMeasureModel` almacena el catálogo maestro de unidades de medida del sistema. Soporta aislamiento multitenant por organización y unidades globales del sistema.

### DDL / Esquema de Base de Datos (`units_of_measure`)

```sql
CREATE TYPE uom_scope_enum AS ENUM ('SYSTEM', 'ORGANIZATION');
CREATE TYPE uom_kind_enum AS ENUM ('BASE', 'DERIVED', 'PACKAGING', 'CUSTOM');

CREATE TABLE units_of_measure (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    dimension_id UUID NOT NULL REFERENCES measurement_dimensions(id) ON DELETE RESTRICT,
    code VARCHAR(32) NOT NULL,
    name VARCHAR(128) NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    scope uom_scope_enum NOT NULL DEFAULT 'ORGANIZATION',
    kind uom_kind_enum NOT NULL DEFAULT 'CUSTOM',
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    row_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_units_code_scope UNIQUE (organization_id, code)
);

CREATE INDEX idx_units_dimension ON units_of_measure(dimension_id);
CREATE INDEX idx_units_org_scope ON units_of_measure(organization_id, scope);
```

---

## 2. Tipología y Scopes

### Scopes (`scope`):
- **`SYSTEM`**: Unidades estándar globales (ej. `UND`, `KG`, `G`, `M`, `CM`, `M2`, `M3`, `L`). Visibles para todas las organizaciones. Tienen `organization_id = NULL`.
- **`ORGANIZATION`**: Unidades creadas por un tenant específico para sus operaciones particulares (ej. `TAMBOR_55GAL`, `JABUCO_20KG`).

### Kinds (`kind`):
- **`BASE`**: La unidad canónica fundamental de la dimensión (ej. `UND` en `COUNT`, `KG` en `MASS`).
- **`DERIVED`**: Unidad derivada de la base mediante un factor físico constante (ej. `G` = $0.001\text{ KG}$, `CM` = $0.01\text{ M}$).
- **`PACKAGING`**: Unidad genérica de empaque comercial (ej. `PALLET`, `CAJA`, `PAQUETE`, `DISPLAY`).
- **`CUSTOM`**: Unidad personalizada por cliente para procesos no estandarizados.

---

## 3. Códigos Normalizados y Política de No Eliminación Física

1. **Normalización ISO/UNECE**:
   - Los códigos deben ser en mayúsculas sin espacios (`^[A-Z0-9_]{2,32}$`).
   - Símbolos normalizados según Sistema Internacional (ej. `kg`, `g`, `m`, `m²`, `m³`, `L`, `ud`).
2. **Política de Eliminación Lógica (Soft-Delete)**:
   - **Queda estrictamente prohibida la eliminación física (`DELETE`)** de registros en `units_of_measure` si la unidad ha sido utilizada en transacciones de inventario, reglas de conversión o configuraciones de producto.
   - La desactivación se realiza mediante `is_active = false`. El motor de conversión rechaza nuevas transacciones con unidades inactivas pero permite consultar históricos.
