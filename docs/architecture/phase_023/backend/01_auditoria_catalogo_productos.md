# 01 — Auditoría del Catálogo de Productos y Justificación Arquitectónica

## 1. Contexto y Auditoría del Estado Previo

Antes del diseño e implementación de la **Fase 023**, se ejecutó una inspección exhaustiva de la base de código y del esquema de base de datos relacional para verificar la existencia de entidades o modelos relacionados con productos, artículos, materiales o maestros de inventario.

### Hallazgos de la Auditoría:
1. **Modelos Existentes:** Las fases previas (Fase 001 a 022) cubren la arquitectura base de Autenticación, Usuarios, Organizaciones, Tenants, RBAC, Auditoría Base, Logística de Almacenes y Ubicaciones (`Warehouse`, `WarehouseLocationModel`).
2. **Duplicación de ORM:** **Cero (0) modelos ORM preexistentes** para productos, ítems, SKUs o categorías. No existían tablas `products`, `items`, `skus` ni esquemas preliminares en Alembic.
3. **Referencias Cruzadas:** Ciertas tablas de trazabilidad y ubicaciones (Fase 022) contaban con comentarios o campos reservados `product_id UUID NULL` sin claves foráneas activas ni restricciones habilitadas, explícitamente marcados como dependencias futuras de la Fase 023.

---

## 2. Justificación de la Arquitectura de 10 Tablas Específicas

Para evitar el antipatrón de **"God Entity"** (donde la tabla `products` contendría 80+ columnas mezclando lógica fiscal, física, de vencimiento, almacenamiento y logística), se diseñó un modelo altamente cohesionado y desacoplado compuesto por **10 tablas bien delimitadas**:

```
+-----------------------------------------------------------------------------------+
|                                 ORGANIZATION (Tenant)                             |
+-----------------------------------------------------------------------------------+
                                          |
    +-------------------------------------+-----------------------------------+
    |                                     |                                   |
+---+------------------+        +---------+------------+             +--------+-----------+
|    product_brands    |        | product_categories   |             |     products      |
| (Maestro de Marcas)  |        | (Árbol Jerárquico)   |             | (Entidad Principal)|
+----------------------+        +----------------------+             +--------+-----------+
                                                                              |
        +-----------------------+---------------------+-----------------------+-----------------------+
        |                       |                     |                       |                       |
+-------+---------------+ +-----+---------------+ +---+-------------------+ +---+-------------------+ +---+--------------------+
| product_sku_aliases   | | product_versions    | | product_identifiers   | |product_physical_profile| |product_tracking_policy |
|(Alias Históricos SKU) | |(Snapshots SHA-256)  | |(Barcode GTIN/EAN/UPC| | (Peso/Dimensiones/Vol)| |(Políticas Lote/Serie) |
+-----------------------+ +---------------------+ +---------------------+ +-----------------------+ +------------------------+
                                                                              |                       |
                                                                        +-----+-----------------+ +---+--------------------+
                                                                        |product_storage_condit.| |product_handling_condit.|
                                                                        |(Cadena Frío/Hazmat)   | | (Seguridad / EPP)      |
                                                                        +-----------------------+ +------------------------+
```

---

## 3. Matriz de Responsabilidad por Tabla

| # | Nombre de la Tabla | Responsabilidad Principal | Patrón de Diseño / Justificación |
|---|:---|:---|:---|
| 1 | `products` | Entidad raíz del agregador. Contiene identidad básica, SKU activo, nombre, estado operativo y control de versión optimista (`row_version`). | **Aggregate Root**. Mantener limpia la tabla primaria optimiza consultas masivas de listado. |
| 2 | `product_sku_aliases` | Registro histórico de SKUs anteriores tras operaciones de renombre o migración de codificación comercial. | **Historical Log**. Garantiza que escaneos o búsquedas por un SKU descontinuado redirijan al producto correcto. |
| 3 | `product_versions` | Snapshots inmutables JSONB con firma SHA-256 (`content_hash`) capturados en cambios estructurales. | **Event / Snapshot Pattern**. Permite auditoría forense de qué atributos tenía el producto en una fecha/hora dada. |
| 4 | `product_categories` | Estructura jerárquica tipo árbol con `hierarchy_path` (ej. `/cat-1/cat-4/`) y profundidad máxima de 5. | **Materialized Path / Closure Tree**. Búsquedas de subárboles ultra rápidas sin recurrencia pesada (`CTE`). |
| 5 | `product_brands` | Maestro comercial de marcas asociadas a la organización. | **Normalized Entity**. Evita duplicidad de nombres de marcas y facilita filtrado comercial. |
| 6 | `product_identifiers` | Identificadores globales y códigos de barras (GTIN-8, EAN-13, UPC-A, GTIN-14, Internos) con checksum Módulo 10. | **One-to-Many Identifiers**. Soporta múltiples códigos de barras por un mismo SKU (paquete, caja, pallet). |
| 7 | `product_physical_profiles` | Dimensiones (alto, ancho, largo), peso neto/bruto, y métricas volumétricas con precisión `Numeric(14,4)`. | **Value Object Separation**. Carga perezosa (*lazy load*) para operaciones donde el volumen no sea requerido. |
| 8 | `product_tracking_policies` | Reglas sobre si el producto requiere trazabilidad por Lote (`LOT`), Serie (`SERIAL`) o Ambos. | **Policy Pattern**. Desacopla la regla de trazabilidad de los lotes/series reales que se crearán en la Fase 046. |
| 9 | `product_storage_conditions` | Matriz de restricciones ambientales (temperaturas mín/máx, humedad, cadena de frío, Hazmat, frágil). | **Domain Policy**. Base fundamental para el evaluador cualitativo de ubicación de la Fase 022. |
| 10 | `product_handling_conditions` | Requerimientos operativos de manipulación (EPP obligatorios, manipulación en pareja, orientación). | **Safety & Operations**. Garantiza la protección del personal en operaciones de picking y dispatching. |

---

## 4. Garantías de Limpieza y Extensibilidad

1. **Desacoplamiento Estricto:** La entidad `products` no contiene claves foráneas hacia almacenes o stock.
2. **Compatibilidad Multi-Tenant Total:** Todas las tablas principales poseen la columna `organization_id` indexada como clave foránea contra la entidad `organizations`, asegurando aislamiento lógico a nivel de base de datos.
3. **Cero Dependencia de Terceros Inestables:** Las validaciones de checksum barcode (Módulo 10) y normalización de SKUs se resuelven mediante módulos puros en Python/PostgreSQL sin dependencias externas frágiles.
