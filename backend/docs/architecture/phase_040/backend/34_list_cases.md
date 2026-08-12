# Phase 040 — List Cases Query

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The `ListCases` query retrieves a paginated list of cases with optional filters.

## 2. Query Structure

```python
@dataclass
class ListCases(Query):
    """List cases with filters."""
    status: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    supplier_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    page: int = 1
    size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"
```

## 3. Handler

```python
async def list_cases_handler(
    query: ListCases,
) -> QueryResult:
    """Handle ListCases query."""
    filters = CaseFilters(
        status=CaseStatus(query.status) if query.status else None,
        severity=Severity(query.severity) if query.severity else None,
        category=DifferenceCategory(query.category) if query.category else None,
        supplier_id=query.supplier_id,
        warehouse_id=query.warehouse_id,
    )
    
    pagination = PaginationParams(
        page=query.page,
        size=query.size,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    
    cases = await case_repository.list(
        tenant_id=query.tenant_id,
        filters=filters,
        pagination=pagination,
    )
    
    total = await case_repository.count(
        tenant_id=query.tenant_id,
        filters=filters,
    )
    
    return QueryResult(
        data=[case_to_dict(case) for case in cases],
        total=total,
    )
```

## 4. Filters

| Filter         | Type              | Description                      |
| -------------- | ----------------- | -------------------------------- |
| `status`       | `CaseStatus`      | Filter by status                 |
| `severity`     | `Severity`        | Filter by severity               |
| `category`     | `DifferenceCategory` | Filter by category            |
| `supplier_id`  | `str`             | Filter by supplier               |
| `warehouse_id` | `str`             | Filter by warehouse              |

## 5. Pagination

```python
@dataclass
class PaginationParams:
    page: int = 1
    size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"
```

## 6. Response Schema

```python
@dataclass
class ListCasesResponse:
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int
```

## 7. Example Response

```json
{
  "items": [
    {
      "id": "case-123",
      "status": "IN_REVIEW",
      "severity": "HIGH",
      "category": "DAMAGED",
      "items_count": 5,
      "total_impact": "$1,250.00",
      "created_at": "2026-08-01T10:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

---

**See also**: `33_get_case.md` for single case query
