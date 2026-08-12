# Phase 040 — Domain Enums

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/domain/enums.py`

## 1. CaseStatus

Represents the lifecycle state of a reception difference case.

```python
class CaseStatus(str, Enum):
    DETECTED = "DETECTED"
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING_DOCUMENT = "PENDING_DOCUMENT"
    DOCUMENT_ISSUED = "DOCUMENT_ISSUED"
    PENDING_CLOSE = "PENDING_CLOSE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ON_HOLD = "ON_HOLD"
    ESCALATED = "ESCALATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    AWAITING_EVIDENCE = "AWAITING_EVIDENCE"
    RESOLVED = "RESOLVED"
```

| Value               | Description                              | Next States                              |
| ------------------- | ---------------------------------------- | ---------------------------------------- |
| `DETECTED`          | Initial detection at reception           | DRAFT, CANCELLED                         |
| `DRAFT`             | Being prepared by operator               | SUBMITTED, CANCELLED                     |
| `SUBMITTED`         | Submitted for review                     | IN_REVIEW, REJECTED                      |
| `IN_REVIEW`         | Under review by supervisor               | APPROVED, REJECTED, ON_HOLD              |
| `APPROVED`          | Approved for processing                  | PENDING_DOCUMENT                         |
| `REJECTED`          | Rejected with reason                     | DRAFT (resubmit), CANCELLED              |
| `PENDING_DOCUMENT`  | Awaiting DIF document generation         | DOCUMENT_ISSUED                          |
| `DOCUMENT_ISSUED`   | DIF document generated                   | PENDING_CLOSE                            |
| `PENDING_CLOSE`     | Awaiting final closure                   | CLOSED                                   |
| `CLOSED`            | Case fully resolved                      | — (terminal)                             |
| `CANCELLED`         | Case cancelled                           | — (terminal)                             |
| `ON_HOLD`           | Temporarily paused                       | IN_REVIEW, CANCELLED                     |
| `ESCALATED`         | Escalated to higher authority            | IN_REVIEW, APPROVED                      |
| `PENDING_APPROVAL`  | Awaiting multi-level approval            | APPROVED, REJECTED                       |
| `PARTIALLY_RESOLVED`| Some items resolved, others pending      | CLOSED, IN_REVIEW                        |
| `AWAITING_EVIDENCE` | Waiting for evidence submission          | IN_REVIEW, REJECTED                      |
| `RESOLVED`          | Resolution complete, pending closure     | PENDING_CLOSE                            |

## 2. ItemType

```python
class ItemType(str, Enum):
    PRODUCT = "PRODUCT"
    ACCESSORY = "ACCESSORY"
    RAW_MATERIAL = "RAW_MATERIAL"
    PACKAGING = "PACKAGING"
    COMPONENT = "COMPONENT"
```

## 3. DifferenceCategory

```python
class DifferenceCategory(str, Enum):
    QUANTITY_SHORTAGE = "QUANTITY_SHORTAGE"
    QUANTITY_SURPLUS = "QUANTITY_SURPLUS"
    DAMAGED = "DAMAGED"
    WRONG_ITEM = "WRONG_ITEM"
    MISSING_DOCUMENTATION = "MISSING_DOCUMENTATION"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    PACKAGING_DAMAGE = "PACKAGING_DAMAGE"
    EXPIRED = "EXPIRED"
    MISLABELED = "MISLABELED"
    OTHER = "OTHER"
```

| Category                   | Severity Range | Auto-Assign  |
| -------------------------- | -------------- | ------------ |
| `QUANTITY_SHORTAGE`        | LOW → CRITICAL | `calculate_severity()` |
| `QUANTITY_SURPLUS`         | LOW → HIGH     | `calculate_severity()` |
| `DAMAGED`                  | MEDIUM → CRITICAL | Manual review |
| `WRONG_ITEM`               | HIGH → CRITICAL | Auto-escalate |
| `MISSING_DOCUMENTATION`    | LOW → MEDIUM   | Auto-assign   |
| `QUALITY_ISSUE`            | MEDIUM → CRITICAL | Manual review |
| `PACKAGING_DAMAGE`         | LOW → HIGH     | Auto-assign   |
| `EXPIRED`                  | HIGH → CRITICAL | Auto-escalate |
| `MISLABELED`               | MEDIUM → HIGH  | Auto-assign   |
| `OTHER`                    | LOW → MEDIUM   | Manual review |

## 4. Severity

```python
class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
```

| Level      | Financial Threshold | Auto-Action Required         |
| ---------- | ------------------- | ---------------------------- |
| `LOW`      | < $100              | Standard processing          |
| `MEDIUM`   | $100 - $999         | Supervisor notification      |
| `HIGH`     | $1,000 - $9,999     | Manager review               |
| `CRITICAL` | >= $10,000          | Step-up auth + executive     |

## 5. EvidenceFormat

```python
class EvidenceFormat(str, Enum):
    PHOTO = "PHOTO"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    OTHER = "OTHER"
```

## 6. ItemStatus

```python
class ItemStatus(str, Enum):
    PENDING = "PENDING"
    FORMALIZED = "FORMALIZED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"
```

## 7. DocumentType

```python
class DocumentType(str, Enum):
    DIF = "DIF"  # Documento de Incidencia de Facturación
    CREDIT_NOTE = "CREDIT_NOTE"
    ADJUSTMENT = "ADJUSTMENT"
    REPORT = "REPORT"
```

## 8. ResponsibilityType

```python
class ResponsibilityType(str, Enum):
    SUPPLIER = "SUPPLIER"
    WAREHOUSE = "WAREHOUSE"
    CARRIER = "CARRIER"
    INTERNAL = "INTERNAL"
    UNKNOWN = "UNKNOWN"
```

## 9. TransitionAction

```python
class TransitionAction(str, Enum):
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CANCEL = "CANCEL"
    ESCALATE = "ESCALATE"
    HOLD = "HOLD"
    RESUME = "RESUME"
    ISSUE_DOCUMENT = "ISSUE_DOCUMENT"
    CLOSE = "CLOSE"
```

## 10. SnapshotReason

```python
class SnapshotReason(str, Enum):
    PRE_TRANSITION = "PRE_TRANSITION"
    MANUAL = "MANUAL"
    AUDIT = "AUDIT"
    SCHEDULED = "SCHEDULED"
```

---

**See also**: `07_case_status_transitions.md` for transition rules
