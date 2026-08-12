# Phase 040 — Request/Response Examples

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Create Case

### Request

```http
POST /api/v1/reception-differences/cases
Content-Type: application/json
Authorization: Bearer <token>

{
  "reception_id": "REC-2026-001234",
  "category": "DAMAGED",
  "description": "3 items arrived with packaging damage",
  "supplier_id": "SUP-001",
  "warehouse_id": "WH-001",
  "items": [
    {
      "sku": "PROD-001",
      "item_type": "PRODUCT",
      "expected_qty": "100.000",
      "received_qty": "95.000",
      "unit_cost": "25.50"
    },
    {
      "sku": "PROD-002",
      "item_type": "PRODUCT",
      "expected_qty": "50.000",
      "received_qty": "48.000",
      "unit_cost": "45.00"
    }
  ]
}
```

### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DETECTED",
  "severity": "MEDIUM",
  "category": "DAMAGED",
  "description": "3 items arrived with packaging damage",
  "reception_id": "REC-2026-001234",
  "supplier_id": "SUP-001",
  "warehouse_id": "WH-001",
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "sku": "PROD-001",
      "item_type": "PRODUCT",
      "status": "PENDING",
      "expected_qty": "100.000",
      "received_qty": "95.000",
      "difference_qty": "5.000",
      "unit_cost": "25.50",
      "total_impact": "127.50"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440002",
      "sku": "PROD-002",
      "item_type": "PRODUCT",
      "status": "PENDING",
      "expected_qty": "50.000",
      "received_qty": "48.000",
      "difference_qty": "2.000",
      "unit_cost": "45.00",
      "total_impact": "90.00"
    }
  ],
  "evidence_count": 0,
  "canonical_hash": "a1b2c3d4e5f6...",
  "created_at": "2026-08-02T10:30:00Z",
  "updated_at": "2026-08-02T10:30:00Z",
  "created_by": "user-123"
}
```

## 2. List Cases

### Request

```http
GET /api/v1/reception-differences/cases?status=IN_REVIEW&severity=HIGH&page=1&size=10
Authorization: Bearer <token>
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "IN_REVIEW",
      "severity": "HIGH",
      "category": "DAMAGED",
      "items_count": 5,
      "total_impact": "$1,250.00",
      "created_at": "2026-08-01T10:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "size": 10,
  "pages": 3
}
```

## 3. Submit Case

### Request

```http
POST /api/v1/reception-differences/cases/550e8400-e29b-41d4-a716-446655440000/submit
Authorization: Bearer <token>
```

### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUBMITTED",
  "submitted_at": "2026-08-02T11:00:00Z"
}
```

## 4. Formalize Candidates

### Request

```http
POST /api/v1/reception-differences/cases/550e8400-e29b-41d4-a716-446655440000/formalize
Content-Type: application/json
Authorization: Bearer <token>

{
  "candidates": [
    {
      "sku": "PROD-001",
      "item_type": "PRODUCT",
      "expected_qty": "100.000",
      "received_qty": "95.000",
      "unit_cost": "25.50",
      "notes": "5 units damaged in transit"
    }
  ]
}
```

### Response (200 OK)

```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 1,
  "formalized": 1,
  "rejected": 0,
  "errors": []
}
```

## 5. Issue Document

### Request

```http
POST /api/v1/reception-differences/cases/550e8400-e29b-41d4-a716-446655440000/documents/issue
Authorization: Bearer <token>
```

### Response (200 OK)

```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_number": "DIF-2026-000001",
  "document_url": "https://storage.example.com/dif/550e8400/DIF-2026-000001.pdf",
  "issued_at": "2026-08-02T14:00:00Z"
}
```

## 6. Error Response

### Response (422 Unprocessable Entity)

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

---

**See also**: `38_validation_rules.md` for validation details
