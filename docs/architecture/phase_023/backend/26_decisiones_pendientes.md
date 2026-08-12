# 26 — Registro de Decisiones de Arquitectura (ADRs 023-01 a 023-05)

## 1. Introducción

Este documento formaliza las Decisiones de Arquitectura de Software (**Architectural Decision Records - ADRs**) adoptadas durante el diseño e implementación del Catálogo de Productos (Fase 023).

---

## 2. ADR 023-01: Separación de Entidad de Producto en 10 Tablas Especializadas

- **Estado:** ACEPTADO.
- **Contexto:** Se requería definir la estructura de persistencia para el catálogo de productos soportando aspectos físicos, volumétricos, ambientales, térmicos, de seguridad, códigos de barras y versionado. Incluir 80+ columnas en una única tabla `products` habría creado una "God Entity" inmanejable con baja cohesión y cuellos de botella en lectura.
- **Decisión:** Descomponer el agregado en **10 tablas bien delimitadas** (`products`, `product_categories`, `product_brands`, `product_identifiers`, `product_sku_aliases`, `product_versions`, `product_physical_profiles`, `product_tracking_policies`, `product_storage_conditions`, `product_handling_conditions`).
- **Consecuencias Positivas:**
  - Consultas de listado de productos ultra-rápidas al no cargar blobs pesados de datos ambientales o de manipulación.
  - Mantenimiento modularizado y responsabilidad única por tabla.
- **Consecuencias Negativas:** Requiere `JOIN` o `selectinload` explícito en SQLAlchemy para operaciones que soliciten el perfil completo.

---

## 3. ADR 023-02: Normalización Determinística de SKU y Conservación Histórica de Alias

- **Estado:** ACEPTADO.
- **Contexto:** Al renombrar un SKU comercial, se corre el riesgo de perder trazabilidad de etiquetas de almacén previamente impresas o registros históricos de venta.
- **Decisión:** Implementar un validador `ProductSKUValidator` que remueva tildes, caracteres invisibles y espacios, junto con la tabla `product_sku_aliases`. Cada renombre guarda automáticamente el SKU anterior.
- **Consecuencias Positivas:** Garantiza que escaneos de códigos de barras descontinuados o SKUs antiguos resuelvan correctamente al producto vigente.
- **Consecuencias Negativas:** Incrementa levemente la complejidad de las consultas de búsqueda, exigiendo evaluar la tabla de alias mediante subconsultas `IN`.

---

## 4. ADR 023-03: Árbol Jerárquico de Categorías con Materialized Path y Límite de Profundidad 5

- **Estado:** ACEPTADO.
- **Contexto:** Las categorías organizacionales forman estructuras en árbol. Las consultas recursivas tipo CTE en SQL son costosas en tiempo de ejecución.
- **Decisión:** Utilizar el patrón **Materialized Path (`hierarchy_path`)** con un límite máximo de profundidad de 5 niveles e impedir determinísticamente referencias circulares en el `ProductCategoryTreeEngine`.
- **Consecuencias Positivas:** Consultar todos los descendientes de una categoría principal toma $< 5\text{ ms}$ usando un `LIKE '/path/%'` con índice B-Tree.
- **Consecuencias Negativas:** Al mover una categoría padre de ubicación en el árbol, se requiere recalcular en cascada el `hierarchy_path` de todos sus descendientes.

---

## 5. ADR 023-04: Firma SHA-256 en Snapshots Inmutables de Versión (`product_versions`)

- **Estado:** ACEPTADO.
- **Contexto:** Los auditores internos y normativos exigen demostrar la inmutabilidad histórica de las especificaciones del producto al momento de una transacción pasada.
- **Decisión:** Generar un snapshot JSONB con el digest SHA-256 (`content_hash`) en cada actualización de producto, almacenado en `product_versions` con rango de vigencia `[effective_start, effective_end)`.
- **Consecuencias Positivas:** Trazabilidad forense garantizada con firma criptográfica.
- **Consecuencias Negativas:** Mayor consumo de almacenamiento en base de datos PostgreSQL al guardar payloads JSON completos por cada versión.

---

## 6. ADR 023-05: Uso de Lista Controlada Provisional para `base_unit_code` (`PENDING_PHASE_024`)

- **Estado:** ACEPTADO.
- **Contexto:** El Maestro Completo de Unidades de Medida y Conversiones (UOM) se implementará en la Fase 024. Se requería permitir la creación de productos en la Fase 023 sin admitir unidades arbitrarias no estandarizadas.
- **Decisión:** Implementar `ProductBaseUnitValidator` respaldado por una lista estática controlada de 11 códigos (ISO/SUNAT) y prohibir explícitamente conversiones de unidades en la Fase 023.
- **Consecuencias Positivas:** Permite avanzar la Fase 023 sin bloquearse por el motor UOM, garantizando una migración limpia hacia la Fase 024.
- **Consecuencias Negativas:** La versión actual no soporta empaques secundarios (cajas/pallets) hasta la liberación de la Fase 024.
