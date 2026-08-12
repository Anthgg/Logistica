# Phase 040 — Manual Creation Service

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/application/manual_creation_service.py`

## 1. Overview

The manual creation service allows operators to manually create difference cases when automatic detection is not available.

## 2. Manual Creation Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Form    │───▶│ Validate │───▶│  Create  │───▶│  Notify  │
│  Input   │    │  Data    │    │  Case    │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 3. Implementation

```python
class ManualCreationService:
    """Manual case creation service."""
    
    def __init__(
        self,
        case_repository: CaseRepository,
        item_repository: ItemRepository,
        notification_service: NotificationService,
    ):
        self.case_repository = case_repository
        self.item_repository = item_repository
        self.notification_service = notification_service
    
    async def create_case_manually(
        self,
        dto: ManualCaseDTO,
        user_id: str,
        tenant_id: str,
    ) -> CaseAggregate:
        """
        Create case manually from operator input.
        
        Validates all required fields and business rules.
        """
        # Validate reception ID
        if not dto.reception_id:
            raise MissingRequiredFieldError("reception_id")
        
        # Check for existing case
        existing = await self.case_repository.get_by_reception(
            dto.reception_id,
            tenant_id,
        )
        if existing:
            raise CaseAlreadyExistsError(dto.reception_id)
        
        # Create case
        case = CaseAggregate(
            id=uuid4(),
            tenant_id=tenant_id,
            status=CaseStatus.DRAFT,
            severity=Severity.LOW,
            category=dto.category,
            description=dto.description,
            reception_id=dto.reception_id,
            supplier_id=dto.supplier_id,
            warehouse_id=dto.warehouse_id,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Add items
        for item_dto in dto.items:
            item = await self._create_item(case, item_dto, user_id)
            case.items.append(item)
        
        # Calculate severity
        total_impact = sum(
            item.total_impact.value
            for item in case.items
            if item.total_impact
        )
        case.severity = calculate_severity(
            total_impact=MonetaryAmount(value=total_impact),
            category=case.category,
            item_count=len(case.items),
        )
        
        # Compute hash
        case.canonical_hash = canonical_hash_diff(case)
        
        # Save
        await self.case_repository.save(case)
        
        return case
    
    async def _create_item(
        self,
        case: CaseAggregate,
        dto: CreateItemDTO,
        user_id: str,
    ) -> ItemAggregate:
        """Create a single item."""
        item = ItemAggregate(
            id=uuid4(),
            case_id=case.id,
            sku=dto.sku,
            item_type=dto.item_type,
            status=ItemStatus.PENDING,
            expected_qty=dto.expected_qty,
            received_qty=dto.received_qty,
            unit_cost=dto.unit_cost,
            notes=dto.notes,
            created_by=user_id,
            created_at=datetime.utcnow(),
        )
        
        # Calculate difference
        item.difference_qty, item.total_impact = strict_decimal_diff(
            item.expected_qty,
            item.received_qty,
            item.unit_cost,
        )
        
        await self.item_repository.save(item)
        
        return item
```

## 4. Manual Case DTO

```python
@dataclass
class ManualCaseDTO:
    reception_id: str
    category: DifferenceCategory
    description: str
    supplier_id: Optional[str]
    warehouse_id: Optional[str]
    items: List[CreateItemDTO]
```

## 5. Validation Rules

| Field           | Rule                                    |
| --------------- | --------------------------------------- |
| `reception_id`  | Required, unique per tenant             |
| `category`      | Must be valid DifferenceCategory        |
| `description`   | Required, max 1000 chars                |
| `items`         | At least one item required              |
| `sku`           | Required, unique within case            |
| `expected_qty`  | Must be > 0                             |
| `received_qty`  | Must be >= 0                            |

---

**See also**: `19_case_service.md` for case operations
