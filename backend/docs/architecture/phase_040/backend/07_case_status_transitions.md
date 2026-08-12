# Phase 040 — Case Status Transitions

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. State Machine Overview

The case lifecycle has **17 states** with defined transitions. All transitions are validated by `require_case_transition()`.

## 2. State Diagram

```
                            ┌──────────┐
                            │ DETECTED │
                            └────┬─────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              ┌──────────┐              ┌──────────┐
              │  DRAFT   │              │CANCELLED │
              └────┬─────┘              └──────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
   ┌──────────┐        ┌──────────┐
   │SUBMITTED │        │CANCELLED │
   └────┬─────┘        └──────────┘
        │
        ▼
   ┌──────────┐
   │IN_REVIEW │◀──────────────────────┐
   └──┬───┬───┘                       │
      │   │                           │
      │   ├───────────┐               │
      │   ▼           ▼               │
      │ ┌────────┐ ┌────────┐         │
      │ │APPROVED│ │REJECTED│         │
      │ └───┬────┘ └───┬────┘         │
      │     │          │              │
      │     │          └──────┐       │
      │     ▼                 ▼       │
      │ ┌──────────┐    ┌──────────┐  │
      │ │ PENDING_ │    │  DRAFT   │──┘
      │ │ DOCUMENT │    └──────────┘
      │ └────┬─────┘
      │      │
      │      ▼
      │ ┌──────────┐
      │ │DOCUMENT_ │
      │ │ ISSUED   │
      │ └────┬─────┘
      │      │
      │      ▼
      │ ┌──────────┐
      │ │ PENDING_ │
      │ │  CLOSE   │
      │ └────┬─────┘
      │      │
      │      ▼
      │ ┌──────────┐
      │ │  CLOSED  │
      │ └──────────┘
      │
      ├───────────┐
      ▼           ▼
┌──────────┐ ┌──────────┐
│ ON_HOLD  │ │ESCALATED │
└────┬─────┘ └────┬─────┘
     │            │
     └─────┬──────┘
           ▼
     ┌──────────┐
     │IN_REVIEW │
     └──────────┘
```

## 3. Transition Map

```python
CASE_TRANSITIONS: Dict[CaseStatus, List[CaseStatus]] = {
    CaseStatus.DETECTED: [
        CaseStatus.DRAFT,
        CaseStatus.CANCELLED,
    ],
    CaseStatus.DRAFT: [
        CaseStatus.SUBMITTED,
        CaseStatus.CANCELLED,
    ],
    CaseStatus.SUBMITTED: [
        CaseStatus.IN_REVIEW,
        CaseStatus.REJECTED,
    ],
    CaseStatus.IN_REVIEW: [
        CaseStatus.APPROVED,
        CaseStatus.REJECTED,
        CaseStatus.ON_HOLD,
        CaseStatus.ESCALATED,
    ],
    CaseStatus.APPROVED: [
        CaseStatus.PENDING_DOCUMENT,
    ],
    CaseStatus.REJECTED: [
        CaseStatus.DRAFT,
        CaseStatus.CANCELLED,
    ],
    CaseStatus.PENDING_DOCUMENT: [
        CaseStatus.DOCUMENT_ISSUED,
    ],
    CaseStatus.DOCUMENT_ISSUED: [
        CaseStatus.PENDING_CLOSE,
    ],
    CaseStatus.PENDING_CLOSE: [
        CaseStatus.CLOSED,
    ],
    CaseStatus.ON_HOLD: [
        CaseStatus.IN_REVIEW,
        CaseStatus.CANCELLED,
    ],
    CaseStatus.ESCALATED: [
        CaseStatus.IN_REVIEW,
        CaseStatus.APPROVED,
    ],
    CaseStatus.PENDING_APPROVAL: [
        CaseStatus.APPROVED,
        CaseStatus.REJECTED,
    ],
    CaseStatus.PARTIALLY_RESOLVED: [
        CaseStatus.CLOSED,
        CaseStatus.IN_REVIEW,
    ],
    CaseStatus.AWAITING_EVIDENCE: [
        CaseStatus.IN_REVIEW,
        CaseStatus.REJECTED,
    ],
    CaseStatus.RESOLVED: [
        CaseStatus.PENDING_CLOSE,
    ],
}
```

## 4. Transition Guards

| Transition                | Guard Condition                              |
| ------------------------- | -------------------------------------------- |
| Any → CRITICAL state      | Step-up authentication required              |
| APPROVED → PENDING_DOCUMENT | Document generation service available      |
| PENDING_CLOSE → CLOSED    | All items must be resolved                   |
| REJECTED → DRAFT          | Rejection reason must be provided            |
| ON_HOLD → IN_REVIEW      | Hold reason must be documented               |
| ESCALATED → IN_REVIEW    | Escalation must be acknowledged              |

## 5. Role-Based Transitions

| Transition            | Required Roles                              |
| --------------------- | ------------------------------------------- |
| DETECTED → DRAFT      | operator, warehouse_staff                   |
| DRAFT → SUBMITTED     | operator, warehouse_staff                   |
| SUBMITTED → IN_REVIEW | supervisor                                  |
| IN_REVIEW → APPROVED  | supervisor, manager, admin                  |
| IN_REVIEW → REJECTED  | supervisor, manager, admin                  |
| * → CLOSED            | admin                                       |
| * → CANCELLED         | supervisor, manager, admin                  |

## 6. Terminal States

| State        | Description                              |
| ------------ | ---------------------------------------- |
| `CLOSED`     | Case fully resolved                      |
| `CANCELLED`  | Case cancelled                           |

## 7. Invalid Transitions

Attempting invalid transitions raises `InvalidTransitionError`:

```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "Cannot transition from CLOSED to SUBMITTED",
    "details": {
      "current_status": "CLOSED",
      "target_status": "SUBMITTED",
      "allowed_transitions": []
    }
  }
}
```

---

**See also**: `05_domain_services.md` for `require_case_transition()` implementation
