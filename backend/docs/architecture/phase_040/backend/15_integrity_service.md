# Phase 040 — Integrity Service

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The integrity service verifies case data integrity using canonical hashes and snapshot comparison.

**Source**: `app/modules/logistics/inbound/reception_differences/infrastructure/integrity_service.py`

## 2. Integrity Verification

```python
class IntegrityService:
    """Verify case data integrity."""
    
    async def verify_case_integrity(
        self,
        case_id: CaseId,
    ) -> IntegrityResult:
        """
        Verify case data integrity.
        
        Steps:
        1. Load case from database
        2. Recompute canonical hash
        3. Compare with stored hash
        4. Return verification result
        """
        case = await self.case_repository.get(case_id)
        
        # Recompute hash
        recomputed_hash = canonical_hash_diff(case)
        
        # Compare
        is_valid = recomputed_hash.value == case.canonical_hash.value
        
        return IntegrityResult(
            case_id=case_id,
            is_valid=is_valid,
            stored_hash=case.canonical_hash.value,
            recomputed_hash=recomputed_hash.value,
            verified_at=datetime.utcnow(),
        )
```

## 3. Integrity Result

```python
@dataclass
class IntegrityResult:
    case_id: CaseId
    is_valid: bool
    stored_hash: str
    recomputed_hash: str
    verified_at: datetime
    discrepancies: Optional[List[dict]] = None
```

## 4. Batch Verification

```python
async def verify_batch_integrity(
    self,
    case_ids: List[CaseId],
) -> List[IntegrityResult]:
    """Verify integrity of multiple cases."""
    results = []
    for case_id in case_ids:
        result = await self.verify_case_integrity(case_id)
        results.append(result)
    return results
```

## 5. Discrepancy Detection

```python
async def detect_discrepancies(
    self,
    case_id: CaseId,
) -> List[dict]:
    """
    Detect specific discrepancies between stored and computed state.
    
    Returns list of discrepancies with details.
    """
    case = await self.case_repository.get(case_id)
    recomputed_hash = canonical_hash_diff(case)
    
    if recomputed_hash.value == case.canonical_hash.value:
        return []
    
    # Find specific differences
    discrepancies = []
    
    # Check status
    # Check items
    # Check metadata
    # ... (detailed comparison)
    
    return discrepancies
```

## 6. Integrity Checks

| Check Type              | Frequency        | Scope                    |
| ----------------------- | ---------------- | ------------------------ |
| Pre-transition          | Every transition | Single case              |
| Post-update             | Every update     | Single case              |
| Scheduled audit         | Daily            | All active cases         |
| Manual trigger          | On-demand        | Single or batch          |

## 7. Audit Trail

Every integrity check is logged:

```python
@dataclass
class IntegrityAuditLog:
    case_id: CaseId
    check_type: str
    is_valid: bool
    stored_hash: str
    recomputed_hash: str
    checked_by: str
    checked_at: datetime
    discrepancies: Optional[List[dict]]
```

---

**See also**: `44_audit_logging.md` for audit trail details
