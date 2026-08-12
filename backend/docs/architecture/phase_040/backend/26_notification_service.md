# Phase 040 — Notification Service

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/application/notification_service.py`

## 1. Overview

The notification service handles all notifications for the reception differences module.

## 2. Notification Types

| Event                        | Recipients                              | Channel           |
| ---------------------------- | --------------------------------------- | ----------------- |
| `CaseCreated`               | Creator, assigned operator              | In-app, Email     |
| `CaseSubmitted`             | Supervisors                             | In-app, Email     |
| `CaseApproved`              | Creator, all stakeholders               | In-app, Email     |
| `CaseRejected`              | Creator                                 | In-app, Email     |
| `CaseClosed`                | All stakeholders                        | In-app            |
| `SeverityChanged`           | Creator, supervisors                    | In-app            |
| `EvidenceRequested`         | Creator                                 | In-app, Email     |
| `DocumentIssued`            | All stakeholders                        | In-app, Email     |
| `SLABreach`                 | Managers, supervisors                   | In-app, Email, SMS|
| `IntegrityFailure`          | Admins                                  | In-app, Email     |

## 3. Implementation

```python
class NotificationService:
    """Notification orchestration."""
    
    def __init__(
        self,
        email_service: EmailService,
        sms_service: SMSService,
        in_app_service: InAppService,
        user_service: UserService,
    ):
        self.email_service = email_service
        self.sms_service = sms_service
        self.in_app_service = in_app_service
        self.user_service = user_service
    
    async def notify_case_submitted(
        self,
        case: CaseAggregate,
    ) -> None:
        """Notify supervisors of new submission."""
        recipients = await self.user_service.get_users_by_role(
            role="supervisor",
            tenant_id=case.tenant_id,
        )
        
        for recipient in recipients:
            await self.in_app_service.send(
                user_id=recipient.id,
                title="New Case Submitted",
                message=f"Case {case.id} requires review",
                case_id=case.id,
            )
            
            await self.email_service.send(
                to=recipient.email,
                subject=f"New Reception Difference Case: {case.id}",
                template="case_submitted",
                context={
                    "case_id": case.id,
                    "category": case.category.value,
                    "severity": case.severity.value,
                },
            )
    
    async def notify_sla_breach(
        self,
        case: CaseAggregate,
    ) -> None:
        """Notify of SLA breach."""
        recipients = await self.user_service.get_users_by_role(
            role="manager",
            tenant_id=case.tenant_id,
        )
        
        for recipient in recipients:
            await self.in_app_service.send(
                user_id=recipient.id,
                title="SLA Breach Alert",
                message=f"Case {case.id} has exceeded SLA",
                case_id=case.id,
                priority="high",
            )
            
            await self.sms_service.send(
                phone=recipient.phone,
                message=f"URGENT: Case {case.id} SLA breached",
            )
```

## 4. Notification Templates

| Template               | Subject                                    |
| ---------------------- | ------------------------------------------ |
| `case_submitted`       | New Reception Difference Case: {case_id}   |
| `case_approved`        | Case Approved: {case_id}                   |
| `case_rejected`        | Case Rejected: {case_id}                   |
| `evidence_requested`   | Evidence Required for Case: {case_id}      |
| `document_issued`      | DIF Document Issued: {doc_number}          |
| `sla_breach`           | SLA Breach Alert: {case_id}               |

## 5. Delivery Channels

| Channel      | Use Case                        | Retry Policy     |
| ------------ | ------------------------------- | ---------------- |
| In-app       | All notifications               | Immediate        |
| Email        | Formal communications           | 3 retries, 5min  |
| SMS          | Critical alerts only            | 3 retries, 1min  |

## 6. Notification Preferences

```python
@dataclass
class NotificationPreference:
    user_id: str
    in_app_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
```

---

**See also**: `41_security_overview.md` for secure notification delivery
