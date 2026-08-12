# 01 — Auditoría de Órdenes de Compra Legacy y Desacoplamiento

---

## 1. Auditoría del Módulo Legacy Previo

En versiones anteriores de la plataforma, el concepto de "Orden de Compra" existía como una entidad monolítica rudimentaria dentro del espacio de nombres `app/modules/logistics/purchase_orders/`. Dicha implementación presentaba severas deficiencias técnicas y arquitectónicas:

1. **Apareamiento Excesivo**: La tabla `purchase_orders` legacy acumulaba datos de logística, recepciones de almacén, facturación y cuentas por pagar en un solo modelo ORM.
2. **Deficiencias de Dominio**:
   - Falta de inmutabilidad en el control de revisiones (los cambios sobreescribían los registros existentes).
   - Uso de tipos de datos de coma flotante (`FLOAT` / `DOUBLE PRECISION`) provocando errores de redondeo en balances contables.
   - Ausencia de soporte para adjudicaciones parciales CCO (Cuadro Comparativo de Ofertas).
   - Sin trazabilidad de asignaciones ni soporte para entregas programadas.
3. **Brechas de Seguridad**:
   - No existía restricción para impedir que el usuario creador aprobase sus propias órdenes.
   - Carecía de integración con mecanismos de autenticación robusta (Step-Up Auth) para autorizaciones de gasto elevado.

---

## 2. Justificación del Desacoplamiento DDD

Para alinearse con los principios de **Domain-Driven Design (DDD)** y la **Arquitectura Hexagonal**, la Fase 034 traslada y refactoriza por completo el subsistema hacia el espacio de nombres delimitado (Bounded Context):

```
app/modules/logistics/procurement/purchase_orders/
```

### Razones Arquitectónicas:
* **Separación de Responsabilidades**: Las Órdenes de Compra son un instrumento del sub-dominio de **Procurement (Aprovisionamiento)**. No deben mezclarse con la ejecución operativa de Almacenes (Warehousing) ni la Gestión de Transporte (Fleet).
* **Encapsulamiento del Dominio**: El dominio de Purchase Orders define sus propias reglas de negocio independientes (políticas de aprobación, cálculo de dinero exacto, snapshots inmutables).
* **Independencia de Despliegue y Evolución**: Permite iterar el flujo comercial y contractual sin impactar el inventario o la facturación downstream.

---

## 3. Estrategia de Prefijo `po_` para la Base de Datos

Para evitar colisiones directas de nombres de tablas con los esquemas heredados o integraciones de terceros (e.g., tablas `purchase_orders` o `purchase_order_lines` legacy), la Fase 034 establece una convención estricta de prefijos:

> **Todas las 16 tablas creadas o administradas por este módulo llevan el prefijo `po_`.**

### Beneficios del Prefijo `po_`:
1. **Prevención de Colisiones (Namespace Cleanliness)**: Garantiza la coexistencia sin riesgos en la misma base de datos PostgreSQL durante el período de coexistencia transitoria.
2. **Claridad en Consultas y Auditoría**: Identifica unívocamente las tablas pertenecientes al Agregado de Órdenes de Compra de Procurement.
3. **Aislamiento de Migraciones Alembic**: Las migraciones operan exclusivamente sobre patrones `po_*`, simplificando scripts de rollback y auditorías DDL.

---

## 4. Matriz de Coexistencia y Migración

| Aspecto | Módulo Legacy (`/logistics/purchase_orders`) | Nuevo Bounded Context (`/logistics/procurement/purchase_orders`) |
| :--- | :--- | :--- |
| **Ubicación de Código** | `app/modules/logistics/purchase_orders/` | `app/modules/logistics/procurement/purchase_orders/` |
| **Tablas PostgreSQL** | `purchase_orders`, `purchase_order_items` | `po_purchase_orders`, `po_purchase_order_revisions`, etc. (16 tablas) |
| **Aritmética Monetaria** | `float` (Prohibido) | `Decimal` con `Numeric(28,10)` |
| **Revisiones / Snapshots** | Mutación in-situ | Inmutabilidad mediante JSONB + SHA-256 |
| **Aprobación** | Flag booleano `is_approved` | `PurchaseOrderApprovalGate` + Step-Up Auth + Anti Self-Approval |
