# Phase 040 — Domain Services

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/domain/services.py`

## 1. Overview

Domain services contain stateless business logic that operates across aggregates. They encapsulate rules that don't belong to a single entity.

## 2. Services

### 2.1 canonical_hash_diff

Computes a SHA-256 hash of the normalized case state for integrity verification.

```python
def canonical_hash_diff(case: CaseAggregate) -> CanonicalHash:
    """
    Compute canonical hash for case integrity verification.
    
    Args:
        case: The case aggregate to hash
        
    Returns:
        CanonicalHash: SHA-256 hash of normalized state
        
    Raises:
        SnapshotError: If snapshot capture fails
    """
    state = {
        "case_id": str(case.id),
        "status": case.status.value,
        "severity": case.severity.value,
        "category": case.category.value,
        "items": sorted([
            {
                "item_id": str(item.id),
                "sku": item.sku,
                "expected_qty": str(item.expected_qty),
                "received_qty": str(item.received_qty),
                "difference_qty": str(item.difference_qty),
                "unit_cost": str(item.unit_cost),
                "total_impact": str(item.total_impact),
            }
            for item in case.items
        ], key=lambda x: x["item_id"]),
        "responsible_party": case.responsible_party,
        "updated_at": case.updated_at.isoformat(),
    }
    
    canonical_string = json.dumps(state, sort_keys=True, default=str)
    hash_value = hashlib.sha256(canonical_string.encode()).hexdigest()
    
    return CanonicalHash(value=hash_value)
```

**Usage**:
- Called after every state change
- Verified during integrity checks
- Stored in `case.canonical_hash`

### 2.2 require_case_transition

Validates whether a status transition is allowed by the state machine.

```python
def require_case_transition(
    current_status: CaseStatus,
    target_status: CaseStatus,
    user_roles: List[str],
    is_step_up_auth: bool = False,
) -> bool:
    """
    Validate case status transition.
    
    Args:
        current_status: Current case status
        target_status: Desired target status
        user_roles: Roles of the requesting user
        is_step_up_auth: Whether step-up authentication was performed
        
    Returns:
        bool: True if transition is valid
        
    Raises:
        InvalidTransitionError: If transition is not allowed
        StepUpAuthRequiredError: If CRITICAL case requires re-auth
        InsufficientPermissionsError: If user lacks required role
    """
    # Define allowed transitions
    TRANSITIONS = {
        CaseStatus.DETECTED: [CaseStatus.DRAFT, CaseStatus.CANCELLED],
        CaseStatus.DRAFT: [CaseStatus.SUBMITTED, CaseStatus.CANCELLED],
        CaseStatus.SUBMITTED: [CaseStatus.IN_REVIEW, CaseStatus.REJECTED],
        CaseStatus.IN_REVIEW: [
            CaseStatus.APPROVED,
            CaseStatus.REJECTED,
            CaseStatus.ON_HOLD,
            CaseStatus.ESCALATED,
        ],
        CaseStatus.APPROVED: [CaseStatus.PENDING_DOCUMENT],
        CaseStatus.REJECTED: [CaseStatus.DRAFT, CaseStatus.CANCELLED],
        CaseStatus.PENDING_DOCUMENT: [CaseStatus.DOCUMENT_ISSUED],
        CaseStatus.DOCUMENT_ISSUED: [CaseStatus.PENDING_CLOSE],
        CaseStatus.PENDING_CLOSE: [CaseStatus.CLOSED],
        CaseStatus.ON_HOLD: [CaseStatus.IN_REVIEW, CaseStatus.CANCELLED],
        CaseStatus.ESCALATED: [CaseStatus.IN_REVIEW, CaseStatus.APPROVED],
        CaseStatus.PENDING_APPROVAL: [CaseStatus.APPROVED, CaseStatus.REJECTED],
        CaseStatus.PARTIALLY_RESOLVED: [CaseStatus.CLOSED, CaseStatus.IN_REVIEW],
        CaseStatus.AWAITING_EVIDENCE: [CaseStatus.IN_REVIEW, CaseStatus.REJECTED],
        CaseStatus.RESOLVED: [CaseStatus.PENDING_CLOSE],
    }
    
    # Check transition is allowed
    allowed = TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise InvalidTransitionError(
            current=current_status,
            target=target_status,
            allowed=allowed,
        )
    
    # Check step-up auth for CRITICAL
    if current_status == CaseStatus.ESCALATED and not is_step_up_auth:
        raise StepUpAuthRequiredError()
    
    # Check role permissions
    REQUIRED_ROLES = {
        CaseStatus.APPROVED: ["supervisor", "manager", "admin"],
        CaseStatus.REJECTED: ["supervisor", "manager", "admin"],
        CaseStatus.CLOSED: ["admin"],
    }
    
    required = REQUIRED_ROLES.get(target_status, [])
    if required and not any(role in required for role in user_roles):
        raise InsufficientPermissionsError(required=required)
    
    return True
```

### 2.3 strict_decimal_diff

Performs precise decimal arithmetic for quantity calculations.

```python
def strict_decimal_diff(
    expected: Quantity,
    received: Quantity,
    unit_cost: Optional[MonetaryAmount] = None,
) -> Tuple[Quantity, Optional[MonetaryAmount]]:
    """
    Calculate quantity difference and optional financial impact.
    
    Args:
        expected: Expected quantity
        received: Received quantity
        unit_cost: Optional unit cost for impact calculation
        
    Returns:
        Tuple of (difference_qty, total_impact)
        
    Raises:
        InvalidQuantityError: If quantities are negative
    """
    if expected < 0 or received < 0:
        raise InvalidQuantityError("Quantities must be non-negative")
    
    difference = expected - received
    
    total_impact = None
    if unit_cost is not None:
        total_impact = MonetaryAmount(
            value=difference * unit_cost.value,
            currency=unit_cost.currency,
        )
    
    return difference, total_impact
```

## 3. Service Interactions

```
┌─────────────────────────────────────────────────────────────┐
│                    Domain Services                          │
│  ┌───────────────────┐  ┌───────────────────┐              │
│  │ canonical_hash_diff│  │ require_case_     │              │
│  │                   │  │ transition        │              │
│  └─────────┬─────────┘  └─────────┬─────────┘              │
│            │                      │                         │
│            ▼                      ▼                         │
│  ┌───────────────────────────────────────────┐              │
│  │         strict_decimal_diff               │              │
│  └───────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ CaseSvc  │  │ ItemSvc  │  │ Form.Svc │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 4. Testing

| Service                   | Unit Tests | Integration Tests |
| ------------------------- | ---------- | ----------------- |
| `canonical_hash_diff`     | 8          | 3                 |
| `require_case_transition` | 15         | 5                 |
| `strict_decimal_diff`     | 12         | 2                 |
| **Total**                 | **35**     | **10**            |

---

**See also**: `07_case_status_transitions.md` for transition details
