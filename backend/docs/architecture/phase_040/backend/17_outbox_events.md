# Phase 040 — Outbox Events

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The module reuses `ArrivalNoticeOutboxEvent` from the existing event infrastructure for reliable event publishing.

**Source**: `app/modules/logistics/inbound/reception_differences/infrastructure/outbox_events.py`

## 2. Outbox Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Outbox Pattern                           │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Domain  │───▶│ Outbox   │───▶│  Event   │              │
│  │  Event   │    │ Table    │    │  Bus     │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                       │                                     │
│                       ▼                                     │
│                 ┌──────────┐                                │
│                 │ Poller   │                                │
│                 └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## 3. Event Types

| Event                        | Trigger                | Payload Key Fields               |
| ---------------------------- | ---------------------- | -------------------------------- |
| `CaseCreated`               | Case detection         | case_id, category, severity      |
| `CaseSubmitted`             | Case submission        | case_id, submitted_by            |
| `CaseApproved`              | Case approval          | case_id, approved_by             |
| `CaseRejected`              | Case rejection         | case_id, rejection_reason        |
| `CaseClosed`                | Case closure           | case_id, resolution              |
| `ItemAdded`                 | Item creation          | case_id, item_id, sku            |
| `ItemFormalized`            | Item formalization     | case_id, item_id                 |
| `SeverityChanged`           | Severity update        | case_id, old_severity, new_severity |
| `EvidenceAttached`          | Evidence upload        | case_id, evidence_id, url        |
| `DocumentIssued`            | DIF generation         | case_id, document_url            |

## 4. Outbox Event Publishing

```python
async def publish_domain_event(
    event_type: str,
    aggregate_id: str,
    payload: dict,
    tenant_id: str,
) -> None:
    """
    Publish domain event via outbox.
    
    Ensures atomicity with database transaction.
    """
    outbox_event = ArrivalNoticeOutboxEvent(
        id=str(uuid4()),
        event_type=event_type,
        aggregate_id=aggregate_id,
        aggregate_type="reception_difference",
        payload=json.dumps(payload),
        tenant_id=tenant_id,
        created_at=datetime.utcnow(),
        status="PENDING",
    )
    
    await outbox_repository.save(outbox_event)
```

## 5. Event Polling

```python
class OutboxPoller:
    """Poll outbox table and publish events."""
    
    async def poll(self):
        """Process pending outbox events."""
        pending_events = await outbox_repository.list_pending(
            limit=100
        )
        
        for event in pending_events:
            try:
                await event_bus.publish(
                    event_type=event.event_type,
                    payload=json.loads(event.payload),
                    aggregate_id=event.aggregate_id,
                    tenant_id=event.tenant_id,
                )
                
                event.status = "PUBLISHED"
                event.published_at = datetime.utcnow()
                await outbox_repository.save(event)
                
            except Exception as e:
                event.status = "FAILED"
                event.error_message = str(e)
                event.retry_count += 1
                await outbox_repository.save(event)
```

## 6. Idempotency

Events include `event_id` for idempotent consumption:

```python
event_payload = {
    "event_id": str(uuid4()),
    "event_type": "CaseCreated",
    "timestamp": datetime.utcnow().isoformat(),
    "data": {
        "case_id": str(case.id),
        "tenant_id": case.tenant_id,
        # ... other fields
    },
}
```

## 7. Event Consumers

| Consumer                    | Events Consumed                     | Action                    |
| --------------------------- | ----------------------------------- | ------------------------- |
| Notification Service        | All                                 | Send notifications        |
| Audit Service               | All                                 | Record audit trail        |
| Reporting Service           | CaseCreated, CaseClosed             | Update reports            |
| Integration Service         | CaseApproved, DocumentIssued        | External sync             |

---

**See also**: `16_background_jobs.md` for polling job
