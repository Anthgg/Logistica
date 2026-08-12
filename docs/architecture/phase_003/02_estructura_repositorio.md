# 02. Estructura de Repositorio

## Árbol implementado

```
app/modules/logistics/
├── __init__.py              # Entry point: create_logistics_router()
├── router.py                # Router raíz /logistics + health endpoint
├── constants.py             # Permisos, módulos, fase
├── exceptions.py            # Excepciones de dominio
├── dependencies.py          # Adaptadores de autenticación
├── shared/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── documents/
│   ├── api/router.py        # Status endpoint
│   ├── application/services.py  # Service contracts
│   ├── domain/contracts.py  # Protocols: Renderer, Storage, NumberGenerator, etc.
│   └── infrastructure/
├── routes_module/
│   ├── api/router.py        # Status endpoint
│   ├── application/
│   ├── domain/contracts.py  # Protocols: DirectionsProvider, GeocodingProvider, etc.
│   └── infrastructure/
├── files/
│   ├── api/router.py        # Status endpoint
│   ├── application/
│   ├── domain/contracts.py  # Protocols: FileStorage, FileValidator, etc.
│   └── infrastructure/
├── audit/
│   ├── api/router.py        # Status endpoint
│   ├── application/
│   ├── domain/contracts.py  # Protocols: AuditEventWriter, AuditEventReader, etc.
│   └── infrastructure/
└── integrations/
    ├── api/router.py        # Status endpoint
    ├── application/
    ├── domain/contracts.py  # Protocols: IntegrationAdapter, IntegrationRegistry, etc.
    └── infrastructure/
```

## Diferencias respecto a la propuesta inicial

- Se usó `routes_module/` en vez de `routes/` para evitar conflicto con el `logistics_routes.py` existente.
- `shared/` se mantiene vacío en esta fase — se poblará cuando haya utilidades comunes reales.
- Las capas `infrastructure/` están vacías — se implementarán en fases posteriores con proveedores concretos.