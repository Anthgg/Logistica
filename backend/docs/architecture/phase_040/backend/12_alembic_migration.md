# Phase 040 — Alembic Migration

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Migration Overview

**Migration ID**: `bb400110040dc`

**Source**: `alembic/versions/bb400110040dc_reception_differences.py`

## 2. Migration Operations

### 2.1 Tables Created

```python
def upgrade() -> None:
    # 1. Cases table
    op.create_table(
        "cases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reception_id", sa.String(100), nullable=False),
        sa.Column("supplier_id", sa.String(100), nullable=True),
        sa.Column("warehouse_id", sa.String(100), nullable=True),
        sa.Column("responsible_party", sa.String(50), nullable=True),
        sa.Column("responsibility_justification", sa.Text(), nullable=True),
        sa.Column("canonical_hash", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "reception_id", name="uq_case_tenant_reception"),
    )
    
    # 2. Case items table
    op.create_table(
        "case_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("item_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("expected_qty", sa.Numeric(10, 3), nullable=False),
        sa.Column("received_qty", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_impact", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("case_id", "sku", name="uq_item_case_sku"),
        sa.CheckConstraint("expected_qty > 0", name="ck_item_expected_qty"),
        sa.CheckConstraint("received_qty >= 0", name="ck_item_received_qty"),
    )
    
    # 3. Case evidence table
    op.create_table(
        "case_evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("evidence_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.String(100), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
    )
    
    # 4. Case snapshots table
    op.create_table(
        "case_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("captured_by", sa.String(100), nullable=False),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
    )
```

### 2.2 Indexes Created

```python
    # Cases indexes
    op.create_index("ix_cases_tenant_id", "cases", ["tenant_id"])
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_severity", "cases", ["severity"])
    op.create_index("ix_cases_category", "cases", ["category"])
    op.create_index("ix_cases_reception_id", "cases", ["reception_id"])
    op.create_index("ix_cases_supplier_id", "cases", ["supplier_id"])
    
    # Case items indexes
    op.create_index("ix_case_items_case_id", "case_items", ["case_id"])
    
    # Case evidence indexes
    op.create_index("ix_case_evidence_case_id", "case_evidence", ["case_id"])
    
    # Case snapshots indexes
    op.create_index("ix_case_snapshots_case_id", "case_snapshots", ["case_id"])
```

### 2.3 Triggers Created

```python
    # Auto-update timestamp trigger
    op.execute("""
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
    """)
    
    # Auto-increment version trigger
    op.execute("""
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
    """)
```

### 2.4 Downgrade

```python
def downgrade() -> None:
    op.drop_table("case_snapshots")
    op.drop_table("case_evidence")
    op.drop_table("case_items")
    op.drop_table("cases")
```

## 3. Migration Commands

```bash
# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history
```

## 4. Data Migration Notes

- No existing data migration required (new module)
- All tables created with `NOT NULL` constraints where appropriate
- Foreign keys use `ON DELETE CASCADE`

---

**See also**: `11_orm_models.md` for model definitions
