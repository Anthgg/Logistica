# Phase 040 — Error Responses

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "timestamp": "2026-08-02T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

## 2. Error Codes

### 2.1 Client Errors (4xx)

| Code                      | HTTP Status | Description                          |
| ------------------------- | ----------- | ------------------------------------ |
| `CASE_NOT_FOUND`          | 404         | Case with given ID not found         |
| `ITEM_NOT_FOUND`          | 404         | Item with given ID not found         |
| `INVALID_TRANSITION`      | 422         | Status transition not allowed        |
| `INVALID_QUANTITY`        | 422         | Quantity value invalid               |
| `DUPLICATE_ITEM`          | 409         | Duplicate SKU in same case           |
| `MISSING_REQUIRED_FIELD`  | 422         | Required field not provided          |
| `INSUFFICIENT_PERMISSIONS`| 403         | User lacks required permission       |
| `STEP_UP_AUTH_REQUIRED`   | 403         | Re-authentication required           |
| `TENANT_MISMATCH`         | 403         | Cross-tenant access attempted        |
| `CASE_VALIDATION_ERROR`   | 422         | Case data validation failed          |
| `EVIDENCE_UPLOAD_ERROR`   | 500         | Upload failed                        |
| `DOCUMENT_GENERATION_ERROR`| 500        | PDF generation failed                |

### 2.2 Server Errors (5xx)

| Code                      | HTTP Status | Description                          |
| ------------------------- | ----------- | ------------------------------------ |
| `DATABASE_ERROR`          | 500         | Database operation failed            |
| `CONCURRENCY_ERROR`       | 409         | Optimistic lock conflict             |
| `EXTERNAL_SERVICE_ERROR`  | 502         | External service failure             |
| `SNAPSHOT_CAPTURE_ERROR`  | 500         | Failed to capture snapshot           |
| `INTEGRITY_VERIFICATION_ERROR`| 500    | Integrity check failed               |

## 3. Error Examples

### 3.1 Case Not Found

```json
{
  "error": {
    "code": "CASE_NOT_FOUND",
    "message": "Case with ID 550e8400-e29b-41d4-a716-446655440000 not found",
    "details": {
      "case_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "timestamp": "2026-08-02T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### 3.2 Invalid Transition

```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "Cannot transition from CLOSED to SUBMITTED",
    "details": {
      "current_status": "CLOSED",
      "target_status": "SUBMITTED",
      "allowed_transitions": []
    },
    "timestamp": "2026-08-02T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### 3.3 Validation Error

```json
{
  "error": {
    "code": "CASE_VALIDATION_ERROR",
    "message": "Case data validation failed",
    "details": {
      "field_errors": [
        {
          "field": "items",
          "message": "At least one item required"
        }
      ]
    },
    "timestamp": "2026-08-02T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### 3.4 Permission Error

```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "User lacks required permission",
    "details": {
      "required": ["supervisor", "admin"],
      "current_roles": ["operator"]
    },
    "timestamp": "2026-08-02T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### 3.5 Step-Up Auth Required

```json
{
  "error": {
    "code": "STEP_UP_AUTH_REQUIRED",
    "message": "Re-authentication required for CRITICAL severity case",
    "details": {
      "case_severity": "CRITICAL",
      "required_action": "step_up_authentication"
    },
    "timestamp": "2026-08-02T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

## 4. Error Logging

```python
async def log_error(
    error_code: str,
    message: str,
    details: dict,
    request_id: str,
) -> None:
    """Log error for debugging."""
    logger.error(
        f"API Error: {error_code}",
        extra={
            "error_code": error_code,
            "message": message,
            "details": details,
            "request_id": request_id,
        },
    )
```

---

**See also**: `04_domain_errors.md` for domain error classes
