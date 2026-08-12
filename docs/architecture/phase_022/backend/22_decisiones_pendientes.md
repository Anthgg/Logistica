# 22. Registro de Decisiones de Arquitectura (ADR)

## Registro de Decisiones Tácticas y Técnicas (Fase 022)

Este documento registra los Architecture Decision Records (ADR) tomados durante el diseño del backend de la Fase 022.

---

## ADR 022-01: Extensión In-Place de `warehouses` vs. Entidad `WarehouseV2`

* **Estado:** **APROBADO**
* **Fecha:** 2026-07-28
* **Contexto:** Se requería enriquecer la entidad `WarehouseModel` existente con campos de geolocalización, capacidades globales, áreas y estados de picking. Existía la tentación de crear una tabla paralela `warehouses_v2`.
* **Decisión:** Extender la tabla `warehouses` in-place mediante migraciones DDL de Alembic agregando columnas nullables con defaults y aplicando un backfill para los registros existentes.
* **Consecuencias:**
  * Preservación de la integridad de llaves foráneas preexistentes.
  * Cero duplicación de código u ORMs redundantes.

---

## ADR 022-02: Búsqueda Jerárquica mediante `hierarchy_path` con Índice B-Tree vs. CTE Recursivos

* **Estado:** **APROBADO**
* **Fecha:** 2026-07-28
* **Contexto:** La consulta de subárboles completos (ej. obtener todas las ubicaciones dentro de una zona) en estructuras adyacentes tradicionalmente requiere expresiones de CTE recursivos (`WITH RECURSIVE`), los cuales degradan el rendimiento en consultas masivas.
* **Decisión:** Almacenar una cadena denormalizada `hierarchy_path` en formato `/uuid_raiz/.../uuid_nodo` en cada ubicación, indexada con `varchar_pattern_ops`.
* **Consecuencias:**
  * Consultas de subárboles en tiempo constante $\mathcal{O}(1)$ usando `WHERE hierarchy_path LIKE '/path/%'`.
  * Requiere recálculo atómico en cascada durante movimientos de subárboles (gestionado transaccionalmente por `WarehouseLocationMoveService`).

---

## ADR 022-03: Separación Estricta entre Capacidades Configuradas y Saldos en Tiempo Real

* **Estado:** **APROBADO**
* **Fecha:** 2026-07-28
* **Contexto:** Se discutió si la entidad `WarehouseLocationCapacityModel` debía incluir columnas como `current_weight_kg` o `current_volume`.
* **Decisión:** Mantener las capacidades como **configuración técnica puramente estática** en la Fase 022. El cálculo de saldos y volumen ocupado se diferirá a las Fases 041-046.
* **Consecuencias:**
  * Evita cuellos de botella por *locks* en escrituras de inventario sobre la tabla topológica.
  * Desacoplamiento limpio de responsabilidades arquitectónicas.

---

## ADR 022-04: Tokenización Opaca de Códigos QR (`t1loc:v1:{public_ref}`)

* **Estado:** **APROBADO**
* **Fecha:** 2026-07-28
* **Contexto:** El uso directo de UUIDs o códigos legibles (`ALM01-Z01-A03`) en imágenes QR expone la estructura interna y vulnera la seguridad física contra escaneos maliciosos.
* **Decisión:** Implementar referencias públicas aleatorias criptográficas `public_ref` con un prefijo versionado `t1loc:v1:`, resolubles exclusivamente mediante API autenticada.
* **Consecuencias:**
  * Protección total contra ataques de enumeración (IDOR).
  * Permite la rotación instantánea de etiquetas en caso de compromiso de seguridad física sin alterar el registro interno de la ubicación.
