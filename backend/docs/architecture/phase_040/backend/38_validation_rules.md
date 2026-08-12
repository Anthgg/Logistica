# Phase 040 — Validation Rules

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Field Validation Rules

### 1.1 Case Fields

| Field           | Type          | Rules                                    |
| --------------- | ------------- | ---------------------------------------- |
| `reception_id`  | `str`         | Required, 1-100 chars, unique per tenant |
| `category`      | `enum`        | Required, valid DifferenceCategory       |
| `description`   | `str`         | Required, 1-1000 chars                   |
| `supplier_id`   | `str`         | Optional, max 100 chars                  |
| `warehouse_id`  | `str`         | Optional, max 100 chars                  |

### 1.2 Item Fields

| Field           | Type          | Rules                                    |
| --------------- | ------------- | ---------------------------------------- |
| `sku`           | `str`         | Required, 1-100 chars, unique in case    |
| `item_type`     | `enum`        | Required, valid ItemType                 |
| `expected_qty`  | `Decimal`     | Required, > 0, max 10 digits, 3 decimals|
| `received_qty`  | `Decimal`     | Required, >= 0, max 10 digits, 3 decimals|
| `unit_cost`     | `Decimal`     | Optional, >= 0, max 12 digits, 2 decimals|
| `notes`         | `str`         | Optional, max 500 chars                  |

### 1.3 Evidence Fields

| Field           | Type          | Rules                                    |
| --------------- | ------------- | ---------------------------------------- |
| `evidence_type` | `enum`        | Required, valid EvidenceFormat           |
| `description`   | `str`         | Optional, max 500 chars                  |

### 1.4 Document Fields

| Field               | Type          | Rules                                |
| ------------------- | ------------- | ------------------------------------ |
| `resolution_notes`  | `str`         | Optional, max 1000 chars             |

## 2. Validation Decorators

```python
from pydantic import Field, validator

class CreateCaseRequest(BaseModel):
    reception_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Reception record ID"
    )
    
    @validator("reception_id")
    def validate_reception_id(cls, v):
        if not v.strip():
            raise ValueError("reception_id cannot be empty")
        return v.strip()
```

## 3. Business Rule Validation

| Rule                          | Validation                          |
| ----------------------------- | ----------------------------------- |
| Case status transitions       | Must follow state machine           |
| Item status consistency       | Must match parent case status       |
| Evidence requirements         | Required for certain categories     |
| Severity thresholds           | Based on financial impact           |
| SLA compliance                | Based on severity level             |

## 4. Cross-Field Validation

```python
@validator("items")
def validate_items(cls, v, values):
    if len(v) == 0:
        raise ValueError("At least one item required")
    
    skus = [item.sku for item in v]
    if len(skus) != len(set(skus)):
        raise ValueError("Duplicate SKUs not allowed")
    
    return v
```

## 5. Async Validation

```python
@validator("reception_id")
async def validate_reception_exists(cls, v, values):
    # Async validation against external service
    exists = await reception_service.check_exists(v)
    if not exists:
        raise ValueError(f"Reception {v} not found")
    return v
```

---

**See also**: `39_error_responses.md` for validation error formats
