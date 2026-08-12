# Phase 040 — Case Service

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/application/case_service.py`

## 1. Overview

`CaseService` orchestrates case lifecycle operations, coordinating domain services and repositories.

## 2. Operations

| Operation              | Method                    | Description                        |
| ---------------------- | ------------------------- | ---------------------------------- |
| Create case            | `create_case()`           | Create new difference case         |
| Get case               | `get_case()`              | Retrieve case by ID                |
| List cases             | `list_cases()`            | List cases with filters            |
| Update case            | `update_case()`           | Update case details                |
| Submit case            | `submit_case()`           | Submit for review                  |
| Approve case           | `approve_case()`          | Approve case                       |
| Reject case            | `reject_case()`           | Reject case with reason            |
| Close case             | `close_case()`            | Close resolved case                |
| Cancel case            | `cancel_case()`           | Cancel case                        |
| Escalate case          | `escalate_case()`         | Escalate to management             |
| Put on hold            | `hold_case()`             | Pause case processing              |
| Resume case            | `resume_case()`           | Resume from hold                   |

## 3. Implementation

```python
class CaseService:
    """Case lifecycle orchestration service."""
    
    def __init__(
        self,
        case_repository: CaseRepository,
        item_repository: ItemRepository,
        snapshot_provider: SnapshotProvider,
        integrity_service: IntegrityService,
        notification_service: NotificationService,
    ):
        self.case_repository = case_repository
        self.item_repository = item_repository
        self.snapshot_provider = snapshot_provider
        self.integrity_service = integrity_service
        self.notification_service = notification_service
    
    async def create_case(
        self,
        dto: CreateCaseDTO,
        user_id: str,
        tenant_id: str,
    ) -> CaseAggregate:
        """Create new reception difference case."""
        # Check for existing case
        existing = await self.case_repository.get_by_reception(
            dto.reception_id,
            tenant_id,
        )
        if existing:
            raise CaseAlreadyExistsError(dto.reception_id)
        
        # Create aggregate
        case = CaseAggregate(
            id=uuid4(),
            tenant_id=tenant_id,
            status=CaseStatus.DETECTED,
            severity=Severity.LOW,  # Will be calculated
            category=dto.category,
            description=dto.description,
            reception_id=dto.reception_id,
            supplier_id=dto.supplier_id,
            warehouse_id=dto.warehouse_id,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Calculate severity
        case.severity = calculate_severity(
            total_impact=dto.total_impact,
            category=dto.category,
            item_count=len(dto.items),
        )
        
        # Compute canonical hash
        case.canonical_hash = canonical_hash_diff(case)
        
        # Save
        await self.case_repository.save(case)
        
        # Publish event
        await publish_domain_event(
            "CaseCreated",
            str(case.id),
            {"case_id": str(case.id), "category": case.category.value},
            tenant_id,
        )
        
        return case
    
    async def submit_case(
        self,
        case_id: CaseId,
        user_id: str,
        tenant_id: str,
    ) -> CaseAggregate:
        """Submit case for review."""
        case = await self.case_repository.get(case_id)
        
        # Verify tenant
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Capture snapshot
        await self.snapshot_provider.capture(
            case,
            SnapshotReason.PRE_TRANSITION,
            user_id,
        )
        
        # Validate transition
        require_case_transition(
            case.status,
            CaseStatus.SUBMITTED,
            user_roles=await self._get_user_roles(user_id),
        )
        
        # Apply transition
        case.status = CaseStatus.SUBMITTED
        case.updated_at = datetime.utcnow()
        
        # Recompute hash
        case.canonical_hash = canonical_hash_diff(case)
        
        # Save
        await self.case_repository.save(case)
        
        # Notify
        await self.notification_service.notify_case_submitted(case)
        
        return case
    
    async def approve_case(
        self,
        case_id: CaseId,
        user_id: str,
        tenant_id: str,
        is_step_up_auth: bool = False,
    ) -> CaseAggregate:
        """Approve case."""
        case = await self.case_repository.get(case_id)
        
        # Verify tenant
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Check step-up auth for CRITICAL
        if case.severity == Severity.CRITICAL and not is_step_up_auth:
            raise StepUpAuthRequiredError()
        
        # Capture snapshot
        await self.snapshot_provider.capture(
            case,
            SnapshotReason.PRE_TRANSITION,
            user_id,
        )
        
        # Validate transition
        require_case_transition(
            case.status,
            CaseStatus.APPROVED,
            user_roles=await self._get_user_roles(user_id),
            is_step_up_auth=is_step_up_auth,
        )
        
        # Apply transition
        case.status = CaseStatus.APPROVED
        case.approved_by = user_id
        case.approved_at = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        
        # Recompute hash
        case.canonical_hash = canonical_hash_diff(case)
        
        # Save
        await self.case_repository.save(case)
        
        # Notify
        await self.notification_service.notify_case_approved(case)
        
        return case
```

## 4. DTOs

```python
@dataclass
class CreateCaseDTO:
    reception_id: str
    category: DifferenceCategory
    description: str
    supplier_id: Optional[str]
    warehouse_id: Optional[str]
    items: List[CreateItemDTO]
    total_impact: MonetaryAmount
```

## 5. Error Handling

| Operation    | Errors Thrown                                    |
| ------------ | ------------------------------------------------ |
| Create       | `CaseAlreadyExistsError`, `CaseValidationError` |
| Submit       | `InvalidTransitionError`, `TenantMismatchError` |
| Approve      | `StepUpAuthRequiredError`, `InsufficientPermissionsError` |
| Reject       | `InvalidTransitionError`, `MissingRequiredFieldError` |
| Close        | `InvalidTransitionError`, `ItemStatusConflictError` |

---

**See also**: `27_commands_overview.md` for command pattern usage
