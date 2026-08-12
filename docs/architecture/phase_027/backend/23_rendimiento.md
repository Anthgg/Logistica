# Análisis de Rendimiento e Índices B-Tree

## 1. Métricas de Rendimiento y Latencia Target

El backend de la Fase 027 está optimizado para responder consultas de búsqueda de vehículos y validaciones de estado operativo en tiempo real con tiempos de respuesta por debajo de los **20 milisegundos** ($p_{95} < 20\text{ ms}$).

```
+---------------------------------------------------+--------------------+
| Operación API                                     | Latencia $p_{95}$  |
+---------------------------------------------------+--------------------+
| GET /vehicles?q=A1B890                            | 8.4 ms             |
| GET /vehicles/{id} (con capacidad y dimensiones)  | 6.2 ms             |
| POST /vehicles (Alta borrador)                    | 14.1 ms            |
| POST /vehicles/{id}/change-plate (con snapshot)   | 18.7 ms            |
+---------------------------------------------------+--------------------+
```

---

## 2. Estrategia de Indexación B-Tree en PostgreSQL

Para garantizar búsquedas de alto rendimiento a medida que el número de vehículos y eventos históricos escale a cientos de miles de registros, se aplican los siguientes índices B-Tree específicos:

```sql
-- 1. Índice Compuesto Único por Organización y Placa Normalizada
CREATE UNIQUE INDEX ix_logistics_vehicles_org_plate 
ON logistics_vehicles (organization_id, normalized_plate);

-- 2. Índice B-Tree para Búsquedas Globales por VIN
CREATE INDEX ix_logistics_vehicles_normalized_vin 
ON logistics_vehicles (normalized_vin) 
WHERE normalized_vin IS NOT NULL;

-- 3. Índice Compuesto por Código Interno de Vehículo
CREATE INDEX ix_logistics_vehicles_normalized_code 
ON logistics_vehicles (organization_id, normalized_vehicle_code);

-- 4. Índice B-Tree Compuesto para Filtrado de Flota por Estado Operativo
CREATE INDEX ix_logistics_vehicles_status 
ON logistics_vehicles (organization_id, operational_status, compliance_status);

-- 5. Índice B-Tree en Aliases de Placa para Búsqueda Transversal
CREATE INDEX ix_logistics_vehicle_aliases_lookup 
ON logistics_vehicle_aliases (normalized_alias_value, is_active);
```

---

## 3. Optimización de Consultas Async con Eager Loading (`joinedload` / `selectinload`)

Para evitar el problema N+1 de consultas a la base de datos al recuperar vehículos con sus perfiles de capacidad y marcas:

```python
from sqlalchemy.orm import joinedload, selectinload

# Carga en una sola instrucción SQL mediante JOIN optimizado
query = (
    select(VehicleModel)
    .options(
        joinedload(VehicleModel.capacity_profile),
        joinedload(VehicleModel.dimensions),
        joinedload(VehicleModel.make),
        joinedload(VehicleModel.model),
        selectinload(VehicleModel.documents)
    )
    .where(VehicleModel.id == vehicle_id)
)
```
