# Phase 040 — Severity Policy

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The severity policy determines the `Severity` level of a reception difference case based on financial impact and category. Severity affects approval workflows, notification routing, and security requirements.

## 2. Severity Levels

| Level      | Financial Threshold | SLA (hours) | Approval Required      | Notifications         |
| ---------- | ------------------- | ----------- | ---------------------- | --------------------- |
| `LOW`      | < $100              | 72          | Operator               | Standard              |
| `MEDIUM`   | $100 - $999         | 48          | Supervisor             | Supervisor alert      |
| `HIGH`     | $1,000 - $9,999     | 24          | Manager                | Manager + supervisor  |
| `CRITICAL` | >= $10,000          | 8           | Executive + step-up    | All stakeholders      |

## 3. Auto-Severity Calculation

```python
def calculate_severity(
    total_impact: MonetaryAmount,
    category: DifferenceCategory,
    item_count: int,
) -> Severity:
    """
    Auto-calculate severity based on impact and category.
    
    Source: app/modules/logistics/inbound/reception_differences/domain/services.py
    """
    impact = abs(total_impact.value)
    
    # Base severity from financial impact
    if impact >= 10000:
        base_severity = Severity.CRITICAL
    elif impact >= 1000:
        base_severity = Severity.HIGH
    elif impact >= 100:
        base_severity = Severity.MEDIUM
    else:
        base_severity = Severity.LOW
    
    # Category adjustments
    HIGH_RISK_CATEGORIES = {
        DifferenceCategory.DAMAGED,
        DifferenceCategory.WRONG_ITEM,
        DifferenceCategory.EXPIRED,
        DifferenceCategory.QUALITY_ISSUE,
    }
    
    if category in HIGH_RISK_CATEGORIES:
        # Upgrade severity by one level for high-risk categories
        severity_map = {
            Severity.LOW: Severity.MEDIUM,
            Severity.MEDIUM: Severity.HIGH,
            Severity.HIGH: Severity.CRITICAL,
            Severity.CRITICAL: Severity.CRITICAL,
        }
        base_severity = severity_map[base_severity]
    
    # Multi-item adjustment
    if item_count > 10:
        if base_severity in (Severity.LOW, Severity.MEDIUM):
            base_severity = Severity.HIGH
    
    return base_severity
```

## 4. Severity Rules Matrix

| Category               | < $100 | $100-999 | $1K-9.9K | >= $10K |
| ---------------------- | ------ | -------- | -------- | ------- |
| `QUANTITY_SHORTAGE`    | LOW    | MEDIUM   | HIGH     | CRITICAL|
| `QUANTITY_SURPLUS`     | LOW    | MEDIUM   | HIGH     | CRITICAL|
| `DAMAGED`              | MEDIUM | HIGH     | CRITICAL | CRITICAL|
| `WRONG_ITEM`           | HIGH   | CRITICAL | CRITICAL | CRITICAL|
| `MISSING_DOCUMENTATION`| LOW    | LOW      | MEDIUM   | HIGH    |
| `QUALITY_ISSUE`        | MEDIUM | HIGH     | CRITICAL | CRITICAL|
| `PACKAGING_DAMAGE`     | LOW    | MEDIUM   | HIGH     | CRITICAL|
| `EXPIRED`              | HIGH   | CRITICAL | CRITICAL | CRITICAL|
| `MISLABELED`           | MEDIUM | HIGH     | HIGH     | CRITICAL|
| `OTHER`                | LOW    | MEDIUM   | MEDIUM   | HIGH    |

## 5. Manual Override

Operators can manually override severity with justification:

```python
def override_severity(
    case: CaseAggregate,
    new_severity: Severity,
    justification: str,
    user_roles: List[str],
) -> Severity:
    """
    Manual severity override with audit trail.
    
    Requires: supervisor role or higher
    """
    if "supervisor" not in user_roles and "admin" not in user_roles:
        raise InsufficientPermissionsError(
            required=["supervisor", "admin"]
        )
    
    old_severity = case.severity
    case.severity = new_severity
    case.severity_justification = justification
    case.severity_overridden_by = case.created_by
    
    # Emit event
    emit_event(
        SeverityChanged,
        case_id=case.id,
        old_severity=old_severity,
        new_severity=new_severity,
        justification=justification,
    )
    
    return new_severity
```

## 6. Severity Impact on Workflows

### 6.1 Approval Chain

```
LOW ──────▶ Operator can approve
MEDIUM ───▶ Supervisor approval
HIGH ─────▶ Manager approval
CRITICAL ─▶ Executive approval + step-up auth
```

### 6.2 Notification Routing

| Severity | Notified Parties                                    |
| -------- | --------------------------------------------------- |
| LOW      | Case creator, assigned operator                     |
| MEDIUM   | + Supervisor                                        |
| HIGH     | + Manager, Quality team                             |
| CRITICAL | + Executive, Legal, Compliance, All stakeholders    |

### 6.3 SLA Enforcement

| Severity | Response SLA | Resolution SLA | Escalation Trigger |
| -------- | ------------ | -------------- | ------------------- |
| LOW      | 4 hours      | 72 hours       | After 72 hours      |
| MEDIUM   | 2 hours      | 48 hours       | After 48 hours      |
| HIGH     | 1 hour       | 24 hours       | After 24 hours      |
| CRITICAL | 30 minutes   | 8 hours        | After 8 hours       |

## 7. Severity Recalculation

Severity is automatically recalculated when:
- Items are added or removed
- Quantities are updated
- Category changes
- Manual override is applied

```python
def recalculate_severity(case: CaseAggregate) -> Severity:
    """Recalculate severity based on current case state."""
    total_impact = sum(
        item.total_impact.value for item in case.items
    )
    
    new_severity = calculate_severity(
        total_impact=MonetaryAmount(value=total_impact),
        category=case.category,
        item_count=len(case.items),
    )
    
    if new_severity != case.severity:
        case.severity = new_severity
        emit_event(SeverityChanged, case_id=case.id)
    
    return new_severity
```

---

**See also**: `06_severity_policy.md` (this file), `45_step_up_auth.md` for CRITICAL auth
