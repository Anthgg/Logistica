# Phase 040 — Formalize Candidates Command

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The `FormalizeCandidates` command converts candidate items into formal case items.

## 2. Command Structure

```python
@dataclass
class FormalizeCandidates(Command):
    """Formalize candidate items into case."""
    case_id: str
    candidates: List[CandidateItemData]
    
@dataclass
class CandidateItemData:
    sku: str
    item_type: str
    expected_qty: str
    received_qty: str
    unit_cost: Optional[str]
    notes: Optional[str]
```

## 3. Handler

```python
async def formalize_candidates_handler(
    command: FormalizeCandidates,
) -> CommandResult:
    """Handle FormalizeCandidates command."""
    try:
        result = await formalization_service.formalize_candidates(
            case_id=command.case_id,
            candidates=[
                CandidateItemDTO(
                    sku=c.sku,
                    item_type=ItemType(c.item_type),
                    expected_qty=Quantity(Decimal(c.expected_qty)),
                    received_qty=Quantity(Decimal(c.received_qty)),
                    unit_cost=MonetaryAmount(Decimal(c.unit_cost)) if c.unit_cost else None,
                    notes=c.notes,
                )
                for c in command.candidates
            ],
            user_id=command.user_id,
            tenant_id=command.tenant_id,
        )
        
        return CommandResult(
            success=True,
            data={
                "case_id": str(result.case_id),
                "total": result.total,
                "formalized": result.formalized,
                "rejected": result.rejected,
                "errors": result.errors,
            },
        )
        
    except Exception as e:
        return CommandResult(
            success=False,
            error=str(e),
        )
```

## 4. Validation Rules

| Rule                          | Validation                          |
| ----------------------------- | ----------------------------------- |
| Case exists                   | Case ID must be valid               |
| Case status                   | Must be DRAFT or SUBMITTED          |
| Tenant match                  | User tenant must match case tenant  |
| SKU uniqueness                | No duplicate SKUs in candidates     |
| Quantity validity             | Expected > 0, Received >= 0         |

## 5. Events Emitted

| Event              | Trigger                          |
| ------------------ | -------------------------------- |
| `ItemFormalized`   | Each successful formalization    |

## 6. Error Handling

| Error                        | Response                          |
| ---------------------------- | --------------------------------- |
| `CaseNotFoundError`          | 404                               |
| `CaseValidationError`        | 422                               |
| `DuplicateItemError`         | 409 (per item)                    |
| `InvalidQuantityError`       | 422                               |

---

**See also**: `21_formalization_service.md` for service implementation
