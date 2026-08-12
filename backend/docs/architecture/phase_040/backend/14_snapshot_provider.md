# Phase 040 — Snapshot Provider

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The snapshot provider captures point-in-time state of cases for audit trails and historical comparison.

**Source**: `app/modules/logistics/inbound/reception_differences/infrastructure/snapshot_provider.py`

## 2. Snapshot Structure

```python
@dataclass
class Snapshot:
    snapshot_id: str
    case_id: CaseId
    data: dict
    captured_at: datetime
    captured_by: str
    reason: SnapshotReason
```

## 3. Snapshot Capture

```python
class SnapshotProvider:
    """Capture and store case snapshots."""
    
    async def capture(
        self,
        case: CaseAggregate,
        reason: SnapshotReason,
        user_id: str,
    ) -> Snapshot:
        """
        Capture current case state.
        
        Args:
            case: Case aggregate to snapshot
            reason: Why snapshot is being taken
            user_id: User triggering capture
            
        Returns:
            Snapshot with captured data
        """
        snapshot_data = {
            "case": {
                "id": str(case.id),
                "status": case.status.value,
                "severity": case.severity.value,
                "category": case.category.value,
                "description": case.description,
                "responsible_party": case.responsible_party,
                "canonical_hash": case.canonical_hash.value,
                "created_at": case.created_at.isoformat(),
                "updated_at": case.updated_at.isoformat(),
            },
            "items": [
                {
                    "id": str(item.id),
                    "sku": item.sku,
                    "item_type": item.item_type.value,
                    "status": item.status.value,
                    "expected_qty": str(item.expected_qty),
                    "received_qty": str(item.received_qty),
                    "difference_qty": str(item.difference_qty),
                    "unit_cost": str(item.unit_cost) if item.unit_cost else None,
                    "total_impact": str(item.total_impact) if item.total_impact else None,
                }
                for item in case.items
            ],
            "evidence_count": len(case.evidence_links),
            "metadata": {
                "snapshot_reason": reason.value,
                "captured_by": user_id,
                "captured_at": datetime.utcnow().isoformat(),
            },
        }
        
        snapshot = Snapshot(
            snapshot_id=str(uuid4()),
            case_id=case.id,
            data=snapshot_data,
            captured_at=datetime.utcnow(),
            captured_by=user_id,
            reason=reason,
        )
        
        # Store snapshot
        await self.snapshot_repository.save(snapshot)
        
        return snapshot
```

## 4. Snapshot Triggers

| Trigger                   | Reason                  | Automatic |
| ------------------------- | ----------------------- | --------- |
| Pre-transition            | `PRE_TRANSITION`        | Yes       |
| Manual capture            | `MANUAL`                | No        |
| Audit request             | `AUDIT`                 | No        |
| Scheduled (daily)         | `SCHEDULED`             | Yes       |

## 5. Pre-Transition Snapshots

```python
async def capture_pre_transition_snapshot(
    case: CaseAggregate,
    target_status: CaseStatus,
    user_id: str,
) -> Snapshot:
    """
    Capture snapshot before status transition.
    
    Called automatically by require_case_transition().
    """
    return await snapshot_provider.capture(
        case=case,
        reason=SnapshotReason.PRE_TRANSITION,
        user_id=user_id,
    )
```

## 6. Snapshot Comparison

```python
def compare_snapshots(
    snapshot_old: Snapshot,
    snapshot_new: Snapshot,
) -> dict:
    """
    Compare two snapshots and return differences.
    
    Returns:
        Dict with changed fields and their old/new values
    """
    differences = {}
    
    old_data = snapshot_old.data
    new_data = snapshot_new.data
    
    # Compare case fields
    for key in old_data.get("case", {}):
        old_val = old_data["case"].get(key)
        new_val = new_data["case"].get(key)
        if old_val != new_val:
            differences[f"case.{key}"] = {
                "old": old_val,
                "new": new_val,
            }
    
    # Compare items
    old_items = {i["id"]: i for i in old_data.get("items", [])}
    new_items = {i["id"]: i for i in new_data.get("items", [])}
    
    for item_id in set(old_items.keys()) | set(new_items.keys()):
        if item_id in old_items and item_id in new_items:
            for key in old_items[item_id]:
                if old_items[item_id][key] != new_items[item_id].get(key):
                    differences[f"item.{item_id}.{key}"] = {
                        "old": old_items[item_id][key],
                        "new": new_items[item_id].get(key),
                    }
        elif item_id in old_items:
            differences[f"item.{item_id}"] = {"status": "removed"}
        else:
            differences[f"item.{item_id}"] = {"status": "added"}
    
    return differences
```

## 7. Storage

| Storage Type | Location                        | Retention |
| ------------ | ------------------------------- | --------- |
| PostgreSQL   | `case_snapshots` table          | Permanent |
| JSONB        | `data` column                   | —         |

---

**See also**: `15_integrity_service.md` for integrity verification
