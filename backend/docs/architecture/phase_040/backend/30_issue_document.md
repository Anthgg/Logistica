# Phase 040 — Issue Document Command

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The `IssueDocument` command generates and issues a DIF document for an approved case.

## 2. Command Structure

```python
@dataclass
class IssueDocument(Command):
    """Issue DIF document."""
    case_id: str
```

## 3. Handler

```python
async def issue_document_handler(
    command: IssueDocument,
) -> CommandResult:
    """Handle IssueDocument command."""
    try:
        result = await document_service.issue_document(
            case_id=command.case_id,
            user_id=command.user_id,
            tenant_id=command.tenant_id,
        )
        
        return CommandResult(
            success=True,
            data={
                "case_id": str(result.case_id),
                "document_number": result.document_number,
                "document_url": result.document_url,
                "issued_at": result.issued_at.isoformat(),
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
| Case status                   | Must be PENDING_DOCUMENT            |
| Case approved                 | Case must be APPROVED first         |
| Items resolved                | All items must be RESOLVED          |
| Tenant match                  | User tenant must match case tenant  |

## 5. Post-conditions

| Effect                        | Description                         |
| ----------------------------- | ----------------------------------- |
| Status change                 | PENDING_DOCUMENT → DOCUMENT_ISSUED  |
| PDF generated                 | DIF document created                |
| Document stored               | Uploaded to storage                 |
| Canonical hash updated        | Hash recomputed                     |
| Event emitted                 | `DocumentIssued` event published    |
| Notifications sent            | Stakeholders notified               |

## 6. State Transition

```
┌──────────────────┐    issue_document()    ┌─────────────────┐
│ PENDING_DOCUMENT │───────────────────────▶│ DOCUMENT_ISSUED │
└──────────────────┘                        └─────────────────┘
```

---

**See also**: `24_document_service.md` for document workflow
