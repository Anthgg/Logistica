# Phase 040 — Item Service

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/application/item_service.py`

## 1. Overview

`ItemService` manages individual items within a case.

## 2. Operations

| Operation              | Method                    | Description                        |
| ---------------------- | ------------------------- | ---------------------------------- |
| Add item               | `add_item()`              | Add item to case                   |
| Update item            | `update_item()`           | Update item details                |
| Remove item            | `remove_item()`           | Remove item from case              |
| Formalize item         | `formalize_item()`        | Formalize candidate item           |
| Reject item            | `reject_item()`           | Reject item during review          |
| Resolve item           | `resolve_item()`          | Mark item as resolved              |
| Bulk formalize         | `bulk_formalize_items()`  | Formalize multiple items           |

## 3. Implementation

```python
class ItemService:
    """Item management service."""
    
    def __init__(
        self,
        item_repository: ItemRepository,
        case_repository: CaseRepository,
        snapshot_provider: SnapshotProvider,
    ):
        self.item_repository = item_repository
        self.case_repository = case_repository
        self.snapshot_provider = snapshot_provider
    
    async def add_item(
        self,
        case_id: CaseId,
        dto: AddItemDTO,
        user_id: str,
    ) -> ItemAggregate:
        """Add item to case."""
        case = await self.case_repository.get(case_id)
        
        # Check duplicate SKU
        existing_skus = {item.sku for item in case.items}
        if dto.sku in existing_skus:
            raise DuplicateItemError(dto.sku)
        
        # Create item
        item = ItemAggregate(
            id=uuid4(),
            case_id=case_id,
            sku=dto.sku,
            item_type=dto.item_type,
            status=ItemStatus.PENDING,
            expected_qty=dto.expected_qty,
            received_qty=dto.received_qty,
            unit_cost=dto.unit_cost,
            created_by=user_id,
            created_at=datetime.utcnow(),
        )
        
        # Calculate difference
        item.difference_qty, item.total_impact = strict_decimal_diff(
            item.expected_qty,
            item.received_qty,
            item.unit_cost,
        )
        
        # Save
        await self.item_repository.save(item)
        
        # Recalculate case severity
        await self._recalculate_case_severity(case)
        
        return item
    
    async def formalize_item(
        self,
        item_id: ItemId,
        user_id: str,
        tenant_id: str,
    ) -> ItemAggregate:
        """Formalize a pending item."""
        item = await self.item_repository.get(item_id)
        case = await self.case_repository.get(item.case_id)
        
        # Verify tenant
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Validate item can be formalized
        if item.status != ItemStatus.PENDING:
            raise ItemStatusConflictError(
                f"Cannot formalize item in {item.status.value} status"
            )
        
        # Formalize
        item.status = ItemStatus.FORMALIZED
        item.formalized_at = datetime.utcnow()
        item.formalized_by = user_id
        
        # Save
        await self.item_repository.save(item)
        
        return item
    
    async def reject_item(
        self,
        item_id: ItemId,
        reason: str,
        user_id: str,
        tenant_id: str,
    ) -> ItemAggregate:
        """Reject item during review."""
        item = await self.item_repository.get(item_id)
        case = await self.case_repository.get(item.case_id)
        
        # Verify tenant
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Validate
        if case.status != CaseStatus.IN_REVIEW:
            raise ItemStatusConflictError(
                "Cannot reject item when case is not in review"
            )
        
        if not reason:
            raise ItemValidationError("Rejection reason is required")
        
        # Reject
        item.status = ItemStatus.REJECTED
        item.rejection_reason = reason
        item.rejected_at = datetime.utcnow()
        item.rejected_by = user_id
        
        # Save
        await self.item_repository.save(item)
        
        return item
    
    async def resolve_item(
        self,
        item_id: ItemId,
        resolution: str,
        user_id: str,
        tenant_id: str,
    ) -> ItemAggregate:
        """Mark item as resolved."""
        item = await self.item_repository.get(item_id)
        case = await self.case_repository.get(item.case_id)
        
        # Verify tenant
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Validate
        if case.status not in (CaseStatus.APPROVED, CaseStatus.PENDING_CLOSE):
            raise ItemStatusConflictError(
                "Cannot resolve item when case is not approved or pending close"
            )
        
        # Resolve
        item.status = ItemStatus.RESOLVED
        item.resolution = resolution
        item.resolved_at = datetime.utcnow()
        item.resolved_by = user_id
        
        # Save
        await self.item_repository.save(item)
        
        return item
    
    async def _recalculate_case_severity(
        self,
        case: CaseAggregate,
    ) -> None:
        """Recalculate case severity based on items."""
        total_impact = sum(
            item.total_impact.value
            for item in case.items
            if item.total_impact
        )
        
        new_severity = calculate_severity(
            total_impact=MonetaryAmount(value=total_impact),
            category=case.category,
            item_count=len(case.items),
        )
        
        if new_severity != case.severity:
            case.severity = new_severity
            case.updated_at = datetime.utcnow()
            await self.case_repository.save(case)
```

## 4. Validation Rules

| Rule                          | Validation                          |
| ----------------------------- | ----------------------------------- |
| SKU uniqueness                | No duplicate SKU in same case       |
| Quantity non-negative         | `received_qty` >= 0                 |
| Expected quantity positive    | `expected_qty` > 0                  |
| Status consistency            | Item status must match case state   |
| Formalization prerequisites   | SKU required, case in DRAFT/SUBMITTED |

---

**See also**: `21_formalization_service.md` for formalization workflow
