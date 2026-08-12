# 10 — Políticas de Permisos y Sensibilidad

## Mapeo de Permisos RBAC por Tipo Documental

```mermaid
graph LR
    User[Logistics Principal] -->|Has Permission?| PermCheck{RBAC Check}
    PermCheck -->|logistics.documents.read| CatalogAPI[Get Document Catalog / Types]
    PermCheck -->|logistics.purchases.read| OC_Detail[Read OC Contract]
    PermCheck -->|logistics.integrations.configure| ValidateAPI[Validate Catalog API]
```

## Clasificación de Sensibilidad
* **`PUBLIC_LIMITED`**: Verificación pública limitada.
* **`INTERNAL`**: Uso interno ordinario.
* **`CONFIDENTIAL`**: Cuadro comparativo (CCO), Orden de compra (OC), Acta de ajuste (AJI), Hoja de ruta (HR).
* **`RESTRICTED`**: Prueba de entrega (POD), Acta parcial (EP), Acta de rechazo (RECH), Control de puerta (CPV).
