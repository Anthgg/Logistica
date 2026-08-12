# Phase 040 — ORM Models

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/infrastructure/orm_models.py`

## 1. Overview

12 ORM models mapping domain aggregates to PostgreSQL tables.

## 2. Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         cases                                   │
├─────────────────────────────────────────────────────────────────┤
│  id: UUID (PK)                                                  │
│  tenant_id: VARCHAR(50) (NOT NULL, INDEX)                       │
│  status: VARCHAR(30) (NOT NULL)                                 │
│  severity: VARCHAR(20) (NOT NULL)                               │
│  category: VARCHAR(50) (NOT NULL)                               │
│  description: TEXT                                              │
│  reception_id: VARCHAR(100) (NOT NULL, FK)                      │
│  supplier_id: VARCHAR(100)                                      │
│  warehouse_id: VARCHAR(100)                                     │
│  responsible_party: VARCHAR(50)                                 │
│  responsibility_justification: TEXT                             │
│  canonical_hash: VARCHAR(64) (NOT NULL)                         │
│  created_by: VARCHAR(100) (NOT NULL)                            │
│  created_at: TIMESTAMP (NOT NULL)                               │
│  updated_at: TIMESTAMP (NOT NULL)                               │
│  version: INTEGER (NOT NULL, DEFAULT 1)                         │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │ 1:N               │ 1:N               │ 1:N
         ▼                    ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   case_items   │  │  case_evidence │  │ case_snapshots │
├────────────────┤  ├────────────────┤  ├────────────────┤
│  id: UUID (PK) │  │  id: UUID (PK) │  │  id: UUID (PK) │
│  case_id: UUID │  │  case_id: UUID │  │  case_id: UUID │
│  sku: VARCHAR   │  │  url: TEXT     │  │  data: JSONB   │
│  item_type: ... │  │  evidence_...  │  │  captured_at:  │
│  status: ...    │  │  description:  │  │  captured_by:  │
│  expected_qty:  │  │  uploaded_by:  │  │  reason: ...   │
│  received_qty:  │  │  uploaded_at:  │  └────────────────┘
│  unit_cost: ... │  └────────────────┘
│  total_impact:  │
│  notes: TEXT    │
│  version: INT   │
└────────────────┘
```

## 3. Model Definitions

### 3.1 CaseModel

```python
class CaseModel(Base):
    __tablename__ = "cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    status = Column(String(30), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    reception_id = Column(String(100), nullable=False, index=True)
    supplier_id = Column(String(100), nullable=True, index=True)
    warehouse_id = Column(String(100), nullable=True, index=True)
    responsible_party = Column(String(50), nullable=True)
    responsibility_justification = Column(Text, nullable=True)
    canonical_hash = Column(String(64), nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, nullable=False, default=1)
    
    # Relationships
    items = relationship("CaseItemModel", back_populates="case", cascade="all, delete-orphan")
    evidence = relationship("CaseEvidenceModel", back_populates="case", cascade="all, delete-orphan")
    snapshots = relationship("CaseSnapshotModel", back_populates="case", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "reception_id", name="uq_case_tenant_reception"),
        CheckConstraint("version >= 1", name="ck_case_version"),
    )
```

### 3.2 CaseItemModel

```python
class CaseItemModel(Base):
    __tablename__ = "case_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    sku = Column(String(100), nullable=False)
    item_type = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING")
    expected_qty = Column(Numeric(10, 3), nullable=False)
    received_qty = Column(Numeric(10, 3), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=True)
    total_impact = Column(Numeric(12, 2), nullable=True)
    notes = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    
    # Relationships
    case = relationship("CaseModel", back_populates="items")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("expected_qty > 0", name="ck_item_expected_qty"),
        CheckConstraint("received_qty >= 0", name="ck_item_received_qty"),
        UniqueConstraint("case_id", "sku", name="uq_item_case_sku"),
    )
```

### 3.3 CaseEvidenceModel

```python
class CaseEvidenceModel(Base):
    __tablename__ = "case_evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    evidence_type = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_by = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    case = relationship("CaseModel", back_populates="evidence")
```

### 3.4 CaseSnapshotModel

```python
class CaseSnapshotModel(Base):
    __tablename__ = "case_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    captured_by = Column(String(100), nullable=False)
    reason = Column(String(30), nullable=False)
    
    # Relationships
    case = relationship("CaseModel", back_populates="snapshots")
```

## 4. Indexes

| Table           | Index                              | Columns                        | Type    |
| --------------- | ---------------------------------- | ------------------------------ | ------- |
| `cases`         | `ix_cases_tenant_id`               | `tenant_id`                    | B-tree  |
| `cases`         | `ix_cases_status`                  | `status`                       | B-tree  |
| `cases`         | `ix_cases_severity`                | `severity`                     | B-tree  |
| `cases`         | `ix_cases_category`                | `category`                     | B-tree  |
| `cases`         | `ix_cases_reception_id`            | `reception_id`                 | B-tree  |
| `cases`         | `ix_cases_supplier_id`             | `supplier_id`                  | B-tree  |
| `case_items`    | `ix_case_items_case_id`            | `case_id`                      | B-tree  |
| `case_evidence` | `ix_case_evidence_case_id`         | `case_id`                      | B-tree  |
| `case_snapshots`| `ix_case_snapshots_case_id`        | `case_id`                      | B-tree  |

## 5. Triggers

```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_cases_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cases_updated_at
    BEFORE UPDATE ON cases
    FOR EACH ROW
    EXECUTE FUNCTION update_cases_timestamp();

-- Auto-increment version on update
CREATE OR REPLACE FUNCTION increment_cases_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cases_version
    BEFORE UPDATE ON cases
    FOR EACH ROW
    EXECUTE FUNCTION increment_cases_version();
```

---

**See also**: `12_alembic_migration.md` for migration details
