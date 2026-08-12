# Phase 040 — Audit Logging

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

Comprehensive audit trail with canonical hash verification for data integrity.

## 2. Audit Log Structure

```python
@dataclass
class AuditLogEntry:
    entry_id: str
    tenant_id: str
    case_id: str
    action: str
    actor_id: str
    actor_email: str
    timestamp: datetime
    changes: dict
    canonical_hash: str
    ip_address: str
    user_agent: str
```

## 3. Actions Logged

| Action                        | Trigger                          |
| ----------------------------- | -------------------------------- |
| `case.created`                | New case created                 |
| `case.updated`                | Case modified                    |
| `case.status_changed`         | Status transition                |
| `case.submitted`              | Submitted for review             |
| `case.approved`               | Case approved                    |
| `case.rejected`               | Case rejected                    |
| `case.closed`                 | Case closed                      |
| `item.created`                | Item added                       |
| `item.formalized`             | Item formalized                  |
| `item.rejected`               | Item rejected                    |
| `item.resolved`               | Item resolved                    |
| `evidence.uploaded`           | Evidence uploaded                |
| `document.issued`             | Document issued                  |
| `severity.overridden`         | Severity manually changed        |
| `responsibility.assigned`     | Responsibility assigned          |

## 4. Canonical Hash in Audit

```python
async def log_audit(
    case: CaseAggregate,
    action: str,
    changes: dict,
    user: User,
    request: Request,
) -> AuditLogEntry:
    """Log audit entry with canonical hash."""
    entry = AuditLogEntry(
        entry_id=str(uuid4()),
        tenant_id=case.tenant_id,
        case_id=str(case.id),
        action=action,
        actor_id=user.id,
        actor_email=user.email,
        timestamp=datetime.utcnow(),
        changes=changes,
        canonical_hash=case.canonical_hash.value,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
    )
    
    await audit_repository.save(entry)
    
    return entry
```

## 5. Audit Query

```python
async def get_case_audit_trail(
    case_id: str,
    tenant_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[AuditLogEntry]:
    """Get audit trail for case."""
    query = select(AuditLogEntry).where(
        AuditLogEntry.case_id == case_id,
        AuditLogEntry.tenant_id == tenant_id,
    )
    
    if start_date:
        query = query.where(AuditLogEntry.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLogEntry.timestamp <= end_date)
    
    query = query.order_by(AuditLogEntry.timestamp.desc())
    
    result = await session.execute(query)
    return result.scalars().all()
```

## 6. Compliance Requirements

| Requirement                 | Implementation                          |
| --------------------------- | --------------------------------------- |
| Complete trail              | All state changes logged                |
| Immutable                   | Append-only audit table                 |
| Timestamp accuracy          | UTC timestamps with milliseconds        |
| Actor identification        | User ID + email + IP                    |
| Data integrity              | Canonical hash verification             |
| Retention                   | 7 years minimum                         |

---

**See also**: `15_integrity_service.md` for integrity verification
