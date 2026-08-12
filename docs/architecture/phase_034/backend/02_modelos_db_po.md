# 02 — Especificación de Modelos de Base de Datos ORM (`po_*`)

---

## 1. Visión General del Esquema Entidad-Relación

La Fase 034 implementa 16 modelos ORM utilizando SQLAlchemy 2.0. Todos los modelos residen en `app/modules/logistics/procurement/purchase_orders/infrastructure/persistence/models.py` y se asignan a tablas con el prefijo `po_`.

### Principios del Diseño de Base de Datos:
* **Claves Primarias**: Identificadores Únicos Universales (`UUID`) generados con versión 4.
* **Integridad Referencial**: Claves foráneas con restricción explícita `ON DELETE RESTRICT` para impedir eliminaciones en cascada accidentales.
* **Tipos Financieros y Numéricos**: Precisión arbitraria exacta `Numeric(28,10)` para importes monetarios y cantidades.
* **Auditoría e Inmutabilidad**: Timestamps `created_at` y `updated_at` con zona horaria UTC (`TIMESTAMPTZ`).

---

## 2. Inventario Completo de los 16 Modelos ORM

| # | Nombre de la Clase ORM | Nombre de Tabla PostgreSQL | Descripción y Propósito |
| :-: | :--- | :--- | :--- |
| 1 | `PurchaseOrderModel` | `po_purchase_orders` | Raíz del Agregado. Registra la cabecera de la OC, código, estado y puntero a la revisión activa. |
| 2 | `PurchaseOrderRevisionModel` | `po_purchase_order_revisions` | Almacena el historial inmutable de revisiones de la OC con snapshots JSONB (`supplier`, `buyer`, `source`, `monetary`) y `content_hash` SHA-256. |
| 3 | `PurchaseOrderLineModel` | `po_purchase_order_lines` | Ítems de detalle de la OC asociados a una revisión específica (descripción, cantidad, precio unitario, montos calculados). |
| 4 | `PurchaseOrderSourceAllocationModel` | `po_purchase_order_source_allocations` | Vinculación inmutable entre líneas de decisión CCO / Requisición y líneas de la OC. |
| 5 | `PurchaseOrderSourceVarianceModel` | `po_purchase_order_source_variances` | Registro de justificaciones de desviaciones/sustituciones respecto a la cotización original. |
| 6 | `PurchaseOrderTaxComponentModel` | `po_purchase_order_tax_components` | Desglose discriminado de impuestos por línea o nivel de orden (IGV, Detracciones, Retenciones). |
| 7 | `PurchaseOrderChargeModel` | `po_purchase_order_charges` | Desglose de cargos aditivos/deductivos adicionales (Flete, Seguro, Embalaje, Descuento Global). |
| 8 | `PurchaseOrderDeliveryScheduleModel` | `po_purchase_order_delivery_schedules` | Cabecera del plan de entregas parciales y condiciones logísticas de despacho. |
| 9 | `PurchaseOrderDeliveryScheduleLineModel` | `po_purchase_order_delivery_schedule_lines` | Distribución detallada de cantidades a entregar por fecha y dirección de destino. |
| 10 | `PurchaseOrderApprovalHistoryModel` | `po_purchase_order_approval_history` | Registro de eventos del flujo de aprobación (solicitud, aprobación, rechazo, devolución) con huella biometric/step-up. |
| 11 | `PurchaseOrderDocumentRefModel` | `po_purchase_order_document_refs` | Enlaces a archivos adjuntos (cotizaciones PDF, fichas técnicas, contratos). |
| 12 | `PurchaseOrderNoteModel` | `po_purchase_order_notes` | Notas internas y observaciones visibles para el proveedor. |
| 13 | `PurchaseOrderTermsModel` | `po_purchase_order_terms` | Cláusulas comerciales, términos de pago (e.g. 30 días crédito) e Incoterms. |
| 14 | `PurchaseOrderContactModel` | `po_purchase_order_contacts` | Contactos operativos asignados (representante del proveedor, comprador responsable). |
| 15 | `PurchaseOrderCustomFieldModel` | `po_purchase_order_custom_fields` | Atributos extendidos dinámicos en formato clave-valor para integración ERP. |
| 16 | `PurchaseOrderAuditLogModel` | `po_purchase_order_audit_logs` | Registro inmutable append-only de mutaciones de estado y eventos del sistema. |

---

## 3. Especificación Detallada de Campos Clave y Tipos

### 3.1. `po_purchase_orders` (Cabecera Principal)
```sql
CREATE TABLE po_purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL,
    organization_id UUID NOT NULL,
    site_id UUID NOT NULL,
    current_revision_id UUID, -- FK a po_purchase_order_revisions (nullable hasta completar primera revision)
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    created_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_po_status CHECK (status IN ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'RETURNED_FOR_CHANGES', 'CANCELLED'))
);
```

### 3.2. `po_purchase_order_revisions` (Snapshot e Inmutabilidad)
```sql
CREATE TABLE po_purchase_order_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES po_purchase_orders(id) ON DELETE RESTRICT,
    revision_number INT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- Digest SHA-256 de la revision
    supplier_snapshot JSONB NOT NULL,
    buyer_snapshot JSONB NOT NULL,
    source_snapshot JSONB NOT NULL,
    monetary_snapshot JSONB NOT NULL,
    created_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_po_revision_number UNIQUE (purchase_order_id, revision_number)
);
```

### 3.3. `po_purchase_order_lines` (Detalle de Ítems)
```sql
CREATE TABLE po_purchase_order_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id UUID NOT NULL REFERENCES po_purchase_order_revisions(id) ON DELETE RESTRICT,
    line_number INT NOT NULL,
    item_id UUID,
    sku VARCHAR(64),
    description TEXT NOT NULL,
    ordered_quantity NUMERIC(28, 10) NOT NULL,
    unit_of_measure VARCHAR(16) NOT NULL,
    unit_price NUMERIC(28, 10) NOT NULL,
    currency_code VARCHAR(3) NOT NULL,
    discount_type VARCHAR(16) NOT NULL DEFAULT 'NONE',
    discount_value NUMERIC(28, 10) NOT NULL DEFAULT 0.0000000000,
    discount_amount NUMERIC(28, 10) NOT NULL DEFAULT 0.0000000000,
    tax_rate NUMERIC(28, 10) NOT NULL DEFAULT 0.0000000000,
    tax_amount NUMERIC(28, 10) NOT NULL DEFAULT 0.0000000000,
    freight_amount NUMERIC(28, 10) NOT NULL DEFAULT 0.0000000000,
    other_charges_amount NUMERIC(28, 10) NOT NULL DEFAULT 0.0000000000,
    line_subtotal NUMERIC(28, 10) NOT NULL,
    line_net NUMERIC(28, 10) NOT NULL,
    line_total NUMERIC(28, 10) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_po_line_qty_positive CHECK (ordered_quantity > 0),
    CONSTRAINT ck_po_line_price_non_negative CHECK (unit_price >= 0),
    CONSTRAINT uq_po_line_number UNIQUE (revision_id, line_number)
);
```

---

## 4. Restricciones de Integridad (Check Constraints & FKs)

1. **`ck_po_line_qty_positive`**: Garantiza que `ordered_quantity > 0`.
2. **`ck_po_line_price_non_negative`**: Impide precios unitarios negativos (`unit_price >= 0`).
3. **`ck_po_tax_rate_range`**: Exige que las tasas impositivas se encuentren entre 0% y 100% (`tax_rate BETWEEN 0 AND 100`).
4. **`ON DELETE RESTRICT`**: Aplicado en todas las llaves foráneas primarias para prevenir la eliminación accidental de revisiones o líneas vinculadas a documentos contables.
