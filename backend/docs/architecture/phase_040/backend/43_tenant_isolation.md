# Phase 040 — Tenant Isolation

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

All data is isolated by tenant using row-level security.

## 2. Isolation Mechanism

### 2.1 Database Level

```python
# Every query includes tenant_id filter
async def get_case(
    case_id: CaseId,
    tenant_id: str,
) -> CaseAggregate:
    """Get case with tenant isolation."""
    result = await session.execute(
        select(CaseModel).where(
            CaseModel.id == case_id,
            CaseModel.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()
```

### 2.2 Repository Level

```python
class CaseRepositoryImpl:
    """Repository with tenant isolation."""
    
    async def list(
        self,
        tenant_id: str,
        filters: Optional[CaseFilters] = None,
    ) -> List[CaseAggregate]:
        """List cases for tenant."""
        query = select(CaseModel).where(
            CaseModel.tenant_id == tenant_id
        )
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        result = await self.session.execute(query)
        return [self._to_domain(m) for m in result.scalars()]
```

## 3. Tenant Context

```python
from contextvars import ContextVar

tenant_context: ContextVar[str] = ContextVar("tenant_id")

def get_current_tenant() -> str:
    """Get current tenant from context."""
    return tenant_context.get()

@app.middleware("http")
async def set_tenant_context(request, call_next):
    """Set tenant context from JWT."""
    token = request.headers.get("Authorization")
    if token:
        payload = decode_jwt(token)
        tenant_context.set(payload["tenant_id"])
    
    response = await call_next(request)
    return response
```

## 4. Cross-Tenant Prevention

```python
async def verify_tenant_access(
    case: CaseAggregate,
    user: User,
) -> None:
    """Verify user has access to case's tenant."""
    if case.tenant_id != user.tenant_id:
        raise TenantMismatchError()
```

## 5. Isolation Guarantees

| Guarantee                 | Implementation                          |
| ------------------------- | --------------------------------------- |
| Data isolation            | Row-level `tenant_id` filter            |
| Query isolation           | Automatic tenant filtering              |
| Cross-tenant prevention   | Explicit tenant verification            |
| Audit trail isolation     | Tenant-scoped audit logs                |

---

**See also**: `44_audit_logging.md` for tenant-scoped auditing
