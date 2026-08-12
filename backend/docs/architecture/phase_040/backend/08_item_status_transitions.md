# Phase 040 — Item Status Transitions

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Item Status Lifecycle

Items within a case follow their own status lifecycle, independent but coordinated with the parent case.

## 2. Item States

| State        | Description                              |
| ------------ | ---------------------------------------- |
| `PENDING`    | Initial state, awaiting processing       |
| `FORMALIZED` | Candidate item formalized into case      |
| `REJECTED`   | Item rejected during review              |
| `RESOLVED`   | Item difference resolved                 |
| `CANCELLED`  | Item removed from case                   |

## 3. State Diagram

```
┌──────────┐
│ PENDING  │
└────┬─────┘
     │
     ├─── formalize_item() ──────▶ ┌────────────┐
     │                              │ FORMALIZED │
     │                              └─────┬──────┘
     │                                    │
     │                      ┌─────────────┴─────────────┐
     │                      ▼                           ▼
     │                ┌──────────┐                ┌──────────┐
     │                │ REJECTED │                │ RESOLVED │
     │                └──────────┘                └──────────┘
     │
     └─── cancel_item() ──────▶ ┌───────────┐
                                 │ CANCELLED │
                                 └───────────┘
```

## 4. Transition Map

```python
ITEM_TRANSITIONS: Dict[ItemStatus, List[ItemStatus]] = {
    ItemStatus.PENDING: [
        ItemStatus.FORMALIZED,
        ItemStatus.CANCELLED,
    ],
    ItemStatus.FORMALIZED: [
        ItemStatus.REJECTED,
        ItemStatus.RESOLVED,
    ],
    ItemStatus.REJECTED: [],
    ItemStatus.RESOLVED: [],
    ItemStatus.CANCELLED: [],
}
```

## 5. Transition Rules

### 5.1 PENDING → FORMALIZED

**Trigger**: Candidate formalization

**Guards**:
- Item must have valid SKU
- `expected_qty` must be > 0
- `received_qty` must be >= 0
- Parent case must be in `DRAFT` or `SUBMITTED` status

```python
def formalize_item(item: ItemAggregate, case: CaseAggregate) -> None:
    """Formalize a pending item."""
    if case.status not in (CaseStatus.DRAFT, CaseStatus.SUBMITTED):
        raise ItemStatusConflictError(
            "Cannot formalize item when case is not in DRAFT or SUBMITTED"
        )
    
    if item.sku is None or item.sku == "":
        raise ItemValidationError("SKU is required for formalization")
    
    item.status = ItemStatus.FORMALIZED
    item.formalized_at = datetime.utcnow()
    item.formalized_by = current_user.id
```

### 5.2 FORMALIZED → REJECTED

**Trigger**: Review rejection

**Guards**:
- Rejection reason must be provided
- Parent case must be in `IN_REVIEW` status

```python
def reject_item(
    item: ItemAggregate,
    case: CaseAggregate,
    reason: str,
) -> None:
    """Reject a formalized item."""
    if case.status != CaseStatus.IN_REVIEW:
        raise ItemStatusConflictError(
            "Cannot reject item when case is not in IN_REVIEW"
        )
    
    if not reason:
        raise ItemValidationError("Rejection reason is required")
    
    item.status = ItemStatus.REJECTED
    item.rejection_reason = reason
    item.rejected_at = datetime.utcnow()
    item.rejected_by = current_user.id
```

### 5.3 FORMALIZED → RESOLVED

**Trigger**: Difference resolution

**Guards**:
- Resolution must be documented
- Parent case must be in `APPROVED` or `PENDING_CLOSE` status

```python
def resolve_item(
    item: ItemAggregate,
    case: CaseAggregate,
    resolution: str,
) -> None:
    """Mark item as resolved."""
    if case.status not in (CaseStatus.APPROVED, CaseStatus.PENDING_CLOSE):
        raise ItemStatusConflictError(
            "Cannot resolve item when case is not in APPROVED or PENDING_CLOSE"
        )
    
    item.status = ItemStatus.RESOLVED
    item.resolution = resolution
    item.resolved_at = datetime.utcnow()
    item.resolved_by = current_user.id
```

### 5.4 PENDING → CANCELLED

**Trigger**: Item removal

**Guards**:
- Case must not be in terminal state (`CLOSED`, `CANCELLED`)

```python
def cancel_item(item: ItemAggregate, case: CaseAggregate) -> None:
    """Cancel a pending item."""
    if case.status in (CaseStatus.CLOSED, CaseStatus.CANCELLED):
        raise ItemStatusConflictError(
            "Cannot cancel item when case is closed or cancelled"
        )
    
    item.status = ItemStatus.CANCELLED
    item.cancelled_at = datetime.utcnow()
    item.cancelled_by = current_user.id
```

## 6. Item-Case Status Consistency

| Case Status         | Allowed Item States                     |
| ------------------- | --------------------------------------- |
| `DETECTED`          | PENDING                                 |
| `DRAFT`             | PENDING, FORMALIZED                     |
| `SUBMITTED`         | PENDING, FORMALIZED                     |
| `IN_REVIEW`         | FORMALIZED, REJECTED                    |
| `APPROVED`          | FORMALIZED, RESOLVED                    |
| `PENDING_CLOSE`     | FORMALIZED, RESOLVED                    |
| `CLOSED`            | RESOLVED (all items must be resolved)   |

## 7. Bulk Operations

```python
def bulk_formalize_items(
    items: List[ItemAggregate],
    case: CaseAggregate,
) -> List[ItemAggregate]:
    """Formalize multiple items at once."""
    formalized = []
    for item in items:
        if item.status == ItemStatus.PENDING:
            formalize_item(item, case)
            formalized.append(item)
    return formalized
```

---

**See also**: `21_formalization_service.md` for formalization workflow
