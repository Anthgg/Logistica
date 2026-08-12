"""Phase 030 - Files and Evidence Centralization

Revision ID: u320110030dc
Revises: u310110030dc
Create Date: 2026-07-29 01:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'u320110030dc'
down_revision = 'u310110030dc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. file_assets
    op.create_table(
        'file_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_code', sa.String(length=50), nullable=False),
        sa.Column('normalized_file_code', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_type', sa.String(length=50), nullable=False, server_default='DOCUMENT'),
        sa.Column('classification', sa.String(length=50), nullable=False, server_default='CONFIDENTIAL'),
        sa.Column('lifecycle_status', sa.String(length=50), nullable=False, server_default='QUARANTINED'),
        sa.Column('evidence_status', sa.String(length=50), nullable=False, server_default='NOT_EVIDENCE'),
        sa.Column('owner_type', sa.String(length=50), nullable=False, server_default='ORGANIZATION'),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('owner_resource_type', sa.String(length=50), nullable=True),
        sa.Column('owner_resource_id', sa.String(length=100), nullable=True),
        sa.Column('current_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('retention_policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('access_scope', sa.String(length=50), nullable=False, server_default='RESOURCE_INHERITED'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('archive_reason', sa.Text(), nullable=True),
        sa.Column('deletion_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deletion_requested_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('organization_id', 'normalized_file_code', name='uq_file_assets_org_code'),
    )
    op.create_index('idx_file_assets_org_id', 'file_assets', ['organization_id'])
    op.create_index('idx_file_assets_org_type', 'file_assets', ['organization_id', 'asset_type'])
    op.create_index('idx_file_assets_org_status', 'file_assets', ['organization_id', 'lifecycle_status'])

    # 2. file_versions
    op.create_table(
        'file_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUARANTINED'),
        sa.Column('storage_provider', sa.String(length=50), nullable=False, server_default='GCS'),
        sa.Column('bucket_reference', sa.String(length=100), nullable=False),
        sa.Column('object_key', sa.String(length=500), nullable=False),
        sa.Column('object_generation', sa.String(length=100), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('sanitized_filename', sa.String(length=255), nullable=False),
        sa.Column('extension', sa.String(length=20), nullable=False),
        sa.Column('declared_MIME_type', sa.String(length=100), nullable=False),
        sa.Column('detected_MIME_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('SHA256', sa.String(length=64), nullable=False),
        sa.Column('CRC32C', sa.String(length=50), nullable=True),
        sa.Column('MD5', sa.String(length=50), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('image_width', sa.Integer(), nullable=True),
        sa.Column('image_height', sa.Integer(), nullable=True),
        sa.Column('XML_root_element', sa.String(length=100), nullable=True),
        sa.Column('schema_reference', sa.String(length=255), nullable=True),
        sa.Column('content_validation_status', sa.String(length=50), nullable=False, server_default='VALID'),
        sa.Column('malware_scan_status', sa.String(length=50), nullable=False, server_default='NOT_SCANNED'),
        sa.Column('malware_scanner_version', sa.String(length=100), nullable=True),
        sa.Column('metadata_schema_version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='UPLOAD'),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supersedes_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('file_asset_id', 'version_number', name='uq_file_versions_asset_version'),
        sa.UniqueConstraint('storage_provider', 'bucket_reference', 'object_key', name='uq_file_versions_storage_location'),
    )
    op.create_index('idx_file_versions_asset_id', 'file_versions', ['file_asset_id'])
    op.create_index('idx_file_versions_sha256', 'file_versions', ['SHA256'])
    op.create_index('idx_file_versions_status', 'file_versions', ['status'])

    # 3. file_metadata
    op.create_table(
        'file_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_type', sa.String(length=100), nullable=True),
        sa.Column('document_number', sa.String(length=100), nullable=True),
        sa.Column('issuer', sa.String(length=150), nullable=True),
        sa.Column('issued_at', sa.Date(), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('expires_at', sa.Date(), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('event_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='es'),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 4. file_ownerships
    op.create_table(
        'file_ownerships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_type', sa.String(length=50), nullable=False, server_default='ORGANIZATION'),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('owner_role_reference', sa.String(length=100), nullable=True),
        sa.Column('custodian_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('owner_resource_type', sa.String(length=50), nullable=True),
        sa.Column('owner_resource_id', sa.String(length=100), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 5. file_associations
    op.create_table(
        'file_associations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('association_type', sa.String(length=50), nullable=False, server_default='ATTACHMENT'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('removed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removal_reason', sa.Text(), nullable=True),
    )
    op.create_index('idx_file_assoc_resource', 'file_associations', ['organization_id', 'resource_type', 'resource_id'])

    # 6. file_access_grants
    op.create_table(
        'file_access_grants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('principal_type', sa.String(length=50), nullable=False),
        sa.Column('principal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('allowed_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 7. file_upload_sessions
    op.create_table(
        'file_upload_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('intended_resource_type', sa.String(length=50), nullable=True),
        sa.Column('intended_resource_id', sa.String(length=100), nullable=True),
        sa.Column('intended_association_type', sa.String(length=50), nullable=True),
        sa.Column('expected_filename', sa.String(length=255), nullable=False),
        sa.Column('expected_size_bytes', sa.Integer(), nullable=False),
        sa.Column('declared_MIME_type', sa.String(length=100), nullable=False),
        sa.Column('expected_SHA256', sa.String(length=64), nullable=True),
        sa.Column('upload_mode', sa.String(length=50), nullable=False, server_default='DIRECT_SIGNED'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CREATED'),
        sa.Column('quarantine_object_key', sa.String(length=500), nullable=False),
        sa.Column('storage_upload_reference', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('finalized_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_code', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 8. file_integrity_records
    op.create_table(
        'file_integrity_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('SHA256', sa.String(length=64), nullable=False),
        sa.Column('storage_checksum', sa.String(length=64), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('calculator_version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='VERIFIED'),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_verification_result', sa.Text(), nullable=True),
        sa.Column('mismatch_detected_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 9. signature_artifact_metadata
    op.create_table(
        'signature_artifact_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('signature_kind', sa.String(length=50), nullable=False, server_default='VISUAL_SIGNATURE_IMAGE'),
        sa.Column('signer_reference', sa.String(length=255), nullable=True),
        sa.Column('signed_file_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('certificate_subject_masked', sa.String(length=255), nullable=True),
        sa.Column('certificate_issuer', sa.String(length=255), nullable=True),
        sa.Column('certificate_serial_hash', sa.String(length=64), nullable=True),
        sa.Column('signature_format', sa.String(length=50), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='FORMAT_VALID'),
        sa.Column('verification_source', sa.String(length=100), nullable=False, server_default='INTERNAL_INSPECTOR'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 10. evidence_records
    op.create_table(
        'evidence_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evidence_code', sa.String(length=50), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('subject_type', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.String(length=100), nullable=False),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('captured_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('captured_by_system', sa.String(length=100), nullable=True),
        sa.Column('acquisition_method', sa.String(length=100), nullable=False, server_default='SYSTEM_CAPTURE'),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='LOGISTICS_PLATFORM'),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('location_reference', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CANDIDATE'),
        sa.Column('acceptance_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('accepted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.Text(), nullable=True),
        sa.Column('chain_of_custody_status', sa.String(length=50), nullable=False, server_default='VALID'),
        sa.Column('retention_policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('organization_id', 'evidence_code', name='uq_evidence_records_org_code'),
    )

    # 11. evidence_custody_events
    op.create_table(
        'evidence_custody_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evidence_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_type', sa.String(length=50), nullable=False, server_default='USER'),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_service', sa.String(length=100), nullable=True),
        sa.Column('source_IP_hash', sa.String(length=64), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('device_reference', sa.String(length=255), nullable=True),
        sa.Column('event_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('previous_hash', sa.String(length=64), nullable=True),
        sa.Column('event_hash', sa.String(length=64), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 12. file_retention_policies
    op.create_table(
        'file_retention_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=True),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('minimum_retention_days', sa.Integer(), nullable=False, server_default='365'),
        sa.Column('archive_after_days', sa.Integer(), nullable=True),
        sa.Column('delete_after_days', sa.Integer(), nullable=True),
        sa.Column('deletion_mode', sa.String(length=50), nullable=False, server_default='REVIEW_REQUIRED'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('legal_basis_reference', sa.String(length=255), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 13. file_legal_holds
    op.create_table(
        'file_legal_holds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('authority_reference', sa.String(length=255), nullable=True),
        sa.Column('applied_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('released_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('release_reason', sa.Text(), nullable=True),
    )

    # 14. file_deletion_requests
    op.create_table(
        'file_deletion_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('deletion_basis', sa.String(length=100), nullable=False, server_default='USER_REQUEST'),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='REQUESTED'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('scheduled_purge_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 15. file_processing_jobs
    op.create_table(
        'file_processing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('file_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('file_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('upload_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('file_processing_jobs')
    op.drop_table('file_deletion_requests')
    op.drop_table('file_legal_holds')
    op.drop_table('file_retention_policies')
    op.drop_table('evidence_custody_events')
    op.drop_table('evidence_records')
    op.drop_table('signature_artifact_metadata')
    op.drop_table('file_integrity_records')
    op.drop_table('file_upload_sessions')
    op.drop_table('file_access_grants')
    op.drop_table('file_associations')
    op.drop_table('file_ownerships')
    op.drop_table('file_metadata')
    op.drop_table('file_versions')
    op.drop_table('file_assets')
