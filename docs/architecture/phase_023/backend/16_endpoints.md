# 16 — Especificación OpenAPI/REST de Endpoints

## 1. Catálogo General de Rutas de la Fase 023

Todos los endpoints de la Fase 023 están expuestos bajo el prefijo `/api/logistics/` y requieren autenticación Bearer JWT multi-tenant.

| Método HTTP | Ruta | Descripción | Requiere Step-Up |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/logistics/products` | Crear un nuevo producto en estado `DRAFT` o `ACTIVE`. | No |
| **GET** | `/api/logistics/products` | Listar productos con búsqueda y filtros combinados. | No |
| **GET** | `/api/logistics/products/{id}` | Obtener detalle completo de un producto por UUID. | No |
| **GET** | `/api/logistics/products/by-code/{code}` | Buscar producto por SKU, SKU Alias o Barcode. | No |
| **PUT** | `/api/logistics/products/{id}` | Actualizar datos principales con control optimista (`row_version`). | No |
| **PATCH** | `/api/logistics/products/{id}/status` | Cambiar estado operativo del ciclo de vida. | **Sí** |
| **PATCH** | `/api/logistics/products/{id}/rename-sku` | Renombrar SKU activo y crear alias histórico. | **Sí** |
| **GET** | `/api/logistics/products/{id}/versions` | Listar snapshots inmutables de versión (SHA-256). | No |
| **POST** | `/api/logistics/products/{id}/evaluate-location-compatibility` | Evaluar compatibilidad cualitativa con ubicación (Fase 022). | No |
| **DELETE** | `/api/logistics/products/{id}` | Archivar o eliminar lógicamente un producto. | **Sí** |
| **POST** | `/api/logistics/product-categories` | Crear una categoría jerárquica. | No |
| **GET** | `/api/logistics/product-categories` | Listar categorías planas. | No |
| **GET** | `/api/logistics/product-categories/tree` | Obtener árbol jerárquico anidado (`depth <= 5`). | No |
| **POST** | `/api/logistics/product-brands` | Crear una marca comercial. | No |
| **GET** | `/api/logistics/product-brands` | Listar marcas comerciales de la organización. | No |
| **POST** | `/api/logistics/product-identifiers` | Asignar código de barras GTIN/EAN/UPC o interno. | No |
| **GET** | `/api/logistics/product-identifiers/{id}/barcode-image` | Descargar imagen PNG del código de barras. | No |

---

## 2. Detalle de Endpoints Principales

### 2.1 `POST /api/logistics/products`
Crea una nueva entidad de producto en el catálogo.

#### Request Body (`ProductCreateSchema`):
```json
{
  "sku": "PROD-MONITOR-4K",
  "name": "Monitor Profesional 27'' 4K HDR",
  "description": "Panel IPS 144Hz para estación de diseño gráfico",
  "product_type": "FINISHED_GOOD",
  "category_id": "c2b34c56-7890-4e1b-9f3c-222222222222",
  "brand_id": "b1a23b45-6789-4d0a-8e2b-999999999999",
  "base_unit_code": "UND",
  "is_hazmat": false,
  "requires_cold_chain": false,
  "is_fragile": true,
  "physical_profile": {
    "net_weight_kg": 6.5000,
    "gross_weight_kg": 8.2000,
    "length_cm": 65.0000,
    "width_cm": 20.0000,
    "height_cm": 45.0000,
    "is_stackable": true,
    "max_stacking_layers": 4
  },
  "tracking_policy": {
    "tracking_mode": "SERIAL",
    "requires_serial_on_receipt": true,
    "requires_serial_on_dispatch": true
  },
  "storage_condition": {
    "min_temperature_celsius": 10.00,
    "max_temperature_celsius": 30.00,
    "severity": "HARD_BLOCK"
  }
}
```

#### Response 201 Created (`ProductDetailSchema`):
```json
{
  "id": "e9f8a7b6-5432-10fe-dcba-9876543210fe",
  "sku": "PROD-MONITOR-4K",
  "normalized_sku": "PROD-MONITOR-4K",
  "name": "Monitor Profesional 27'' 4K HDR",
  "status": "DRAFT",
  "base_unit_code": "UND",
  "row_version": 1,
  "created_at": "2026-07-28T12:00:00Z"
}
```

---

### 2.2 `PATCH /api/logistics/products/{id}/rename-sku`
Renombra un SKU de forma segura preservando trazabilidad mediante un alias histórico en `product_sku_aliases`.

#### Headers:
`X-Step-Up-Token: stepup_sec_token_9988776655`

#### Request Body:
```json
{
  "new_sku": "PROD-MONITOR-27-HDR",
  "reason": "Reestructuración comercial de nomenclaturas 2026"
}
```

#### Response 200 OK:
```json
{
  "id": "e9f8a7b6-5432-10fe-dcba-9876543210fe",
  "previous_sku": "PROD-MONITOR-4K",
  "new_sku": "PROD-MONITOR-27-HDR",
  "normalized_sku": "PROD-MONITOR-27-HDR",
  "alias_created": true,
  "row_version": 2
}
```

---

### 2.3 `POST /api/logistics/product-identifiers`
Registra un identificador barcode (GTIN-13/EAN-13, GTIN-12/UPC, etc.) o genera un código interno.

#### Request Body:
```json
{
  "product_id": "e9f8a7b6-5432-10fe-dcba-9876543210fe",
  "identifier_type": "GTIN_13",
  "raw_value": "7751234567890",
  "is_primary": true,
  "description": "EAN-13 de empaque de venta unitaria"
}
```

#### Response 201 Created:
```json
{
  "id": "11223344-5566-7788-9900-aabbccddeeff",
  "product_id": "e9f8a7b6-5432-10fe-dcba-9876543210fe",
  "identifier_type": "GTIN_13",
  "raw_value": "7751234567890",
  "normalized_value": "7751234567890",
  "is_primary": true,
  "created_at": "2026-07-28T12:05:00Z"
}
```

---

### 2.4 `POST /api/logistics/product-categories`
Crea una categoría en la jerarquía.

#### Request Body:
```json
{
  "code": "CAT-ACCESSORIES",
  "name": "Accesorios de Cómputo",
  "parent_id": "c1a23b45-6789-4d0a-8e2b-111111111111",
  "description": "Cables, adaptadores y periféricos"
}
```

#### Response 201 Created:
```json
{
  "id": "33445566-7788-9900-aabb-ccddeeff1122",
  "code": "CAT-ACCESSORIES",
  "name": "Accesorios de Cómputo",
  "depth": 2,
  "hierarchy_path": "/c1a23b45-6789-4d0a-8e2b-111111111111/33445566-7788-9900-aabb-ccddeeff1122/",
  "is_active": true
}
```
