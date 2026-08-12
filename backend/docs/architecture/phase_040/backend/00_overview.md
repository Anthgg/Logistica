# Phase 040 — Reception Differences Backend: Architecture Overview

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences Backend            |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |
| Author    | Architecture Team                        |

## 1. Purpose

Phase 040 implements the **Reception Differences** module for the logistics inbound domain. It handles discrepancies detected during goods reception: quantity mismatches, damaged items, missing documentation, and other variance categories. The module follows Domain-Driven Design (DDD) with CQRS patterns.

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Router   │  │ Schemas  │  │  Auth    │  │  Errors  │   │
│  │ (64 EPs)  │  │ (31 Pyd.)│  │  (RBAC) │  │ (27 cls) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Application Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Case    │  │   Item   │  │ Formaliz.│  │  Manual  │   │
│  │ Service  │  │ Service  │  │ Service  │  │ Creation │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Quantity │  │ Document │  │ Review   │  │Notificat.│   │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     Domain Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Case    │  │   Item   │  │ Severity │  │ Evidence │   │
│  │Aggregate │  │Aggregate │  │ Policy   │  │ Workflow │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Enums   │  │  Errors  │  │ Services │                  │
│  │ (15+ )   │  │ (27 cls) │  │ (3 svc)  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 Infrastructure Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  ORM     │  │ Alembic  │  │   PDF    │  │ Snapshot │   │
│  │ (12 mdl) │  │ Migration│  │Generator │  │ Provider │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Integrity│  │   Jobs   │  │  Outbox  │  │  Repos   │   │
│  │ Service  │  │ (6 jobs) │  │  Events  │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 3. Key Design Decisions

| Decision                  | Choice                     | Rationale                              |
| ------------------------- | -------------------------- | -------------------------------------- |
| Architecture Style        | DDD + CQRS                 | Complex domain with distinct reads/writes |
| Aggregate Root            | `CaseAggregate`            | Consistency boundary for differences   |
| Event Sourcing            | Outbox pattern             | Reliable event publishing              |
| PDF Generation            | reportlab                  | Programmatic DIF document creation     |
| Background Processing     | 6 async jobs               | Non-blocking workflows                 |
| Security                  | RBAC + Step-up auth        | CRITICAL severity requires re-auth     |

## 4. Module Location

```
app/modules/logistics/inbound/reception_differences/
├── domain/
│   ├── enums.py
│   ├── errors.py
│   ├── services.py
│   ├── case_aggregate.py
│   └── item_aggregate.py
├── application/
│   ├── case_service.py
│   ├── item_service.py
│   └── ...
├── infrastructure/
│   ├── orm_models.py
│   ├── repositories.py
│   └── ...
└── presentation/
    ├── router.py
    ├── schemas.py
    └── ...
```

## 5. Dependencies

- **Upstream**: Inbound Reception module (triggers difference detection)
- **Downstream**: Notification service, Document issuance, Audit trail
- **Cross-cutting**: Authentication, Tenant isolation, Event bus

## 6. Metrics

| Metric               | Value  |
| -------------------- | ------ |
| Endpoints            | 64     |
| Pydantic Schemas     | 31     |
| Domain Enums         | 15+    |
| Error Classes        | 27     |
| ORM Models           | 12     |
| Background Jobs      | 6      |
| Test Cases           | 219    |
| Permissions          | 34     |
| Status States        | 17     |
| Command Types        | 4      |
| Query Types          | 2      |

---

**See also**: `01_domain_model.md` for detailed DDD analysis
