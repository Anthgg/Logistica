# 38. Endpoints

El OpenAPI efectivo contiene las 86 declaraciones HTTP exigidas por el contrato, sin faltantes. Los grupos canónicos son `/warehouse-docks`, `/inbound-dock-queue`, `/dock-assignment-plans`, `/inbound-dock-assignments`, `/unloading-operations`, pausas, métricas y `/dock-operation-exports`.

Todos los POST/PATCH de Fase 038 requieren CSRF e `Idempotency-Key`; los contratos rechazan campos extra.
