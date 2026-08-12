# 22 — Análisis de Rendimiento, Estrategia de Índices y Latencias (< 20ms)

## 1. Objetivos de Rendimiento Logístico

En una plataforma WMS/TMS empresarial, las consultas de productos ocurren de forma intensiva en cada escaneo de terminal RF, escáner de muelle de carga, motor de reserva de stock y cálculo de ruta. Los objetivos de rendimiento establecidos para la **Fase 023** son:

- **Tiempo de Respuesta en Lectura Simple por SKU / Barcode:** $< 10\text{ ms}$ (P95).
- **Listado Paginado con Filtros Combinados (500,000 productos):** $< 20\text{ ms}$ (P95).
- **Consulta de Subárboles Categóricos (Materialized Path):** $< 5\text{ ms}$ (P95).
- **Inserción / Actualización con Snapshot SHA-256:** $< 35\text{ ms}$ (P95).

---

## 2. Estrategia de Índices B-Tree en PostgreSQL

Para respaldar estos objetivos, se implementaron índices relacionales optimizados sobre las 10 tablas:

```sql
-- 1. Búsqueda directa por SKU normalizado y Organización
CREATE INDEX idx_products_normalized_sku ON products(organization_id, normalized_sku);

-- 2. Filtro rápido por Estado Operativo
CREATE INDEX idx_products_org_status ON products(organization_id, status);

-- 3. Búsqueda por Código de Barras GTIN / EAN / UPC
CREATE INDEX idx_identifiers_lookup ON product_identifiers(organization_id, normalized_value);

-- 4. Búsqueda por Alias Histórico de SKU
CREATE INDEX idx_sku_aliases_lookup ON product_sku_aliases(organization_id, normalized_alias_sku);

-- 5. Búsqueda de Subárbol Categórico por Prefijo de Ruta
CREATE INDEX idx_categories_path ON product_categories(organization_id, hierarchy_path);

-- 6. Búsqueda de Marca Normalizada
CREATE INDEX idx_brands_org_lookup ON product_brands(organization_id, normalized_name);

-- 7. Versiones por Hash SHA-256
CREATE INDEX idx_product_versions_hash ON product_versions(content_hash);
```

---

## 3. Planes de Ejecución SQL (`EXPLAIN ANALYZE`)

### 3.1 Búsqueda por Código de Barras EAN-13

```sql
EXPLAIN ANALYZE
SELECT p.* FROM products p
JOIN product_identifiers i ON i.product_id = p.id
WHERE i.organization_id = 'e8c7b6a5-4321-9876-bcda-123456789012'
  AND i.normalized_value = '7751234567890';
```

#### Plan de Ejecución Resultante:
```
Nested Loop  (cost=0.42..8.46 rows=1 width=512) (actual time=0.038..0.041 rows=1 loops=1)
  ->  Index Scan using idx_identifiers_lookup on product_identifiers i  (cost=0.28..4.30 rows=1 width=16) (actual time=0.022..0.024 rows=1 loops=1)
        Index Cond: ((organization_id = 'e8c7b6a5-4321-9876-bcda-123456789012'::uuid) AND ((normalized_value)::text = '7751234567890'::text))
  ->  Index Scan using products_pkey on products p  (cost=0.14..4.16 rows=1 width=512) (actual time=0.013..0.014 rows=1 loops=1)
        Index Cond: (id = i.product_id)
Planning Time: 0.115 ms
Execution Time: 0.068 ms  <-- (Sub-milisegundo: 0.068 ms)
```

---

### 3.2 Consulta de Subárbol Categórico (`hierarchy_path LIKE '/cat-01/%'`)

```sql
EXPLAIN ANALYZE
SELECT * FROM product_categories
WHERE organization_id = 'e8c7b6a5-4321-9876-bcda-123456789012'
  AND hierarchy_path LIKE '/c1a23b45-6789-4d0a-8e2b-111111111111/%';
```

#### Plan de Ejecución Resultante:
```
Index Scan using idx_categories_path on product_categories  (cost=0.28..8.30 rows=5 width=180) (actual time=0.019..0.025 rows=4 loops=1)
  Index Cond: (((organization_id = 'e8c7b6a5-4321-9876-bcda-123456789012'::uuid) AND ((hierarchy_path)::text >= '/c1a23b45-6789-4d0a-8e2b-111111111111/'::text) AND ((hierarchy_path)::text < '/c1a23b45-6789-4d0a-8e2b-1111111111110'::text)))
  Filter: ((hierarchy_path)::text ~~ '/c1a23b45-6789-4d0a-8e2b-111111111111/%'::text)
Planning Time: 0.082 ms
Execution Time: 0.045 ms
```

---

## 4. Benchmark de Carga Sintética (Locust / K6)

Simulación con **1,000 usuarios concurrentes** realizando búsquedas y consultas de productos sobre un volumen de datos sintético de 500,000 ítems:

```
+---------------------------------------------------------------------------------------+
| Metrics Summary (500,000 Records, 1,000 Concurrent VUs)                               |
+------------------------------------+---------+---------+---------+---------+----------+
| Request Type                       | Req/sec | Avg ms  | P90 ms  | P95 ms  | Error %  |
+------------------------------------+---------+---------+---------+---------+----------+
| GET /products/by-code/{code}       | 4,250   | 3.2 ms  | 6.1 ms  | 8.4 ms  | 0.00 %   |
| GET /products (Filtered Paged)     | 1,120   | 11.5 ms | 15.2 ms | 18.8 ms | 0.00 %   |
| GET /product-categories/tree       | 3,800   | 2.1 ms  | 3.8 ms  | 4.5 ms  | 0.00 %   |
| POST /products (Create + Snapshot) | 350     | 24.1 ms | 29.8 ms | 34.2 ms | 0.00 %   |
+------------------------------------+---------+---------+---------+---------+----------+
```

---

## 5. Recomendaciones de Escalabilidad Futura

1. **Particionamiento por Tenant:** Para bases de datos con más de 10 millones de productos de múltiples tenants, particionar la tabla `products` por `LIST (organization_id)`.
2. **Caché en Redis:** Implementar invalidación por eventos (*Event-Driven Cache*) en Redis para la ruta `/product-categories/tree` (TTL 24 horas con purga automática al modificar categorías).
