# Phase 040 — Submit Case Command

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The `SubmitCase` command submits a case for supervisor review.

## 2. Command Structure

```python
@dataclass
class SubmitCase(Command):
    """Submit case for review."""
    case_id: str
```

## 3. Handler

```python
async def submit_case_handler(
    command: SubmitCase,
) -> CommandResult:
    """Handle SubmitCase command."""
    try:
        case = await case_service.submit_case(
            case_id=command.case_id,
            user_id=command.user_id,
            tenant_id=command.tenant_id,
        )
        
        return CommandResult(
            success=True,
            data={
                "case_id": str(case.id),
                "status": case.status.value,
                "submitted_at": case.submitted_at.isoformat(),
            },
        )
        
    except Exception as e:
        return CommandResult(
            success=False,
            error=str(e),
        )
```

## 4. Pre-conditions

| Condition                     | Validation                          |
| ----------------------------- | ----------------------------------- |
| Case exists                   | Case ID must be valid               |
| Case status                   | Must be DRAFT                       |
| Items formalized              | All items must be FORMALIZED        |
| Evidence attached             | Required evidence must be present   |
| Tenant match                  | User tenant must match case tenant  |

## 5. Post-conditions

| Effect                        | Description                         |
| ----------------------------- | ----------------------------------- |
| Status change                 | DRAFT → SUBMITTED                   |
| Snapshot captured             | Pre-transition snapshot created     |
| Canonical hash updated        | Hash recomputed                     |
| Event emitted                 | `CaseSubmitted` event published     |
| Notifications sent            | Supervisors notified                |

## 6. State Transition

```
┌──────────┐    submit_case()    ┌──────────┐
│  DRAFT   │────────────────────▶│SUBMITTED │
└──────────┘                     └──────────┘
```

---

**See also**: `07_case_status_transitions.md` for transition rules
