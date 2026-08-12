# Phase 040 — Domain Errors

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/domain/errors.py`

## 1. Error Hierarchy

```
ReceptionDifferenceError (base)
├── CaseNotFoundError
├── CaseAlreadyExistsError
├── CaseValidationError
│   ├── InvalidCaseStatusError
│   ├── InvalidTransitionError
│   ├── MissingRequiredFieldError
│   ├── InvalidQuantityError
│   └── InvalidSeverityError
├── CaseAuthorizationError
│   ├── InsufficientPermissionsError
│   ├── StepUpAuthRequiredError
│   └── TenantMismatchError
├── ItemNotFoundError
├── ItemValidationError
│   ├── DuplicateItemError
│   ├── InvalidItemTypeError
│   └── ItemStatusConflictError
├── SnapshotError
│   ├── SnapshotCaptureError
│   └── SnapshotNotFoundError
├── IntegrityError
│   ├── HashMismatchError
│   └── IntegrityVerificationError
├── DocumentError
│   ├── DocumentGenerationError
│   ├── DocumentNotFoundError
│   └── DocumentAlreadyIssuedError
├── EvidenceError
│   ├── EvidenceNotFoundError
│   ├── EvidenceUploadError
│   └── InvalidEvidenceFormatError
├── RepositoryError
│   ├── DatabaseError
│   └── ConcurrencyError
└── ExternalServiceError
    ├── NotificationServiceError
    └── SupplierServiceError
```

## 2. Error Classes (27 Total)

### 2.1 Base Error

```python
class ReceptionDifferenceError(Exception):
    """Base error for reception differences module."""
    error_code: str = "RECEPTION_DIFFERENCE_ERROR"
    status_code: int = 500
    message: str = "An unexpected error occurred"
```

### 2.2 Case Errors

| Error Class                | Code                     | Status | Description                           |
| -------------------------- | ------------------------ | ------ | ------------------------------------- |
| `CaseNotFoundError`        | `CASE_NOT_FOUND`         | 404    | Case with given ID not found          |
| `CaseAlreadyExistsError`   | `CASE_ALREADY_EXISTS`    | 409    | Duplicate case for reception          |
| `CaseValidationError`      | `CASE_VALIDATION_ERROR`  | 422    | Case data validation failed           |
| `InvalidCaseStatusError`   | `INVALID_CASE_STATUS`    | 422    | Invalid status for operation          |
| `InvalidTransitionError`   | `INVALID_TRANSITION`     | 422    | Status transition not allowed         |
| `MissingRequiredFieldError`| `MISSING_REQUIRED_FIELD` | 422    | Required field not provided           |
| `InvalidQuantityError`     | `INVALID_QUANTITY`       | 422    | Quantity value invalid                |
| `InvalidSeverityError`     | `INVALID_SEVERITY`       | 422    | Severity calculation failed           |

### 2.3 Authorization Errors

| Error Class                  | Code                       | Status | Description                         |
| ---------------------------- | -------------------------- | ------ | ----------------------------------- |
| `CaseAuthorizationError`     | `CASE_AUTHORIZATION_ERROR` | 403    | Base authorization error            |
| `InsufficientPermissionsError`| `INSUFFICIENT_PERMISSIONS`| 403    | User lacks required permission      |
| `StepUpAuthRequiredError`    | `STEP_UP_AUTH_REQUIRED`    | 403    | Re-authentication required          |
| `TenantMismatchError`        | `TENANT_MISMATCH`          | 403    | Cross-tenant access attempted       |

### 2.4 Item Errors

| Error Class                | Code                     | Status | Description                           |
| -------------------------- | ------------------------ | ------ | ------------------------------------- |
| `ItemNotFoundError`        | `ITEM_NOT_FOUND`         | 404    | Item with given ID not found          |
| `ItemValidationError`      | `ITEM_VALIDATION_ERROR`  | 422    | Item data validation failed           |
| `DuplicateItemError`       | `DUPLICATE_ITEM`         | 409    | Duplicate SKU in same case            |
| `InvalidItemTypeError`     | `INVALID_ITEM_TYPE`      | 422    | Item type not allowed                 |
| `ItemStatusConflictError`  | `ITEM_STATUS_CONFLICT`   | 422    | Item status incompatible with case    |

### 2.5 Snapshot Errors

| Error Class              | Code                   | Status | Description                         |
| ------------------------ | ---------------------- | ------ | ----------------------------------- |
| `SnapshotError`          | `SNAPSHOT_ERROR`       | 500    | Base snapshot error                 |
| `SnapshotCaptureError`   | `SNAPSHOT_CAPTURE_ERROR`| 500   | Failed to capture snapshot          |
| `SnapshotNotFoundError`  | `SNAPSHOT_NOT_FOUND`   | 404    | Snapshot not found                  |

### 2.6 Integrity Errors

| Error Class                   | Code                        | Status | Description                    |
| ----------------------------- | --------------------------- | ------ | ------------------------------ |
| `IntegrityError`              | `INTEGRITY_ERROR`           | 500    | Base integrity error           |
| `HashMismatchError`           | `HASH_MISMATCH`             | 409    | Canonical hash verification failed |
| `IntegrityVerificationError`  | `INTEGRITY_VERIFICATION_ERROR`| 500  | Integrity check failed         |

### 2.7 Document Errors

| Error Class                   | Code                         | Status | Description                   |
| ----------------------------- | ---------------------------- | ------ | ----------------------------- |
| `DocumentError`               | `DOCUMENT_ERROR`             | 500    | Base document error           |
| `DocumentGenerationError`     | `DOCUMENT_GENERATION_ERROR`  | 500    | PDF generation failed         |
| `DocumentNotFoundError`       | `DOCUMENT_NOT_FOUND`         | 404    | Document not found            |
| `DocumentAlreadyIssuedError`  | `DOCUMENT_ALREADY_ISSUED`    | 409    | Document already generated    |

### 2.8 Evidence Errors

| Error Class                   | Code                         | Status | Description                   |
| ----------------------------- | ---------------------------- | ------ | ----------------------------- |
| `EvidenceError`               | `EVIDENCE_ERROR`             | 500    | Base evidence error           |
| `EvidenceNotFoundError`       | `EVIDENCE_NOT_FOUND`         | 404    | Evidence not found            |
| `EvidenceUploadError`         | `EVIDENCE_UPLOAD_ERROR`      | 500    | Upload failed                 |
| `InvalidEvidenceFormatError`  | `INVALID_EVIDENCE_FORMAT`    | 422    | Unsupported evidence format   |

### 2.9 Repository & External Errors

| Error Class                   | Code                         | Status | Description                   |
| ----------------------------- | ---------------------------- | ------ | ----------------------------- |
| `RepositoryError`             | `REPOSITORY_ERROR`           | 500    | Base repository error         |
| `DatabaseError`               | `DATABASE_ERROR`             | 500    | Database operation failed     |
| `ConcurrencyError`            | `CONCURRENCY_ERROR`          | 409    | Optimistic lock conflict      |
| `ExternalServiceError`        | `EXTERNAL_SERVICE_ERROR`     | 502    | External service failure      |
| `NotificationServiceError`    | `NOTIFICATION_SERVICE_ERROR` | 502    | Notification delivery failed  |
| `SupplierServiceError`        | `SUPPLIER_SERVICE_ERROR`     | 502    | Supplier API failure          |

## 3. Error Response Format

```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "Cannot transition from CLOSED to SUBMITTED",
    "details": {
      "current_status": "CLOSED",
      "target_status": "SUBMITTED",
      "allowed_transitions": ["CANCELLED"]
    },
    "timestamp": "2026-08-02T17:00:00Z",
    "request_id": "req_abc123"
  }
}
```

---

**See also**: `39_error_responses.md` for API error response format
