# Phase 040 — Responsibility Workflow

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The responsibility workflow tracks which party is responsible for a reception difference. This affects approval routing, notification targets, and resolution accountability.

## 2. Responsibility Types

| Type         | Description                              | Typical Resolution          |
| ------------ | ---------------------------------------- | --------------------------- |
| `SUPPLIER`   | Supplier provided wrong/insufficient goods | Credit note, replacement   |
| `WAREHOUSE`  | Warehouse handling error                  | Internal correction         |
| `CARRIER`    | Transportation damage/loss                | Carrier claim               |
| `INTERNAL`   | Internal process failure                  | Process improvement         |
| `UNKNOWN`    | Responsibility not yet determined         | Investigation required      |

## 3. Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ UNKNOWN  │───▶│ ASSIGNED │───▶│ ACCEPTED │───▶│ RESOLVED │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │               │
                     ▼               ▼
               ┌──────────┐    ┌──────────┐
               │ DISPUTED │    │ REJECTED │
               └──────────┘    └──────────┘
```

## 4. Assignment Rules

### 4.1 Auto-Assignment

```python
def auto_assign_responsibility(
    case: CaseAggregate,
    reception_data: dict,
) -> ResponsibilityType:
    """
    Auto-determine responsibility based on reception data.
    
    Rules:
    - Damaged items → CARRIER (if damage during transport)
    - Wrong items → SUPPLIER
    - Quantity shortage → SUPPLIER (if not warehouse-verified)
    - Quality issues → SUPPLIER or INTERNAL
    """
    category = case.category
    
    if category == DifferenceCategory.DAMAGED:
        if reception_data.get("damage_type") == "transport":
            return ResponsibilityType.CARRIER
        return ResponsibilityType.WAREHOUSE
    
    if category == DifferenceCategory.WRONG_ITEM:
        return ResponsibilityType.SUPPLIER
    
    if category == DifferenceCategory.QUANTITY_SHORTAGE:
        if reception_data.get("warehouse_verified"):
            return ResponsibilityType.SUPPLIER
        return ResponsibilityType.WAREHOUSE
    
    if category == DifferenceCategory.QUALITY_ISSUE:
        return ResponsibilityType.SUPPLIER
    
    return ResponsibilityType.UNKNOWN
```

### 4.2 Manual Assignment

```python
def assign_responsibility(
    case: CaseAggregate,
    responsibility: ResponsibilityType,
    justification: str,
) -> None:
    """Manually assign responsibility with justification."""
    case.responsible_party = responsibility.value
    case.responsibility_justification = justification
    case.responsibility_assigned_at = datetime.utcnow()
    case.responsibility_assigned_by = current_user.id
    
    emit_event(
        ResponsibilityAssigned,
        case_id=case.id,
        responsibility=responsibility,
        justification=justification,
    )
```

## 5. Responsibility → Approval Routing

| Responsibility | Approver Role        | Escalation Path         |
| -------------- | -------------------- | ----------------------- |
| `SUPPLIER`     | Procurement Manager  | Supply Chain Director   |
| `WAREHOUSE`    | Warehouse Manager    | Operations Director     |
| `CARRIER`      | Logistics Manager    | Transport Director      |
| `INTERNAL`     | Quality Manager      | Quality Director        |
| `UNKNOWN`      | Operations Manager   | VP Operations           |

## 6. Dispute Workflow

When a party disputes responsibility:

```python
def dispute_responsibility(
    case: CaseAggregate,
    dispute_reason: str,
    evidence: List[EvidenceLink],
) -> None:
    """Record responsibility dispute."""
    case.responsibility_status = "DISPUTED"
    case.dispute_reason = dispute_reason
    case.dispute_evidence = evidence
    case.disputed_at = datetime.utcnow()
    case.disputed_by = current_user.id
    
    # Escalate to management
    case.status = CaseStatus.ESCALATED
    
    emit_event(
        ResponsibilityDisputed,
        case_id=case.id,
        dispute_reason=dispute_reason,
    )
```

## 7. Impact on Notifications

| Event                    | Notified Parties                        |
| ------------------------ | --------------------------------------- |
| Responsibility assigned  | Assigned party, case creator            |
| Responsibility disputed  | Both parties, management                |
| Responsibility accepted  | Case creator, quality team              |
| Responsibility resolved  | All stakeholders                        |

---

**See also**: `26_notification_service.md` for notification routing
