# 07. Router Logístico

## Registro

El router se registra en `app/api/router.py`:

```python
from app.modules.logistics import create_logistics_router
logistics_router = create_logistics_router()
api_router.include_router(logistics_router)
```

## Prefijos

- `settings.API_PREFIX` = `/api` (config existente)
- Router logístico: `prefix="/logistics"`
- Resultado: `/api/logistics/...`

No hay duplicación de `/api/api/logistics`.

## Tags OpenAPI

- `Logistics` — router raíz
- `Logistics · Documents` — submódulo documentos
- `Logistics · Routes` — submódulo rutas
- `Logistics · Files` — submódulo archivos
- `Logistics · Audit` — submódulo auditoría
- `Logistics · Integrations` — submódulo integraciones

## Endpoints técnicos

| Método | Path | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/logistics/health` | Estado del dominio logístico | Requerida |
| GET | `/api/logistics/documents/` | Estado del submódulo documentos | Requerida |
| GET | `/api/logistics/routes/` | Estado del submódulo rutas | Requerida |
| GET | `/api/logistics/files/` | Estado del submódulo archivos | Requerida |
| GET | `/api/logistics/audit/` | Estado del submódulo auditoría | Requerida |
| GET | `/api/logistics/integrations/` | Estado del submódulo integraciones | Requerida |