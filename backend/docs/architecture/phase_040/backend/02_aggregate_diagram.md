# Phase 040 — Aggregate Diagram

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Aggregate Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      CaseAggregate (Root)                       │
├─────────────────────────────────────────────────────────────────┤
│  id: CaseId (UUID)                                              │
│  tenant_id: str                                                 │
│  status: CaseStatus                                             │
│  severity: Severity                                             │
│  category: DifferenceCategory                                   │
│  description: str                                               │
│  reception_id: str                                              │
│  supplier_id: str                                               │
│  warehouse_id: str                                              │
│  responsible_party: Optional[str]                               │
│  canonical_hash: CanonicalHash                                  │
│  created_at: datetime                                           │
│  updated_at: datetime                                           │
│  created_by: str                                                │
├─────────────────────────────────────────────────────────────────┤
│  │                                                              │
│  │ 1:N                                                         │
│  ▼                                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  ItemAggregate (Child)                    │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  id: ItemId (UUID)                                        │  │
│  │  case_id: CaseId (FK)                                     │  │
│  │  sku: str                                                 │  │
│  │  item_type: ItemType                                      │  │
│  │  status: ItemStatus                                       │  │
│  │  expected_qty: Quantity                                   │  │
│  │  received_qty: Quantity                                   │  │
│  │  difference_qty: Quantity (computed)                      │  │
│  │  unit_cost: MonetaryAmount                                │  │
│  │  total_impact: MonetaryAmount (computed)                  │  │
│  │  notes: Optional[str]                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  │ 1:1 (optional)                                              │
│  ▼                                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Snapshot (Value Object)                 │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  snapshot_id: str                                         │  │
│  │  case_id: CaseId (FK)                                     │  │
│  │  data: JSON                                               │  │
│  │  captured_at: datetime                                    │  │
│  │  captured_by: str                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  │ 1:N                                                        │
│  ▼                                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                EvidenceLink (Value Object)                 │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  evidence_id: str                                         │  │
│  │  case_id: CaseId (FK)                                     │  │
│  │  url: str                                                 │  │
│  │  evidence_type: EvidenceFormat                            │  │
│  │  description: Optional[str]                               │  │
│  │  uploaded_by: str                                         │  │
│  │  uploaded_at: datetime                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Invariant Rules

### CaseAggregate Invariants

| ID    | Rule                                                           | Enforcement       |
| ----- | -------------------------------------------------------------- | ----------------- |
| INV-1 | Case MUST have at least one ItemAggregate                      | Pre-condition     |
| INV-2 | Status transitions MUST follow state machine                   | `require_case_transition` |
| INV-3 | CRITICAL severity MUST have step-up authentication             | Security guard    |
| INV-4 | `canonical_hash` MUST be recomputed on state change            | Domain service    |
| INV-5 | `snapshot` MUST be captured before transitions                 | Pre-transition hook |
| INV-6 | Tenant ID MUST match authenticated user's tenant               | Infrastructure    |
| INV-7 | `reception_id` MUST reference valid reception record           | FK constraint     |

### ItemAggregate Invariants

| ID    | Rule                                                           | Enforcement       |
| ----- | -------------------------------------------------------------- | ----------------- |
| INV-8 | `difference_qty` = `expected_qty` - `received_qty`            | Computed field    |
| INV-9 | `total_impact` = `difference_qty` × `unit_cost`               | Computed field    |
| INV-10| Item status MUST be consistent with parent case status         | State machine     |
| INV-11| `expected_qty` MUST be > 0                                     | Validation        |
| INV-12| `received_qty` MUST be >= 0                                    | Validation        |

## 3. Consistency Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                 Consistency Boundary                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CaseAggregate                                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │  │
│  │  │  Case   │  │  Items  │  │Evidence │              │  │
│  │  │  State  │──│  List   │──│  Links  │              │  │
│  │  └─────────┘  └─────────┘  └─────────┘              │  │
│  │       │                                               │  │
│  │       ▼                                               │  │
│  │  ┌─────────┐  ┌─────────┐                            │  │
│  │  │Snapshot │  │Canonical│                            │  │
│  │  │         │  │  Hash   │                            │  │
│  │  └─────────┘  └─────────┘                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Transaction Scope:                                         │
│  - All item changes within case                             │
│  - Snapshot capture                                         │
│  - Hash recomputation                                       │
│  - Status transition                                        │
└─────────────────────────────────────────────────────────────┘
```

## 4. Aggregate Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Detected │───▶│  Draft   │───▶│Submitted │───▶│ InReview │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                       │              │
                                       ▼              ▼
                                 ┌──────────┐   ┌──────────┐
                                 │ Rejected │   │ Approved │
                                 └──────────┘   └──────────┘
                                                      │
                                                      ▼
                                                ┌──────────┐
                                                │ Document │
                                                │  Issued  │
                                                └──────────┘
                                                      │
                                                      ▼
                                                ┌──────────┐
                                                │  Closed  │
                                                └──────────┘
```

## 5. Cross-Aggregate References

| Reference               | From              | To                  | Type     |
| ----------------------- | ----------------- | ------------------- | -------- |
| Reception → Case        | ReceptionRecord   | CaseAggregate       | Inbound  |
| Case → Supplier         | CaseAggregate     | Supplier (external) | Reference|
| Case → Warehouse        | CaseAggregate     | Warehouse (external)| Reference|
| Case → User             | CaseAggregate     | User (auth)         | Reference|
| Case → Document         | CaseAggregate     | DIF Document        | Outbound |

---

**See also**: `07_case_status_transitions.md` for detailed state machine
