# Phase 040 — Review and Approval Services

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/application/review_approval_service.py`

## 1. Overview

Services handling case review and approval workflows.

## 2. Review Service

```python
class ReviewService:
    """Case review orchestration."""
    
    async def submit_for_review(
        self,
        case_id: CaseId,
        user_id: str,
        tenant_id: str,
    ) -> CaseAggregate:
        """Submit case for supervisor review."""
        case = await self.case_repository.get(case_id)
        
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Verify items are formalized
        pending_items = [
            item for item in case.items
            if item.status == ItemStatus.PENDING
        ]
        if pending_items:
            raise CaseValidationError(
                "All items must be formalized before submission"
            )
        
        # Verify evidence if required
        if not verify_evidence(case):
            raise CaseValidationError(
                "Required evidence not attached"
            )
        
        # Submit
        case.status = CaseStatus.SUBMITTED
        case.submitted_by = user_id
        case.submitted_at = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        
        case.canonical_hash = canonical_hash_diff(case)
        
        await self.case_repository.save(case)
        
        return case
    
    async def review_case(
        self,
        case_id: CaseId,
        action: ReviewAction,
        comments: Optional[str],
        user_id: str,
        tenant_id: str,
    ) -> CaseAggregate:
        """Perform review action on case."""
        case = await self.case_repository.get(case_id)
        
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        if case.status != CaseStatus.IN_REVIEW:
            raise InvalidCaseStatusError(
                f"Case must be in IN_REVIEW status"
            )
        
        if action == ReviewAction.APPROVE:
            case.status = CaseStatus.APPROVED
            case.approved_by = user_id
            case.approved_at = datetime.utcnow()
        elif action == ReviewAction.REJECT:
            if not comments:
                raise MissingRequiredFieldError("comments")
            case.status = CaseStatus.REJECTED
            case.rejection_reason = comments
            case.rejected_by = user_id
            case.rejected_at = datetime.utcnow()
        
        case.review_comments = comments
        case.updated_at = datetime.utcnow()
        
        case.canonical_hash = canonical_hash_diff(case)
        
        await self.case_repository.save(case)
        
        return case
```

## 3. Approval Service

```python
class ApprovalService:
    """Multi-level approval workflow."""
    
    APPROVAL_LEVELS = {
        Severity.LOW: ["operator"],
        Severity.MEDIUM: ["supervisor"],
        Severity.HIGH: ["manager"],
        Severity.CRITICAL: ["executive"],
    }
    
    async def request_approval(
        self,
        case_id: CaseId,
        user_id: str,
        tenant_id: str,
    ) -> CaseAggregate:
        """Request approval for case."""
        case = await self.case_repository.get(case_id)
        
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Determine required approval level
        required_level = self.APPROVAL_LEVELS.get(case.severity)
        
        case.status = CaseStatus.PENDING_APPROVAL
        case.required_approval_level = required_level
        case.updated_at = datetime.utcnow()
        
        case.canonical_hash = canonical_hash_diff(case)
        
        await self.case_repository.save(case)
        
        # Notify approvers
        await self.notification_service.notify_approval_required(
            case, required_level
        )
        
        return case
    
    async def approve(
        self,
        case_id: CaseId,
        user_id: str,
        tenant_id: str,
        is_step_up_auth: bool = False,
    ) -> CaseAggregate:
        """Approve case at required level."""
        case = await self.case_repository.get(case_id)
        
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Check step-up auth for CRITICAL
        if case.severity == Severity.CRITICAL and not is_step_up_auth:
            raise StepUpAuthRequiredError()
        
        # Verify user has required role
        user_roles = await self._get_user_roles(user_id)
        required_roles = case.required_approval_level
        
        if not any(role in required_roles for role in user_roles):
            raise InsufficientPermissionsError(required=required_roles)
        
        case.status = CaseStatus.APPROVED
        case.approved_by = user_id
        case.approved_at = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        
        case.canonical_hash = canonical_hash_diff(case)
        
        await self.case_repository.save(case)
        
        return case
```

## 4. Review Actions

| Action     | Description                              | Required Role     |
| ---------- | ---------------------------------------- | ----------------- |
| `APPROVE`  | Approve case for processing              | supervisor+       |
| `REJECT`   | Reject with reason                       | supervisor+       |
| `HOLD`     | Put on hold                              | supervisor+       |
| `ESCALATE` | Escalate to management                   | supervisor+       |

---

**See also**: `07_case_status_transitions.md` for transition rules
