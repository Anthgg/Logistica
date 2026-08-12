# 14. Control de Vigencias Temporales y Snapshots Versionados (`UnitOfMeasureVersionModel`)

## 1. Control de Vigencia Temporal (`effective_from` / `effective_to`)

Las reglas de conversión física y empaques comerciales no son inmutables a lo largo del tiempo. Un proveedor puede rediseñar una caja para que contenga 30 unidades en lugar de 24.

Para preservar la integridad histórica de transacciones pasadas sin romper nuevos procesos, el modelo utiliza un esquema de **Temporal Validity (Vigencia Bitemporal)**:

- `effective_from` (`TIMESTAMP WITH TIME ZONE`): Fecha/hora exacta a partir de la cual entra en vigor la regla.
- `effective_to` (`TIMESTAMP WITH TIME ZONE`): Fecha/hora exacta hasta la cual fue válida la regla (`NULL` representa vigencia activa indefinida).

### Regla de Desactivación por Superposición:
Cuando se crea una nueva versión de regla para un par de unidades, el sistema ejecuta una transacción atómica:
1. Actualiza la regla previa: `effective_to = CURRENT_TIMESTAMP`.
2. Inserta la nueva regla con `effective_from = CURRENT_TIMESTAMP` y `effective_to = NULL`.

---

## 2. Modelo de Versionado Inmutable (`UnitOfMeasureVersionModel`)

Para garantizar auditorías forenses a nivel de base de datos, cada modificación relevante sobre una unidad o regla genera un snapshot inmutable serializado en la tabla `unit_of_measure_versions`.

### DDL / Esquema de Base de Datos (`unit_of_measure_versions`)

```sql
CREATE TABLE unit_of_measure_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id UUID NOT NULL REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    version_number INTEGER NOT NULL,
    snapshot_data JSONB NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    created_by_user_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_unit_version_number UNIQUE (unit_id, version_number)
);

CREATE INDEX idx_unit_versions_unit ON unit_of_measure_versions(unit_id);
```

---

## 3. Algoritmo de Generación de Checksum SHA-256

El servicio `UnitVersioningService` calcula la firma digital SHA-256 del payload serializado JSONB antes de insertarlo:

```python
import hashlib
import json

def create_version_snapshot(db, unit_model, user_id: UUID) -> UnitOfMeasureVersionModel:
    next_version = get_next_version_number(db, unit_model.id)
    
    snapshot = {
        "id": str(unit_model.id),
        "code": unit_model.code,
        "name": unit_model.name,
        "symbol": unit_model.symbol,
        "dimension_code": unit_model.dimension.code,
        "scope": unit_model.scope,
        "kind": unit_model.kind,
        "is_active": unit_model.is_active,
        "version_number": next_version
    }
    
    canonical_json = json.dumps(snapshot, sort_keys=True)
    checksum = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    
    version_entry = UnitOfMeasureVersionModel(
        unit_id=unit_model.id,
        version_number=next_version,
        snapshot_data=snapshot,
        checksum_sha256=checksum,
        created_by_user_id=user_id
    )
    db.add(version_entry)
    return version_entry
```
