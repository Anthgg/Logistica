# Phase 040 — Formalization Service

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/application/formalization_service.py`

## 1. Overview

The formalization service converts candidate items into formal case items, validating business rules and ensuring data consistency.

## 2. Formalization Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Candidate │───▶│ Validate │───▶│Create Item│───▶│ Update   │
│  Data    │    │  Rules   │    │          │    │ Severity │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      │               │               │               │
      ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Received │    │ Invalid  │    │ Duplicate│    │ Case     │
│          │    │ Rejected │    │ Error    │    │ Updated  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 3. Implementation

```python
class FormalizationService:
    """Candidate formalization logic."""
    
    def __init__(
        self,
        item_repository: ItemRepository,
        case_repository: CaseRepository,
        notification_service: NotificationService,
    ):
        self.item_repository = item_repository
        self.case_repository = case_repository
        self.notification_service = notification_service
    
    async def formalize_candidates(
        self,
        case_id: CaseId,
        candidates: List[CandidateItemDTO],
        user_id: str,
        tenant_id: str,
    ) -> FormalizationResult:
        """
        Formalize multiple candidate items.
        
        Args:
            case_id: Parent case ID
            candidates: List of candidate items
            user_id: User performing formalization
            tenant_id: Tenant for authorization
            
        Returns:
            FormalizationResult with success/failure details
        """
        case = await self.case_repository.get(case_id)
        
        # Verify tenant
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Verify case status
        if case.status not in (CaseStatus.DRAFT, CaseStatus.SUBMITTED):
            raise CaseValidationError(
                "Cannot formalize items when case is not in DRAFT or SUBMITTED"
            )
        
        result = FormalizationResult(
            case_id=case_id,
            total=len(candidates),
            formalized=0,
            rejected=0,
            errors=[],
        )
        
        for candidate in candidates:
            try:
                await self._formalize_single(
                    case, candidate, user_id
                )
                result.formalized += 1
            except Exception as e:
                result.rejected += 1
                result.errors.append({
                    "sku": candidate.sku,
                    "error": str(e),
                })
        
        # Recalculate severity
        await self._update_case_severity(case)
        
        # Notify if partial success
        if result.rejected > 0:
            await self.notification_service.notify_partial_formalization(
                case, result
            )
        
        return result
    
    async def _formalize_single(
        self,
        case: CaseAggregate,
        candidate: CandidateItemDTO,
        user_id: str,
    ) -> ItemAggregate:
        """Formalize a single candidate item."""
        # Validate SKU
        if not candidate.sku:
            raise ItemValidationError("SKU is required")
        
        # Check duplicate
        existing_skus = {item.sku for item in case.items}
        if candidate.sku in existing_skus:
            raise DuplicateItemError(candidate.sku)
        
        # Validate quantities
        if candidate.expected_qty <= 0:
            raise InvalidQuantityError("Expected quantity must be positive")
        
        if candidate.received_qty < 0:
            raise InvalidQuantityError("Received quantity cannot be negative")
        
        # Create item
        item = ItemAggregate(
            id=uuid4(),
            case_id=case.id,
            sku=candidate.sku,
            item_type=candidate.item_type,
            status=ItemStatus.FORMALIZED,
            expected_qty=candidate.expected_qty,
            received_qty=candidate.received_qty,
            unit_cost=candidate.unit_cost,
            formalized_at=datetime.utcnow(),
            formalized_by=user_id,
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
        
        # Add to case
        case.items.append(item)
        
        # Emit event
        await publish_domain_event(
            "ItemFormalized",
            str(case.id),
            {"case_id": str(case.id), "item_id": str(item.id)},
            case.tenant_id,
        )
        
        return item
```

## 4. Formalization Result

```python
@dataclass
class FormalizationResult:
    case_id: CaseId
    total: int
    formalized: int
    rejected: int
    errors: List[dict]
```

## 5. Candidate DTO

```python
@dataclass
class CandidateItemDTO:
    sku: str
    item_type: ItemType
    expected_qty: Quantity
    received_qty: Quantity
    unit_cost: Optional[MonetaryAmount] = None
    notes: Optional[str] = None
```

---

**See also**: `20_item_service.md` for item operations
