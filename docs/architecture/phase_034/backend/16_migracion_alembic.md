# 16 — Especificación de Migración DDL Alembic (`w340110034dc`)

---

## 1. Identificación de la Migración

* **Fichero Alembic**: `backend/alembic/versions/w340110034dc_phase_034_purchase_orders.py`
* **Revision ID**: `w340110034dc`
* **Revises (Parent)**: `v330110033dc` (Fase 033 — Evaluaciones y Cuadro Comparativo CCO)
* **Fecha de Creación**: `2026-07-31`
* **Alcance DDL**: Creación de 16 tablas con prefijo `po_`, llaves primarias UUID, claves foráneas `ON DELETE RESTRICT`, restricciones CHECK e índices B-Tree.

---

## 2. Definición de Tipos y Funciones Auxiliares Dialectales

Para mantener la compatibilidad en ejecuciones de prueba locales (SQLite) y entornos de producción (PostgreSQL), la migración utiliza adaptadores dialectales:

```python
def _jsonb():
    """Retorna JSONB en PostgreSQL y JSON genérico en SQLite."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB()
    return sa.JSON()

def _uuid():
    """Retorna UUID nativo en PostgreSQL y String(36) en SQLite."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(36)
```

---

## 3. Resumen de las 16 Tablas Creadas en `upgrade()`

| Nombre de Tabla | Claves Primarias / Foráneas | Columnas Destacadas / Restricciones |
| :--- | :--- | :--- |
| `po_purchase_orders` | PK: `id` (UUID) | `purchase_order_code`, `status`, `subtotal`, `grand_total` (`Numeric(28,10)`). |
| `po_purchase_order_revisions` | PK: `id` (UUID), FK: `purchase_order_id` | `revision_number`, `content_hash` (`VARCHAR(64)`), snapshots JSONB. |
| `po_purchase_order_lines` | PK: `id` (UUID), FK: `revision_id` | `ordered_quantity` (`Numeric(28,10)`), `unit_price`, `line_total`. |
| `po_purchase_order_source_allocations` | PK: `id`, FK: `purchase_order_line_id` | `source_type`, `source_document_id`, `allocated_quantity`. |
| `po_purchase_order_source_variances` | PK: `id`, FK: `purchase_order_line_id` | `variance_type`, `original_value`, `new_value`, `justification`. |
| `po_purchase_order_tax_components` | PK: `id`, FK: `revision_id`, `line_id` | `tax_type`, `tax_rate` (`Numeric(12,8)`), `tax_amount`. |
| `po_purchase_order_charges` | PK: `id`, FK: `revision_id` | `charge_type`, `amount` (`Numeric(28,10)`), `is_additive`. |
| `po_purchase_order_delivery_schedules` | PK: `id`, FK: `purchase_order_id` | `incoterm`, `total_deliveries_count`. |
| `po_purchase_order_delivery_schedule_lines`| PK: `id`, FK: `delivery_schedule_id` | `scheduled_quantity`, `expected_delivery_date`, `destination_warehouse_id`. |
| `po_purchase_order_approval_history` | PK: `id`, FK: `purchase_order_id` | `action` (`SUBMIT`, `APPROVE`, `REJECT`), `actor_user_id`, `step_up_factor`. |
| `po_purchase_order_document_refs` | PK: `id`, FK: `purchase_order_id` | `document_type`, `file_name`, `storage_path`. |
| `po_purchase_order_notes` | PK: `id`, FK: `purchase_order_id` | `note_type`, `content`, `is_public_for_supplier`. |
| `po_purchase_order_terms` | PK: `id`, FK: `revision_id` | `payment_terms_code`, `credit_days`, `warranty_terms`. |
| `po_purchase_order_contacts` | PK: `id`, FK: `purchase_order_id` | `contact_role`, `full_name`, `email`, `phone`. |
| `po_purchase_order_custom_fields` | PK: `id`, FK: `purchase_order_id` | `field_key`, `field_value_json`. |
| `po_purchase_order_audit_logs` | PK: `id`, FK: `purchase_order_id` | `event_name`, `actor_user_id`, `payload_json`. |

---

## 4. Índices B-Tree Estratégicos

Para asegurar consultas de alto rendimiento y tiempos de respuesta sub-10ms en la API, la migración crea los siguientes índices B-Tree:

```python
op.create_index("ix_po_orders_org_branch", "po_purchase_orders", ["organization_id", "branch_id"])
op.create_index("ix_po_orders_status", "po_purchase_orders", ["status"])
op.create_index("ix_po_orders_code", "po_purchase_orders", ["normalized_purchase_order_code"], unique=True)
op.create_index("ix_po_revisions_po_id", "po_purchase_order_revisions", ["purchase_order_id"])
op.create_index("ix_po_lines_rev_id", "po_purchase_order_lines", ["revision_id"])
op.create_index("ix_po_alloc_source", "po_purchase_order_source_allocations", ["source_document_id", "source_line_id"])
```

---

## 5. Script DDL `downgrade()`

El procedimiento `downgrade()` elimina las 16 tablas en orden inverso de dependencia para preservar la integridad referencial:

```python
def downgrade() -> None:
    tables = [
        "po_purchase_order_audit_logs",
        "po_purchase_order_custom_fields",
        "po_purchase_order_contacts",
        "po_purchase_order_terms",
        "po_purchase_order_notes",
        "po_purchase_order_document_refs",
        "po_purchase_order_approval_history",
        "po_purchase_order_delivery_schedule_lines",
        "po_purchase_order_delivery_schedules",
        "po_purchase_order_charges",
        "po_purchase_order_tax_components",
        "po_purchase_order_source_variances",
        "po_purchase_order_source_allocations",
        "po_purchase_order_lines",
        "po_purchase_order_revisions",
        "po_purchase_orders"
    ]
    for tbl in tables:
        op.drop_table(tbl)
```
