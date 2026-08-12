# Motor de Búsqueda y Filtrado Multicriterio

## 1. Arquitectura del Motor de Consultas (`VehicleSearchService`)

El motor de búsqueda de vehículos (`app/services/logistics/vehicle_search_service.py`) provee capacidades avanzadas de filtrado paginado, búsqueda por coincidencia parcial o exacta, ordenamiento dinámico e inclusión de relaciones clave.

Está diseñado para ofrecer tiempos de respuesta inferiores a **20 milisegundos** aprovechando los índices B-Tree en campos normalizados.

---

## 2. Parámetros de Búsqueda Soportados

| Parámetro Query | Tipo | Descripción | Campo DB Indexado |
|---|---|---|---|
| `q` | `str` | Búsqueda universal por placa, VIN, código de vehículo o alias. | `normalized_plate`, `normalized_vin`, `normalized_vehicle_code`, `normalized_alias_value` |
| `plate` | `str` | Búsqueda directa por placa exacta o prefijo. | `normalized_plate` |
| `vin` | `str` | Búsqueda por número VIN. | `normalized_vin` |
| `vehicle_code` | `str` | Búsqueda por código interno del activo. | `normalized_vehicle_code` |
| `make_id` | `UUID` | Filtro por marca de vehículo. | `make_id` |
| `model_id` | `UUID` | Filtro por modelo de vehículo. | `model_id` |
| `vehicle_type` | `Enum` | Filtro por tipo (`RIGID_TRUCK`, `SEMI_TRAILER`, etc.). | `vehicle_type` |
| `body_type` | `Enum` | Filtro por carrocería (`REFRIGERATED`, `TANKER`, etc.). | `body_type` |
| `lifecycle_status` | `Enum` | Filtro por estado de ciclo de vida (`ACTIVE`, `DRAFT`, etc.). | `lifecycle_status` |
| `operational_status`| `Enum` | Filtro por estado operativo (`AVAILABLE`, `MAINTENANCE`, etc.).| `operational_status` |
| `compliance_status` | `Enum` | Filtro por estado documental (`COMPLIANT`, `NON_COMPLIANT`, etc.).| `compliance_status` |
| `carrier_partner_id`| `UUID` | Filtro por transportista asignado (Fase 025). | `logistics_vehicle_carrier_assignments` |
| `page` | `int` | Número de página (Default: 1). | N/A |
| `page_size` | `int` | Tamaño de página (Default: 20, Máx: 100). | N/A |

---

## 3. Construcción Dinámica de la Consulta SQL (SQLAlchemy v2 Async)

```python
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

class VehicleSearchService:
    @classmethod
    async def search_vehicles(
        cls,
        db: AsyncSession,
        org_id: UUID,
        params: VehicleSearchParams
    ) -> tuple[list[VehicleModel], int]:
        
        query = select(VehicleModel).where(VehicleModel.organization_id == org_id)
        
        # 1. Búsqueda universal por término 'q'
        if params.q:
            clean_q = params.q.strip().upper().replace("-", "")
            
            # Subquery para resolver IDs por alias
            alias_subq = select(VehicleAliasModel.vehicle_id).where(
                VehicleAliasModel.normalized_alias_value.like(f"%{clean_q}%")
            )
            
            query = query.where(
                or_(
                    VehicleModel.normalized_plate.like(f"%{clean_q}%"),
                    VehicleModel.normalized_vin.like(f"%{clean_q}%"),
                    VehicleModel.normalized_vehicle_code.like(f"%{clean_q}%"),
                    VehicleModel.id.in_(alias_subq)
                )
            )
            
        # 2. Filtros exactos
        if params.vehicle_type:
            query = query.where(VehicleModel.vehicle_type == params.vehicle_type)
            
        if params.operational_status:
            query = query.where(VehicleModel.operational_status == params.operational_status)

        if params.compliance_status:
            query = query.where(VehicleModel.compliance_status == params.compliance_status)

        # 3. Conteo total para paginación
        count_query = select(func.count()).select_from(query.subquery())
        total_records = (await db.execute(count_query)).scalar_one()

        # 4. Paginación y ordenamiento
        offset = (params.page - 1) * params.page_size
        query = query.order_by(VehicleModel.created_at.desc()).offset(offset).limit(params.page_size)
        
        res = await db.execute(query)
        vehicles = res.scalars().all()
        
        return list(vehicles), total_records
```
