# Phase 040 — Background Jobs

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

6 background jobs handle asynchronous processing for the reception differences module.

## 2. Job List

| Job ID | Name                        | Schedule    | Description                          |
| ------ | --------------------------- | ----------- | ------------------------------------ |
| 1      | `CaseIntegrityCheckJob`     | Daily 02:00 | Verify integrity of all active cases |
| 2      | `SnapshotCleanupJob`        | Weekly Sun  | Archive old snapshots                |
| 3      | `SLAEscalationJob`          | Every hour  | Escalate cases exceeding SLA         |
| 4      | `NotificationDigestJob`     | Daily 08:00 | Send notification digests            |
| 5      | `DocumentGenerationJob`     | On-demand   | Generate pending DIF documents       |
| 6      | `StaleCaseDetectionJob`     | Daily 06:00 | Detect cases stuck in status         |

## 3. Job Implementations

### 3.1 CaseIntegrityCheckJob

```python
class CaseIntegrityCheckJob:
    """Verify integrity of all active cases."""
    
    name = "case_integrity_check"
    schedule = "0 2 * * *"  # Daily at 02:00
    
    async def execute(self):
        """Run integrity check on all active cases."""
        active_cases = await case_repository.list_active()
        
        results = await integrity_service.verify_batch_integrity(
            [case.id for case in active_cases]
        )
        
        failures = [r for r in results if not r.is_valid]
        
        if failures:
            await notification_service.notify_integrity_failures(failures)
            
            for failure in failures:
                await audit_log.record(
                    "integrity_check_failed",
                    case_id=failure.case_id,
                    details=failure,
                )
```

### 3.2 SnapshotCleanupJob

```python
class SnapshotCleanupJob:
    """Archive old snapshots."""
    
    name = "snapshot_cleanup"
    schedule = "0 0 * * 0"  # Weekly on Sunday
    
    async def execute(self):
        """Archive snapshots older than 90 days."""
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        old_snapshots = await snapshot_repository.list_before(cutoff_date)
        
        for snapshot in old_snapshots:
            await archive_service.archive(snapshot)
            await snapshot_repository.delete(snapshot.id)
```

### 3.3 SLAEscalationJob

```python
class SLAEscalationJob:
    """Escalate cases exceeding SLA."""
    
    name = "sla_escalation"
    schedule = "0 * * * *"  # Every hour
    
    async def execute(self):
        """Check and escalate SLA violations."""
        sla_limits = {
            Severity.LOW: timedelta(hours=72),
            Severity.MEDIUM: timedelta(hours=48),
            Severity.HIGH: timedelta(hours=24),
            Severity.CRITICAL: timedelta(hours=8),
        }
        
        active_cases = await case_repository.list_active()
        
        for case in active_cases:
            elapsed = datetime.utcnow() - case.created_at
            limit = sla_limits.get(case.severity)
            
            if elapsed > limit:
                await escalation_service.escalate(case)
                await notification_service.notify_sla_breach(case)
```

### 3.4 NotificationDigestJob

```python
class NotificationDigestJob:
    """Send notification digests."""
    
    name = "notification_digest"
    schedule = "0 8 * * *"  # Daily at 08:00
    
    async def execute(self):
        """Compile and send daily digests."""
        users = await user_service.get_digest_recipients()
        
        for user in users:
            cases = await case_repository.list_for_user(user.id)
            digest = await notification_service.compile_digest(user, cases)
            await email_service.send_digest(user.email, digest)
```

### 3.5 DocumentGenerationJob

```python
class DocumentGenerationJob:
    """Generate pending DIF documents."""
    
    name = "document_generation"
    schedule = None  # On-demand
    
    async def execute(self):
        """Generate DIF documents for approved cases."""
        pending = await case_repository.list_by_status(
            CaseStatus.PENDING_DOCUMENT
        )
        
        for case in pending:
            try:
                await document_service.generate_dif(case)
                case.status = CaseStatus.DOCUMENT_ISSUED
                await case_repository.save(case)
            except DocumentGenerationError as e:
                await notification_service.notify_generation_failure(case, e)
```

### 3.6 StaleCaseDetectionJob

```python
class StaleCaseDetectionJob:
    """Detect cases stuck in status."""
    
    name = "stale_case_detection"
    schedule = "0 6 * * *"  # Daily at 06:00
    
    async def execute(self):
        """Find cases stuck in same status for >7 days."""
        stale_threshold = datetime.utcnow() - timedelta(days=7)
        
        stale_cases = await case_repository.list_stale(stale_threshold)
        
        for case in stale_cases:
            await notification_service.notify_stale_case(case)
            await audit_log.record("stale_case_detected", case_id=case.id)
```

## 4. Job Configuration

| Setting               | Value                                    |
| --------------------- | ---------------------------------------- |
| Retry Attempts        | 3                                        |
| Retry Delay           | 60 seconds                               |
| Timeout               | 300 seconds                              |
| Concurrency           | 5 jobs                                   |
| Queue                 | `reception_differences`                  |

## 5. Monitoring

| Metric                | Alert Threshold                          |
| --------------------- | ---------------------------------------- |
| Job Duration          | > 5 minutes                              |
| Failure Rate          | > 5%                                     |
| Queue Depth           | > 100                                    |
| Retry Rate            | > 10%                                    |

---

**See also**: `16_background_jobs.md` (this file), `17_outbox_events.md` for event publishing
