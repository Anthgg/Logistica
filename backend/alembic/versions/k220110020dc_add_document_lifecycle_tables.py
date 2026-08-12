"""add document lifecycle tables

Revision ID: k220110020dc
Revises: j990100019dc
Create Date: 2026-07-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'k220110020dc'
down_revision = 'j990100019dc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. document_instances
    op.create_table(
        'document_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('template_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_resource_type', sa.String(length=64), nullable=False),
        sa.Column('source_resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_operation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_number_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_code', sa.String(length=128), nullable=True),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('lifecycle_status', sa.String(length=32), nullable=False),
        sa.Column('sensitivity', sa.String(length=32), nullable=False),
        sa.Column('current_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('authoritative_artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('issued_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('reprint_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('print_request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['branch_id'], ['logistics_branches.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['document_number_id'], ['document_numbers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['document_type_id'], ['document_types.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['document_type_version_id'], ['document_type_versions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['template_version_id'], ['document_template_versions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'document_code', name='uq_document_instance_org_code')
    )
    op.create_index('ix_document_instances_document_code', 'document_instances', ['document_code'])
    op.create_index('ix_document_instances_status', 'document_instances', ['status'])
    op.create_index('ix_document_instances_issued_at', 'document_instances', ['issued_at'])
    op.create_index('ix_document_instances_source_resource', 'document_instances', ['source_resource_type', 'source_resource_id'])

    # 2. document_snapshots
    op.create_table(
        'document_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_version', sa.Integer(), nullable=False),
        sa.Column('snapshot_type', sa.String(length=32), nullable=False),
        sa.Column('snapshot_schema_version', sa.String(length=32), nullable=False),
        sa.Column('canonical_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('canonical_payload_hash', sa.String(length=64), nullable=False),
        sa.Column('document_type_code', sa.String(length=32), nullable=False),
        sa.Column('document_type_version', sa.String(length=32), nullable=False),
        sa.Column('catalog_version', sa.String(length=32), nullable=False),
        sa.Column('template_key', sa.String(length=128), nullable=False),
        sa.Column('template_version', sa.String(length=32), nullable=False),
        sa.Column('renderer_name', sa.String(length=64), nullable=False),
        sa.Column('renderer_version', sa.String(length=32), nullable=False),
        sa.Column('code_standard_version', sa.String(length=32), nullable=False),
        sa.Column('organization_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('branch_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('warehouse_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['document_instances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'snapshot_version', name='uq_document_snapshot_ver')
    )

    # 3. document_artifacts
    op.create_table(
        'document_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('artifact_type', sa.String(length=32), nullable=False),
        sa.Column('representation_status', sa.String(length=32), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('filename', sa.String(length=256), nullable=False),
        sa.Column('storage_provider', sa.String(length=32), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('template_version', sa.String(length=32), nullable=False),
        sa.Column('renderer_version', sa.String(length=32), nullable=False),
        sa.Column('copy_number', sa.Integer(), nullable=True),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_authoritative', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_sensitive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document_instances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['document_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_artifacts_status', 'document_artifacts', ['representation_status'])

    # 4. document_reprints
    op.create_table(
        'document_reprints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_artifact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_artifact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('copy_number', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('step_up_reference', sa.String(length=128), nullable=True),
        sa.Column('idempotency_key_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['document_instances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_artifact_id'], ['document_artifacts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['document_snapshots.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['source_artifact_id'], ['document_artifacts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'copy_number', name='uq_document_reprint_num')
    )

    # 5. document_cancellations
    op.create_table(
        'document_cancellations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issued_artifact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cancelled_artifact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('step_up_reference', sa.String(length=128), nullable=True),
        sa.Column('authorization_reference', sa.String(length=128), nullable=True),
        sa.Column('idempotency_key_hash', sa.String(length=64), nullable=False),
        sa.Column('correlation_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['cancelled_artifact_id'], ['document_artifacts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['document_id'], ['document_instances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issued_artifact_id'], ['document_artifacts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['document_snapshots.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', name='uq_document_cancellation_doc')
    )

    # 6. document_export_jobs
    op.create_table(
        'document_export_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('export_type', sa.String(length=32), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('artifact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['artifact_id'], ['document_artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_export_jobs_status', 'document_export_jobs', ['status'])
    op.create_index('ix_document_export_jobs_expires_at', 'document_export_jobs', ['expires_at'])


def downgrade():
    op.drop_index('ix_document_export_jobs_expires_at', table_name='document_export_jobs')
    op.drop_index('ix_document_export_jobs_status', table_name='document_export_jobs')
    op.drop_table('document_export_jobs')
    op.drop_table('document_cancellations')
    op.drop_table('document_reprints')
    op.drop_index('ix_document_artifacts_status', table_name='document_artifacts')
    op.drop_table('document_artifacts')
    op.drop_table('document_snapshots')
    op.drop_index('ix_document_instances_source_resource', table_name='document_instances')
    op.drop_index('ix_document_instances_issued_at', table_name='document_instances')
    op.drop_index('ix_document_instances_status', table_name='document_instances')
    op.drop_index('ix_document_instances_document_code', table_name='document_instances')
    op.drop_table('document_instances')
