"""Phase 026 — RUC Lookup and SUNAT Reduced Registry Integration Migration.

Revision ID: q280110026dc
Revises: p270110025dc
Create Date: 2026-07-28 17:15:00.000000

Creates 8 tables for Phase 026:
  1. ruc_data_sources
  2. ruc_dataset_versions
  3. ruc_import_jobs
  4. ruc_registry_entries
  5. ruc_registry_annex_addresses
  6. ruc_assisted_verifications
  7. business_partner_ruc_verifications
  8. ruc_data_conflicts
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'q280110026dc'
down_revision: Union[str, None] = 'p270110025dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ruc_data_sources
    op.create_table(
        'ruc_data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),  # OFFICIAL_REDUCED_REGISTRY, AUTHORIZED_PROVIDER, etc.
        sa.Column('authority', sa.String(length=100), nullable=False, server_default='SUNAT'),
        sa.Column('source_reference', sa.String(length=500), nullable=False),
        sa.Column('base_domain', sa.String(length=200), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=sa.text('10')),
        sa.Column('confidence_policy', postgresql.JSONB(), nullable=True),
        sa.Column('refresh_policy', postgresql.JSONB(), nullable=True),
        sa.Column('licensing_reference', sa.String(length=255), nullable=True),
        sa.Column('terms_reference', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('last_successful_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failed_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 2. ruc_dataset_versions
    op.create_table(
        'ruc_dataset_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ruc_data_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dataset_type', sa.String(length=40), nullable=False),  # RUC_GENERAL, RUC_ANNEX_ADDRESS
        sa.Column('source_published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('import_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('import_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DISCOVERED'),
        sa.Column('parser_version', sa.String(length=30), nullable=False, server_default='1.0.0'),
        sa.Column('schema_version', sa.String(length=30), nullable=False, server_default='1.0.0'),
        sa.Column('source_filename', sa.String(length=255), nullable=True),
        sa.Column('compressed_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('uncompressed_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('archive_hash', sa.String(length=64), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('total_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('accepted_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('rejected_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('duplicate_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('inserted_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('updated_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('unchanged_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('removed_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('warning_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('import_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('activated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_ruc_dataset_versions_type_status', 'ruc_dataset_versions', ['dataset_type', 'status'])

    # 3. ruc_import_jobs
    op.create_table(
        'ruc_import_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ruc_data_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dataset_type', sa.String(length=40), nullable=False),
        sa.Column('trigger_type', sa.String(length=30), nullable=False, server_default='SCHEDULED'),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='QUEUED'),
        sa.Column('idempotency_key_hash', sa.String(length=64), nullable=True, index=True),
        sa.Column('request_hash', sa.String(length=64), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_stage', sa.String(length=50), nullable=False, server_default='INIT'),
        sa.Column('progress_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('downloaded_bytes', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('processed_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('accepted_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('rejected_rows', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('error_code', sa.String(length=80), nullable=True),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 4. ruc_registry_entries
    op.create_table(
        'ruc_registry_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ruc_dataset_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ruc', sa.String(length=11), nullable=False),
        sa.Column('normalized_ruc', sa.String(length=11), nullable=False, index=True),
        sa.Column('legal_name', sa.String(length=300), nullable=False),
        sa.Column('normalized_legal_name', sa.String(length=300), nullable=False, index=True),
        sa.Column('taxpayer_status_raw', sa.String(length=100), nullable=True),
        sa.Column('taxpayer_status_normalized', sa.String(length=50), nullable=False, server_default='UNKNOWN'),
        sa.Column('domicile_condition_raw', sa.String(length=100), nullable=True),
        sa.Column('domicile_condition_normalized', sa.String(length=50), nullable=False, server_default='UNKNOWN'),
        sa.Column('ubigeo_code', sa.String(length=10), nullable=True, index=True),
        sa.Column('source_published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('imported_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('record_hash', sa.String(length=64), nullable=False),
        sa.Column('row_status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
    )
    op.create_index('uix_ruc_registry_dataset_ruc', 'ruc_registry_entries', ['dataset_version_id', 'normalized_ruc'], unique=True)
    op.create_index('ix_ruc_registry_status_cond', 'ruc_registry_entries', ['taxpayer_status_normalized', 'domicile_condition_normalized'])

    # 5. ruc_registry_annex_addresses
    op.create_table(
        'ruc_registry_annex_addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ruc_dataset_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ruc', sa.String(length=11), nullable=False, index=True),
        sa.Column('ubigeo_code', sa.String(length=10), nullable=True, index=True),
        sa.Column('address_raw', sa.Text(), nullable=False),
        sa.Column('address_normalized', sa.Text(), nullable=True),
        sa.Column('source_published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('imported_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('record_hash', sa.String(length=64), nullable=False),
        sa.Column('row_status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
    )
    op.create_index('ix_ruc_annex_dataset_ruc', 'ruc_registry_annex_addresses', ['dataset_version_id', 'ruc'])

    # 6. ruc_assisted_verifications
    op.create_table(
        'ruc_assisted_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ruc', sa.String(length=11), nullable=False, index=True),
        sa.Column('verification_reason', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='ASSISTED_OFFICIAL_REVIEW'),
        sa.Column('source_reference', sa.String(length=255), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('observed_legal_name', sa.String(length=300), nullable=True),
        sa.Column('observed_status', sa.String(length=50), nullable=True),
        sa.Column('observed_condition', sa.String(length=50), nullable=True),
        sa.Column('observed_ubigeo', sa.String(length=10), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('evidence_reference_id', sa.String(length=255), nullable=True),
        sa.Column('result', sa.String(length=30), nullable=False, server_default='MATCH_CONFIRMED'),
        sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 7. business_partner_ruc_verifications
    op.create_table(
        'business_partner_ruc_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('identifier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partner_identifiers.id', ondelete='CASCADE'), nullable=True),
        sa.Column('ruc', sa.String(length=11), nullable=False, index=True),
        sa.Column('verification_method', sa.String(length=50), nullable=False),  # OFFICIAL_REGISTRY, AUTHORIZED_PROVIDER, ASSISTED
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('dataset_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ruc_dataset_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('provider_code', sa.String(length=50), nullable=True),
        sa.Column('assisted_verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ruc_assisted_verifications.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verification_result', sa.String(length=30), nullable=False, server_default='VERIFIED'),
        sa.Column('verified_legal_name', sa.String(length=300), nullable=True),
        sa.Column('verified_taxpayer_status', sa.String(length=50), nullable=True),
        sa.Column('verified_domicile_condition', sa.String(length=50), nullable=True),
        sa.Column('verified_ubigeo', sa.String(length=10), nullable=True),
        sa.Column('source_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='HIGH'),
        sa.Column('snapshot_payload', postgresql.JSONB(), nullable=False),
        sa.Column('snapshot_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='CURRENT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_bp_ruc_verif_bp_id', 'business_partner_ruc_verifications', ['business_partner_id', 'status'])

    # 8. ruc_data_conflicts
    op.create_table(
        'ruc_data_conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=True),
        sa.Column('ruc', sa.String(length=11), nullable=False, index=True),
        sa.Column('conflict_type', sa.String(length=50), nullable=False),  # LEGAL_NAME_MISMATCH, STATUS_MISMATCH, UBIGEO_MISMATCH, etc.
        sa.Column('source_a', sa.String(length=50), nullable=False),
        sa.Column('value_a', sa.Text(), nullable=True),
        sa.Column('source_b', sa.String(length=50), nullable=False),
        sa.Column('value_b', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('ruc_data_conflicts')
    op.drop_table('business_partner_ruc_verifications')
    op.drop_table('ruc_assisted_verifications')
    op.drop_table('ruc_registry_annex_addresses')
    op.drop_table('ruc_registry_entries')
    op.drop_table('ruc_import_jobs')
    op.drop_table('ruc_dataset_versions')
    op.drop_table('ruc_data_sources')
