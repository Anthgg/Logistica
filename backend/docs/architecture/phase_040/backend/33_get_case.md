# Phase 040 — Get Case Query

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The `GetCase` query retrieves a single case by ID with all related data.

## 2. Query Structure

```python
@dataclass
class GetCase(Query):
    """Get case by ID."""
    case_id: str
```

## 3. Handler

```python
async def get_case_handler(
    query: GetCase,
) -> QueryResult:
    """Handle GetCase query."""
    case = await case_repository.get(query.case_id)
    
    if case is None:
        raise CaseNotFoundError(query.case_id)
    
    if case.tenant_id != query.tenant_id:
        raise TenantMismatchError()
    
    return QueryResult(
        data=case_to_dict(case),
    )
```

## 4. Response Schema

```python
def case_to_dict(case: CaseAggregate) -> dict:
    """Convert case to response dict."""
    return {
        "id": str(case.id),
        "status": case.status.value,
        "severity": case.severity.value,
        "category": case.category.value,
        "description": case.description,
        "reception_id": case.reception_id,
        "supplier_id": case.supplier_id,
        "warehouse_id": case.warehouse_id,
        "responsible_party": case.responsible_party,
        "items": [
            {
                "id": str(item.id),
                "sku": item.sku,
                "item_type": item.item_type.value,
                "status": item.status.value,
                "expected_qty": str(item.expected_qty),
                "received_qty": str(item.received_qty),
                "difference_qty": str(item.difference_qty),
                "unit_cost": str(item.unit_cost) if item.unit_cost else None,
                "total_impact": str(item.total_impact) if item.total_impact else None,
            }
            for item in case.items
        ],
        "evidence_count": len(case.evidence_links),
        "canonical_hash": case.canonical_hash.value,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
        "created_by": case.created_by,
    }
```

## 5. Authorization

| Check                 | Required                                |
| --------------------- | --------------------------------------- |
| Authentication        | Yes                                     |
| Tenant isolation      | Case tenant must match user tenant      |
| Role                  | Any authenticated user                  |

---

**See also**: `34_list_cases.md` for list query
