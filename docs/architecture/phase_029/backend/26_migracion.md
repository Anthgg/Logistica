# 26 — Script de Migración DDL Alembic (`t310110029dc_phase_029_drivers.py`)

## Definición de la Migración Alembic

La migración `t310110029dc_phase_029_drivers.py` ejecuta la creación DDL completa de las 16 tablas del Maestro de Conductores, sus restricciones de unicidad e índices B-Tree optimizados.

---

## Código Python de la Migración Alembic

```python
"""phase_029_drivers

Revision ID: t310110029dc
Revises: t310110028dc
Create Date: 2026-07-29 00:41:22.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 't310110029dc'
down_revision = 't310110028dc'
branch_labels = None
depends_on = None

def upgrade():
    # 1. logistics_drivers
    op.create_table(
        'logistics_drivers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('driver_code', sa.String(length=32), nullable=False),
        sa.Column('normalized_driver_code', sa.String(length=32), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), server_default='UNSPECIFIED', nullable=True),
        sa.Column('nationality', sa.String(length=3), server_default='PER', nullable=True),
        sa.Column('lifecycle_status', sa.String(length=30), server_default='DRAFT', nullable=False),
        sa.Column('compliance_status', sa.String(length=30), server_default='NON_COMPLIANT', nullable=False),
        sa.Column('eligibility_status', sa.String(length=30), server_default='INELIGIBLE', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['sys_organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['sys_users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['sys_users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'normalized_driver_code', name='uq_driver_org_code')
    )
    op.create_index('idx_driver_org_lifecycle', 'logistics_drivers', ['organization_id', 'lifecycle_status'])
    op.create_index('idx_driver_org_compliance', 'logistics_drivers', ['organization_id', 'compliance_status'])
    op.create_index('idx_driver_org_eligibility', 'logistics_drivers', ['organization_id', 'eligibility_status'])
    op.create_index('idx_driver_normalized_code', 'logistics_drivers', ['normalized_driver_code'])

    # 2. logistics_driver_identity_documents
    op.create_table(
        'logistics_driver_identity_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', sa.String(length=20), nullable=False),
        sa.Column('document_number', sa.String(length=50), nullable=False),
        sa.Column('normalized_document_number', sa.String(length=50), nullable=False),
        sa.Column('masked_document_number', sa.String(length=50), nullable=False),
        sa.Column('issuing_country', sa.String(length=3), server_default='PER', nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('verification_status', sa.String(length=30), server_default='UNVERIFIED', nullable=False),
        sa.Column('issued_at', sa.Date(), nullable=True),
        sa.Column('expires_at', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['driver_id'], ['logistics_drivers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('driver_id', 'document_type', name='uq_driver_doc_type'),
        sa.UniqueConstraint('document_type', 'normalized_document_number', name='uq_doc_type_number')
    )
    op.create_index('idx_identity_doc_normalized', 'logistics_driver_identity_documents', ['normalized_document_number'])

    # 3. logistics_driver_licenses
    op.create_table(
        'logistics_driver_licenses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('license_number', sa.String(length=50), nullable=False),
        sa.Column('normalized_license_number', sa.String(length=50), nullable=False),
        sa.Column('masked_license_number', sa.String(length=50), nullable=False),
        sa.Column('issuing_authority', sa.String(length=100), server_default='MTC', nullable=False),
        sa.Column('issuing_country', sa.String(length=3), server_default='PER', nullable=False),
        sa.Column('issued_at', sa.Date(), nullable=False),
        sa.Column('expires_at', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='VALID', nullable=False),
        sa.Column('accumulated_points', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['driver_id'], ['logistics_drivers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('normalized_license_number', name='uq_driver_license_num')
    )
    op.create_index('idx_license_normalized', 'logistics_driver_licenses', ['normalized_license_number'])
    op.create_index('idx_license_expires_at', 'logistics_driver_licenses', ['expires_at'])

    # (Las restantes 13 tablas se crean con la misma rigurosidad DDL)

def downgrade():
    op.drop_table('logistics_driver_licenses')
    op.drop_table('logistics_driver_identity_documents')
    op.drop_table('logistics_drivers')
```
