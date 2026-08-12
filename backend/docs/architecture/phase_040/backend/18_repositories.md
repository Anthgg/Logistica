# Phase 040 — Repositories

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

Repository implementations provide data access for domain aggregates.

**Source**: `app/modules/logistics/inbound/reception_differences/infrastructure/repositories.py`

## 2. Repository Interfaces

### 2.1 CaseRepository

```python
class CaseRepository(Protocol):
    """Case aggregate repository interface."""
    
    async def get(self, case_id: CaseId) -> CaseAggregate:
        """Get case by ID."""
        ...
    
    async def get_by_reception(
        self, 
        reception_id: str,
        tenant_id: str,
    ) -> Optional[CaseAggregate]:
        """Get case by reception ID."""
        ...
    
    async def list(
        self,
        tenant_id: str,
        filters: Optional[CaseFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> List[CaseAggregate]:
        """List cases with filters."""
        ...
    
    async def list_active(
        self,
        tenant_id: str,
    ) -> List[CaseAggregate]:
        """List all active (non-terminal) cases."""
        ...
    
    async def list_by_status(
        self,
        status: CaseStatus,
        tenant_id: str,
    ) -> List[CaseAggregate]:
        """List cases by status."""
        ...
    
    async def save(self, case: CaseAggregate) -> None:
        """Save or update case."""
        ...
    
    async def delete(self, case_id: CaseId) -> None:
        """Delete case (soft delete)."""
        ...
    
    async def count(
        self,
        tenant_id: str,
        filters: Optional[CaseFilters] = None,
    ) -> int:
        """Count cases matching filters."""
        ...
```

### 2.2 ItemRepository

```python
class ItemRepository(Protocol):
    """Item aggregate repository interface."""
    
    async def get(self, item_id: ItemId) -> ItemAggregate:
        """Get item by ID."""
        ...
    
    async def get_by_case(
        self,
        case_id: CaseId,
    ) -> List[ItemAggregate]:
        """Get all items for a case."""
        ...
    
    async def save(self, item: ItemAggregate) -> None:
        """Save or update item."""
        ...
    
    async def delete(self, item_id: ItemId) -> None:
        """Delete item."""
        ...
    
    async def bulk_save(
        self,
        items: List[ItemAggregate],
    ) -> None:
        """Save multiple items atomically."""
        ...
```

### 2.3 SnapshotRepository

```python
class SnapshotRepository(Protocol):
    """Snapshot repository interface."""
    
    async def get(self, snapshot_id: str) -> Snapshot:
        """Get snapshot by ID."""
        ...
    
    async def get_latest(
        self,
        case_id: CaseId,
    ) -> Optional[Snapshot]:
        """Get most recent snapshot for case."""
        ...
    
    async def list(
        self,
        case_id: CaseId,
        limit: int = 10,
    ) -> List[Snapshot]:
        """List recent snapshots for case."""
        ...
    
    async def save(self, snapshot: Snapshot) -> None:
        """Save snapshot."""
        ...
    
    async def delete(self, snapshot_id: str) -> None:
        """Delete snapshot."""
        ...
```

## 3. Implementations

### 3.1 CaseRepositoryImpl

```python
class CaseRepositoryImpl(CaseRepository):
    """PostgreSQL implementation of CaseRepository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, case_id: CaseId) -> CaseAggregate:
        result = await self.session.execute(
            select(CaseModel).where(CaseModel.id == case_id)
        )
        model = result.scalar_one_or_none()
        
        if model is None:
            raise CaseNotFoundError(case_id)
        
        return self._to_domain(model)
    
    async def save(self, case: CaseAggregate) -> None:
        model = self._to_model(case)
        
        existing = await self.session.get(CaseModel, case.id)
        if existing:
            await self.session.merge(model)
        else:
            self.session.add(model)
        
        await self.session.flush()
    
    def _to_domain(self, model: CaseModel) -> CaseAggregate:
        """Convert ORM model to domain aggregate."""
        return CaseAggregate(
            id=model.id,
            tenant_id=model.tenant_id,
            status=CaseStatus(model.status),
            severity=Severity(model.severity),
            category=DifferenceCategory(model.category),
            description=model.description,
            reception_id=model.reception_id,
            supplier_id=model.supplier_id,
            warehouse_id=model.warehouse_id,
            responsible_party=model.responsible_party,
            canonical_hash=CanonicalHash(value=model.canonical_hash),
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            items=[self._to_item_domain(item) for item in model.items],
        )
    
    def _to_model(self, aggregate: CaseAggregate) -> CaseModel:
        """Convert domain aggregate to ORM model."""
        return CaseModel(
            id=aggregate.id,
            tenant_id=aggregate.tenant_id,
            status=aggregate.status.value,
            severity=aggregate.severity.value,
            category=aggregate.category.value,
            description=aggregate.description,
            reception_id=aggregate.reception_id,
            supplier_id=aggregate.supplier_id,
            warehouse_id=aggregate.warehouse_id,
            responsible_party=aggregate.responsible_party,
            canonical_hash=aggregate.canonical_hash.value,
            created_by=aggregate.created_by,
            created_at=aggregate.created_at,
            updated_at=aggregate.updated_at,
        )
```

## 4. Query Examples

```python
# List cases with filters
filters = CaseFilters(
    status=CaseStatus.IN_REVIEW,
    severity=Severity.HIGH,
    category=DifferenceCategory.DAMAGED,
    supplier_id="SUP-001",
)

cases = await case_repository.list(
    tenant_id="tenant_123",
    filters=filters,
    pagination=PaginationParams(page=1, size=20),
)

# Count cases
total = await case_repository.count(
    tenant_id="tenant_123",
    filters=filters,
)
```

## 5. Transaction Management

```python
async def save_case_with_items(
    case: CaseAggregate,
    items: List[ItemAggregate],
) -> None:
    """Save case and items in single transaction."""
    async with session.begin():
        await case_repository.save(case)
        await item_repository.bulk_save(items)
```

---

**See also**: `11_orm_models.md` for ORM model definitions
