# Phase 040 — Close Case Command

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The `CloseCase` command closes a resolved case, marking it as terminal.

## 2. Command Structure

```python
@dataclass
class CloseCase(Command):
    """Close resolved case."""
    case_id: str
    resolution_notes: Optional[str] = None
```

## 3. Handler

```python
async def close_case_handler(
    command: CloseCase,
) -> CommandResult:
    """Handle CloseCase command."""
    try:
        case = await case_service.close_case(
            case_id=command.case_id,
            resolution_notes=command.resolution_notes,
            user_id=command.user_id,
            tenant_id=command.tenant_id,
        )
        
        return CommandResult(
            success=True,
            data={
                "case_id": str(case.id),
                "status": case.status.value,
                "closed_at": case.closed_at.isoformat(),
            },
        )
        
    except Exception as e:
        return CommandResult(
            success=False,
            error=str(e),
        )
```

## 4. Implementation

```python
async def close_case(
    self,
    case_id: CaseId,
    resolution_notes: Optional[str],
    user_id: str,
    tenant_id: str,
) -> CaseAggregate:
    """Close resolved case."""
    case = await self.case_repository.get(case_id)
    
    if case.tenant_id != tenant_id:
        raise TenantMismatchError()
    
    # Verify status
    if case.status not in (
        CaseStatus.PENDING_CLOSE,
        CaseStatus.RESOLVED,
    ):
        raise InvalidTransitionError(
            current=case.status,
            target=CaseStatus.CLOSED,
            allowed=[CaseStatus.PENDING_CLOSE, CaseStatus.RESOLVED],
        )
    
    # Verify all items resolved
    unresolved = [
        item for item in case.items
        if item.status != ItemStatus.RESOLVED
    ]
    if unresolved:
        raise CaseValidationError(
            f"Cannot close case with {len(unresolved)} unresolved items"
        )
    
    # Capture snapshot
    await self.snapshot_provider.capture(
        case,
        SnapshotReason.PRE_TRANSITION,
        user_id,
    )
    
    # Close
    case.status = CaseStatus.CLOSED
    case.closed_by = user_id
    case.closed_at = datetime.utcnow()
    case.resolution_notes = resolution_notes
    case.updated_at = datetime.utcnow()
    
    # Recompute hash
    case.canonical_hash = canonical_hash_diff(case)
    
    # Save
    await self.case_repository.save(case)
    
    # Notify
    await self.notification_service.notify_case_closed(case)
    
    return case
```

## 5. Pre-conditions

| Condition                     | Validation                          |
| ----------------------------- | ----------------------------------- |
| Case exists                   | Case ID must be valid               |
| Case status                   | Must be PENDING_CLOSE or RESOLVED   |
| All items resolved            | All items must be RESOLVED          |
| Admin role                    | Closing requires admin role         |
| Tenant match                  | User tenant must match case tenant  |

## 6. Post-conditions

| Effect                        | Description                         |
| ----------------------------- | ----------------------------------- |
| Status change                 | → CLOSED (terminal)                 |
| Snapshot captured             | Final snapshot created              |
| Canonical hash updated        | Final hash computed                 |
| Event emitted                 | `CaseClosed` event published        |
| Notifications sent            | All stakeholders notified           |

## 7. State Transition

```
┌──────────────────┐    close_case()    ┌──────────┐
│   PENDING_CLOSE  │───────────────────▶│  CLOSED  │
└──────────────────┘                    └──────────┘
```

---

**See also**: `19_case_service.md` for case operations
