# Phase 040 — Schemas

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/presentation/schemas.py`

## 1. Overview

31 Pydantic models for request/response validation.

## 2. Schema Categories

| Category        | Count | Purpose                      |
| --------------- | ----- | ---------------------------- |
| Request         | 12    | Input validation             |
| Response        | 10    | Output serialization         |
| Internal        | 6     | Service layer DTOs           |
| Error           | 3     | Error response formats       |

## 3. Request Schemas

### 3.1 CreateCaseRequest

```python
class CreateCaseRequest(BaseModel):
    reception_id: str = Field(..., min_length=1, max_length=100)
    category: DifferenceCategory
    description: str = Field(..., min_length=1, max_length=1000)
    supplier_id: Optional[str] = Field(None, max_length=100)
    warehouse_id: Optional[str] = Field(None, max_length=100)
    items: List[CreateItemRequest] = Field(..., min_length=1)
```

### 3.2 CreateItemRequest

```python
class CreateItemRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    item_type: ItemType
    expected_qty: Decimal = Field(..., gt=0)
    received_qty: Decimal = Field(..., ge=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)
```

### 3.3 FormalizeCandidatesRequest

```python
class FormalizeCandidatesRequest(BaseModel):
    candidates: List[CandidateItemRequest] = Field(..., min_length=1)

class CandidateItemRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    item_type: ItemType
    expected_qty: Decimal = Field(..., gt=0)
    received_qty: Decimal = Field(..., ge=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)
```

### 3.4 SubmitCaseRequest

```python
class SubmitCaseRequest(BaseModel):
    pass  # No additional fields needed
```

### 3.5 IssueDocumentRequest

```python
class IssueDocumentRequest(BaseModel):
    pass  # No additional fields needed
```

### 3.6 CloseCaseRequest

```python
class CloseCaseRequest(BaseModel):
    resolution_notes: Optional[str] = Field(None, max_length=1000)
```

### 3.7 ReviewCaseRequest

```python
class ReviewCaseRequest(BaseModel):
    action: ReviewAction
    comments: Optional[str] = Field(None, max_length=1000)
```

### 3.8 AssignResponsibilityRequest

```python
class AssignResponsibilityRequest(BaseModel):
    responsibility: ResponsibilityType
    justification: str = Field(..., min_length=1, max_length=1000)
```

### 3.9 OverrideSeverityRequest

```python
class OverrideSeverityRequest(BaseModel):
    severity: Severity
    justification: str = Field(..., min_length=1, max_length=1000)
```

### 3.10 UploadEvidenceRequest

```python
class UploadEvidenceRequest(BaseModel):
    evidence_type: EvidenceFormat
    description: Optional[str] = Field(None, max_length=500)
```

### 3.11 ListCasesRequest

```python
class ListCasesRequest(BaseModel):
    status: Optional[CaseStatus] = None
    severity: Optional[Severity] = None
    category: Optional[DifferenceCategory] = None
    supplier_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at")
    sort_order: str = Field("desc", regex="^(asc|desc)$")
```

### 3.12 GetCaseRequest

```python
class GetCaseRequest(BaseModel):
    case_id: str = Field(..., format="uuid")
```

## 4. Response Schemas

### 4.1 CaseResponse

```python
class CaseResponse(BaseModel):
    id: str
    status: CaseStatus
    severity: Severity
    category: DifferenceCategory
    description: Optional[str]
    reception_id: str
    supplier_id: Optional[str]
    warehouse_id: Optional[str]
    responsible_party: Optional[str]
    items: List[ItemResponse]
    evidence_count: int
    canonical_hash: str
    created_at: datetime
    updated_at: datetime
    created_by: str
```

### 4.2 ItemResponse

```python
class ItemResponse(BaseModel):
    id: str
    sku: str
    item_type: ItemType
    status: ItemStatus
    expected_qty: str
    received_qty: str
    difference_qty: str
    unit_cost: Optional[str]
    total_impact: Optional[str]
    notes: Optional[str]
```

### 4.3 ListCasesResponse

```python
class ListCasesResponse(BaseModel):
    items: List[CaseSummaryResponse]
    total: int
    page: int
    size: int
    pages: int
```

### 4.4 CaseSummaryResponse

```python
class CaseSummaryResponse(BaseModel):
    id: str
    status: CaseStatus
    severity: Severity
    category: DifferenceCategory
    items_count: int
    total_impact: str
    created_at: datetime
```

### 4.5 FormalizationResponse

```python
class FormalizationResponse(BaseModel):
    case_id: str
    total: int
    formalized: int
    rejected: int
    errors: List[dict]
```

### 4.6 DocumentResponse

```python
class DocumentResponse(BaseModel):
    case_id: str
    document_number: str
    document_url: str
    issued_at: datetime
```

### 4.7 IntegrityResponse

```python
class IntegrityResponse(BaseModel):
    case_id: str
    is_valid: bool
    stored_hash: str
    recomputed_hash: str
    verified_at: datetime
```

### 4.8 SnapshotResponse

```python
class SnapshotResponse(BaseModel):
    snapshot_id: str
    case_id: str
    captured_at: datetime
    captured_by: str
    reason: str
```

### 4.9 ErrorResponse

```python
class ErrorResponse(BaseModel):
    error: ErrorDetail

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None
    timestamp: str
    request_id: Optional[str] = None
```

### 4.10 PaginationResponse

```python
class PaginationResponse(BaseModel):
    page: int
    size: int
    total: int
    pages: int
```

---

**See also**: `36_router.md` for endpoint definitions
