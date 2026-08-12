# Phase 040 — Domain Model

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Bounded Context

**Logistics Inbound → Reception Differences**

This bounded context manages discrepancies detected during goods reception, from initial detection through resolution and document issuance.

```
┌─────────────────────────────────────────────────┐
│         Reception Differences Context           │
├─────────────────────────────────────────────────┤
│  Aggregates:                                    │
│    ├── CaseAggregate (root)                     │
│    └── ItemAggregate (child)                    │
│                                                 │
│  Value Objects:                                 │
│    ├── CaseId                                   │
│    ├── ItemId                                   │
│    ├── Quantity                                 │
│    ├── MonetaryAmount                           │
│    ├── CanonicalHash                            │
│    └── Snapshot                                 │
│                                                 │
│  Domain Services:                               │
│    ├── canonical_hash_diff                      │
│    ├── require_case_transition                  │
│    └── strict_decimal_diff                      │
└─────────────────────────────────────────────────┘
```

## 2. Aggregates

### 2.1 CaseAggregate (Root)

The primary aggregate root representing a reception difference case.

**Source**: `app/modules/logistics/inbound/reception_differences/domain/case_aggregate.py`

| Attribute          | Type              | Description                        |
| ------------------ | ----------------- | ---------------------------------- |
| `id`               | `CaseId`          | Unique identifier (UUID)           |
| `tenant_id`        | `str`             | Tenant isolation key               |
| `status`           | `CaseStatus`      | Current lifecycle state            |
| `severity`         | `Severity`        | Calculated severity level          |
| `category`         | `DifferenceCategory` | Type of difference              |
| `description`      | `str`             | Human-readable description         |
| `reception_id`     | `str`             | Reference to reception record      |
| `supplier_id`      | `str`             | Supplier identifier                |
| `warehouse_id`     | `str`             | Warehouse identifier               |
| `items`            | `List[ItemAggregate]` | Child items                    |
| `responsible_party`| `Optional[str]`   | Assigned responsible party         |
| `evidence_links`   | `List[EvidenceLink]` | Attached evidence                |
| `snapshot`         | `Optional[Snapshot]` | Point-in-time state capture     |
| `canonical_hash`   | `CanonicalHash`   | Integrity hash                     |
| `created_at`       | `datetime`        | Creation timestamp                 |
| `updated_at`       | `datetime`        | Last modification timestamp        |
| `created_by`       | `str`             | Creator user ID                    |

**Invariants**:
1. A case MUST have at least one item
2. Status transitions MUST follow the state machine (see `07_case_status_transitions.md`)
3. CRITICAL severity cases MUST have step-up authentication
4. `canonical_hash` MUST be recomputed on every state change
5. `snapshot` MUST be captured before status transitions

### 2.2 ItemAggregate (Child)

Individual line items within a case.

**Source**: `app/modules/logistics/inbound/reception_differences/domain/item_aggregate.py`

| Attribute          | Type              | Description                        |
| ------------------ | ----------------- | ---------------------------------- |
| `id`               | `ItemId`          | Unique identifier (UUID)           |
| `case_id`          | `CaseId`          | Parent case reference              |
| `sku`              | `str`             | Product SKU                        |
| `item_type`        | `ItemType`        | Type of item (PRODUCT, ACCESSORY)  |
| `status`           | `ItemStatus`      | Current item state                 |
| `expected_qty`     | `Quantity`        | Expected quantity from PO          |
| `received_qty`     | `Quantity`        | Actual received quantity           |
| `difference_qty`   | `Quantity`        | Calculated difference              |
| `unit_cost`        | `MonetaryAmount`  | Unit cost                          |
| `total_impact`     | `MonetaryAmount`  | Financial impact                   |
| `notes`            | `Optional[str]`   | Additional notes                   |

**Invariants**:
1. `difference_qty` = `expected_qty` - `received_qty`
2. `total_impact` = `difference_qty` × `unit_cost`
3. Item status MUST be consistent with parent case status

## 3. Value Objects

| Value Object     | Definition                                              | Location |
| ---------------- | ------------------------------------------------------- | -------- |
| `CaseId`         | UUID v4, immutable                                      | domain/  |
| `ItemId`         | UUID v4, immutable                                      | domain/  |
| `Quantity`       | Decimal(10,3), non-negative                             | domain/  |
| `MonetaryAmount` | Decimal(12,2), currency-aware                           | domain/  |
| `CanonicalHash`  | SHA-256 of normalized case state                        | domain/  |
| `Snapshot`       | JSON-serialized case state at point in time             | domain/  |
| `EvidenceLink`   | URL + type + description                                | domain/  |

## 4. Domain Events

| Event                        | Trigger                          | Payload                      |
| ---------------------------- | -------------------------------- | ---------------------------- |
| `CaseCreated`               | New case detection               | case_id, category            |
| `CaseSubmitted`             | Case submitted for review        | case_id, submitted_by        |
| `CaseApproved`              | Case approved                    | case_id, approved_by         |
| `CaseRejected`              | Case rejected                    | case_id, rejection_reason    |
| `CaseClosed`                | Case resolution complete         | case_id, resolution          |
| `ItemAdded`                 | New item added to case           | case_id, item_id             |
| `ItemFormalized`            | Candidate item formalized        | case_id, item_id             |
| `SeverityChanged`           | Severity recalculated            | case_id, old, new            |
| `EvidenceAttached`          | Evidence linked to case          | case_id, evidence_url        |
| `DocumentIssued`            | DIF document generated           | case_id, document_url        |

## 5. Domain Services

| Service                     | Purpose                                        | Source |
| --------------------------- | ---------------------------------------------- | ------ |
| `canonical_hash_diff`       | Computes integrity hash for case state         | domain/services.py |
| `require_case_transition`   | Validates state machine transitions            | domain/services.py |
| `strict_decimal_diff`       | Precise decimal arithmetic for quantities      | domain/services.py |

## 6. Repositories

| Repository              | Aggregate      | Methods                                          |
| ----------------------- | -------------- | ------------------------------------------------ |
| `CaseRepository`        | CaseAggregate  | get, list, save, delete, count                   |
| `ItemRepository`        | ItemAggregate  | get_by_case, save, delete                        |
| `SnapshotRepository`    | Snapshot       | get_latest, save                                 |

---

**See also**: `02_aggregate_diagram.md` for visual aggregate relationships
