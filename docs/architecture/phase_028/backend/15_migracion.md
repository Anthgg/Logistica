# DDL y Script de Migración Alembic (`s310110028dc_phase_028_vehicle_verifications.py`)

## 1. Resumen de la Migración

La migración Alembic **`s310110028dc_phase_028_vehicle_verifications.py`** implementa la estructura relacional de la Fase 028 mediante la creación de **10 tablas**, claves foráneas, restricciones de unicidad, checks de segregación de funciones e índices B-Tree de alta velocidad.

* **Revision ID**: `s310110028dc`
* **Revisión Previa (`down_revision`)**: `r300110027dc` (Fase 027)

---

## 2. Código del Script de Migración Python / Alembic

```python
"""Phase 028: Vehicle Verification Backend Tables

Revision ID: s310110028dc
Revises: r300110027dc
Create Date: 2026-07-28 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's310110028dc'
down_revision = 'r300110027dc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. logistics_vehicle_verification_sources
    op.create_table(
        'logistics_vehicle_verification_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('source_type', sa.String(length=30), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('default_confidence_score', sa.Numeric(precision=3, scale=2), nullable=False, server_default='1.00'),
        sa.Column('staleness_days', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('is_official_entity', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('authorization_status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('idx_vv_sources_status_priority', 'logistics_vehicle_verification_sources', ['authorization_status', 'priority'])

    # 2. logistics_vehicle_verification_provider_configs
    op.create_table(
        'logistics_vehicle_verification_provider_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_verification_sources.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('provider_class', sa.String(length=150), nullable=False),
        sa.Column('base_url', sa.String(length=255), nullable=True),
        sa.Column('encrypted_api_key', sa.Text(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('rate_limit_config', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('idx_vv_provider_configs_active', 'logistics_vehicle_verification_provider_configs', ['source_id', 'is_active'])

    # 3. logistics_vehicle_verifications
    op.create_table(
        'logistics_vehicle_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_verification_sources.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('verification_number', sa.String(length=60), nullable=False, unique=True),
        sa.Column('plate_number', sa.String(length=15), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('verification_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('idx_vv_vehicle_status', 'logistics_vehicle_verifications', ['vehicle_id', 'status'])
    op.create_index('idx_vv_plate_search', 'logistics_vehicle_verifications', ['plate_number', 'verification_date'])

    # 4. logistics_vehicle_verification_results
    op.create_table(
        'logistics_vehicle_verification_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_verifications.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('outcome_status', sa.String(length=30), nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(), nullable=False),
        sa.Column('payload_sha256', sa.CHAR(length=64), nullable=False),
        sa.Column('overall_confidence_score', sa.Numeric(precision=3, scale=2), nullable=False, server_default='1.00'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('idx_vv_results_sha256', 'logistics_vehicle_verification_results', ['payload_sha256'])

    # 5. logistics_vehicle_verification_field_provenance
    op.create_table(
        'logistics_vehicle_verification_field_provenance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('result_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_verification_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_name', sa.String(length=60), nullable=False),
        sa.Column('raw_source_value', sa.Text(), nullable=True),
        sa.Column('normalized_value', sa.Text(), nullable=True),
        sa.Column('erp_current_value', sa.Text(), nullable=True),
        sa.Column('is_matching', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('field_confidence_score', sa.Numeric(precision=3, scale=2), nullable=False, server_default='1.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('idx_vv_field_provenance_matching', 'logistics_vehicle_verification_field_provenance', ['result_id', 'field_name', 'is_matching'])

    # 6. logistics_assisted_vehicle_verifications
    op.create_table(
        'logistics_assisted_vehicle_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_verifications.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('operator_notes', sa.Text(), nullable=False),
        sa.Column('owner_identity_hash', sa.CHAR(length=64), nullable=False),
        sa.Column('masked_owner_name', sa.String(length=150), nullable=False),
        sa.Column('approval_status', sa.String(length=30), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('approved_by IS NULL OR created_by <> approved_by', name='chk_assisted_segregation_of_duties')
    )
    op.create_index('idx_assisted_vv_approval_status', 'logistics_assisted_vehicle_verifications', ['approval_status', 'created_at'])

    # 7. logistics_assisted_verification_evidence
    op.create_table(
        'logistics_assisted_verification_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assisted_verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_assisted_vehicle_verifications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_sha256', sa.CHAR(length=64), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('idx_vv_evidence_file_sha256', 'logistics_assisted_verification_evidence', ['file_sha256'])

    # 8. logistics_vehicle_verification_conflicts
    op.create_table(
        'logistics_vehicle_verification_conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_verifications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('field_name', sa.String(length=60), nullable=False),
        sa.Column('erp_value', sa.Text(), nullable=True),
        sa.Column('verified_value', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN'),
        sa.Column('resolution_comment', sa.Text(), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('idx_vv_conflicts_vehicle_status', 'logistics_vehicle_verification_conflicts', ['vehicle_id', 'status'])
    op.create_index('idx_vv_conflicts_severity', 'logistics_vehicle_verification_conflicts', ['severity', 'status'])

    # 9. logistics_vehicle_verification_requirements
    op.create_table(
        'logistics_vehicle_verification_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_type', sa.String(length=50), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('compliance_status', sa.String(length=30), nullable=False, server_default='PENDING_VERIFICATION'),
        sa.Column('last_evaluated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('evaluation_details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('vehicle_id', 'requirement_type', name='uq_vv_requirements_vehicle_type')
    )
    op.create_index('idx_vv_reqs_compliance', 'logistics_vehicle_verification_requirements', ['vehicle_id', 'compliance_status', 'is_mandatory'])

    # 10. logistics_vehicle_verification_review_tasks
    op.create_table(
        'logistics_vehicle_verification_review_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conflict_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_verification_conflicts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_number', sa.String(length=60), nullable=False, unique=True),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('assigned_role', sa.String(length=60), nullable=False),
        sa.Column('assigned_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_status', sa.String(length=30), nullable=False, server_default='OPEN'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.create_index('idx_vv_review_tasks_status', 'logistics_vehicle_verification_review_tasks', ['task_status', 'priority', 'assigned_user_id'])


def downgrade():
    op.drop_table('logistics_vehicle_verification_review_tasks')
    op.drop_table('logistics_vehicle_verification_requirements')
    op.drop_table('logistics_vehicle_verification_conflicts')
    op.drop_table('logistics_assisted_verification_evidence')
    op.drop_table('logistics_assisted_vehicle_verifications')
    op.drop_table('logistics_vehicle_verification_field_provenance')
    op.drop_table('logistics_vehicle_verification_results')
    op.drop_table('logistics_vehicle_verifications')
    op.drop_table('logistics_vehicle_verification_provider_configs')
    op.drop_table('logistics_vehicle_verification_sources')
```
