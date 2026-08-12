"""Phase 028 — Vehicle Verifications 10 tables DDL migration.

Revision ID: s310110028dc
Revises: r300110027dc
Create Date: 2026-07-28 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 's310110028dc'
down_revision: Union[str, None] = 's280110028a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. vehicle_verification_sources
    op.create_table(
        'vehicle_verification_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('authority', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='OTHER'),
        sa.Column('base_domain', sa.String(length=255), nullable=True),
        sa.Column('provider_code', sa.String(length=50), nullable=True),
        sa.Column('verification_domains', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'")),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('automation_mode', sa.String(length=50), nullable=False, server_default='MANUAL_ASSISTED'),
        sa.Column('authorization_status', sa.String(length=50), nullable=False, server_default='NOT_EVALUATED'),
        sa.Column('authorization_reference', sa.String(length=255), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('confidence_policy', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('refresh_policy', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('terms_reference', sa.String(length=255), nullable=True),
        sa.Column('privacy_reference', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('last_health_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_call_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failed_call_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 2. vehicle_verification_provider_configurations
    op.create_table(
        'vehicle_verification_provider_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verification_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_code', sa.String(length=50), nullable=False),
        sa.Column('environment', sa.String(length=20), nullable=False, server_default='PRODUCTION'),
        sa.Column('secret_manager_reference', sa.String(length=255), nullable=True),
        sa.Column('endpoint_allowlisted', sa.String(length=255), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('retry_limit', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('circuit_breaker_threshold', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('source_id', 'environment', name='uq_provider_config_source_env'),
    )

    # 3. vehicle_verifications
    op.create_table(
        'vehicle_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('vehicle_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('plate_assignment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_plate_assignments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('normalized_plate', sa.String(length=20), nullable=False, index=True),
        sa.Column('verification_domain', sa.String(length=50), nullable=False, index=True),
        sa.Column('verification_method', sa.String(length=50), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verification_sources.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('provider_code', sa.String(length=50), nullable=True),
        sa.Column('request_reference', sa.String(length=100), nullable=True),
        sa.Column('external_reference', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT', index=True),
        sa.Column('result_status', sa.String(length=30), nullable=False, server_default='UNKNOWN', index=True),
        sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='NOT_EVALUATED'),
        sa.Column('source_data_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('stale_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_verification_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('verified_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('original_response_hash', sa.String(length=64), nullable=True),
        sa.Column('normalized_result_hash', sa.String(length=64), nullable=True),
        sa.Column('evidence_status', sa.String(length=30), nullable=False, server_default='NO_EVIDENCE'),
        sa.Column('conflict_status', sa.String(length=30), nullable=False, server_default='NO_CONFLICT'),
        sa.Column('supersedes_verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verifications.id', ondelete='SET NULL'), nullable=True),
        sa.Column('superseded_by_verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verifications.id', ondelete='SET NULL'), nullable=True),
        sa.Column('failure_code', sa.String(length=50), nullable=True),
        sa.Column('failure_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 4. vehicle_verification_results
    op.create_table(
        'vehicle_verification_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verifications.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('queried_plate', sa.String(length=20), nullable=False),
        sa.Column('source_plate', sa.String(length=20), nullable=True),
        sa.Column('registered_owner_name', sa.String(length=255), nullable=True),
        sa.Column('registered_owner_identifier_masked', sa.String(length=50), nullable=True),
        sa.Column('make', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('manufacturing_year', sa.Integer(), nullable=True),
        sa.Column('vin_masked', sa.String(length=50), nullable=True),
        sa.Column('chassis_masked', sa.String(length=50), nullable=True),
        sa.Column('engine_number_masked', sa.String(length=50), nullable=True),
        sa.Column('registration_status', sa.String(length=50), nullable=True),
        sa.Column('transport_authorization_status', sa.String(length=50), nullable=True),
        sa.Column('technical_inspection_status', sa.String(length=50), nullable=True),
        sa.Column('technical_inspection_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('insurance_type', sa.String(length=50), nullable=True),
        sa.Column('insurance_status', sa.String(length=50), nullable=True),
        sa.Column('insurance_provider', sa.String(length=100), nullable=True),
        sa.Column('insurance_policy_masked', sa.String(length=50), nullable=True),
        sa.Column('insurance_valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('insurance_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('liens_status', sa.String(length=50), nullable=True),
        sa.Column('restrictions_summary', sa.Text(), nullable=True),
        sa.Column('normalized_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('schema_version', sa.String(length=20), nullable=False, server_default='1.0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 5. vehicle_verification_field_provenance
    op.create_table(
        'vehicle_verification_field_provenance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verifications.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('normalized_value', sa.Text(), nullable=True),
        sa.Column('raw_value_hash', sa.String(length=64), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verification_sources.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('source_data_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='NOT_EVALUATED'),
        sa.Column('selected', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('conflict_status', sa.String(length=30), nullable=False, server_default='NO_CONFLICT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 6. vehicle_verification_evidence
    op.create_table(
        'vehicle_verification_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verifications.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('file_reference_id', sa.String(length=255), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('captured_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('retention_policy', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 7. assisted_vehicle_verifications
    op.create_table(
        'assisted_vehicle_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('plate_assignment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_plate_assignments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verification_domain', sa.String(length=50), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verification_sources.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('verification_reason', sa.Text(), nullable=False),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('observed_plate', sa.String(length=20), nullable=False),
        sa.Column('observed_owner', sa.String(length=255), nullable=True),
        sa.Column('observed_make', sa.String(length=100), nullable=True),
        sa.Column('observed_model', sa.String(length=100), nullable=True),
        sa.Column('observed_year', sa.Integer(), nullable=True),
        sa.Column('observed_status', sa.String(length=50), nullable=True),
        sa.Column('observed_expiration', sa.DateTime(timezone=True), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('evidence_reference_id', sa.String(length=255), nullable=True),
        sa.Column('result_status', sa.String(length=30), nullable=False, server_default='FOUND'),
        sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('approval_status', sa.String(length=30), nullable=False, server_default='SUBMITTED', index=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 8. vehicle_verification_conflicts
    op.create_table(
        'vehicle_verification_conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verifications.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('conflict_type', sa.String(length=50), nullable=False),
        sa.Column('master_value_hash', sa.String(length=64), nullable=True),
        sa.Column('verified_value_hash', sa.String(length=64), nullable=True),
        sa.Column('master_display_value', sa.Text(), nullable=True),
        sa.Column('verified_display_value', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN', index=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution', sa.String(length=50), nullable=True),
        sa.Column('resolution_reason', sa.Text(), nullable=True),
        sa.Column('applied_vehicle_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 9. vehicle_verification_requirements
    op.create_table(
        'vehicle_verification_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('vehicle_type', sa.String(length=50), nullable=True),
        sa.Column('body_type', sa.String(length=50), nullable=True),
        sa.Column('ownership_type', sa.String(length=30), nullable=True),
        sa.Column('carrier_category', sa.String(length=50), nullable=True),
        sa.Column('verification_domain', sa.String(length=50), nullable=False, index=True),
        sa.Column('source_type_preference', sa.String(length=50), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('blocking', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('maximum_age_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('warning_days_before_expiration', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('minimum_confidence', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('allow_assisted_verification', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('requires_evidence', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE', index=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 10. vehicle_verification_review_tasks
    op.create_table(
        'vehicle_verification_review_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('verification_domain', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN', index=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verification_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('related_verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_verifications.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_result', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('vehicle_verification_review_tasks')
    op.drop_table('vehicle_verification_requirements')
    op.drop_table('vehicle_verification_conflicts')
    op.drop_table('assisted_vehicle_verifications')
    op.drop_table('vehicle_verification_evidence')
    op.drop_table('vehicle_verification_field_provenance')
    op.drop_table('vehicle_verification_results')
    op.drop_table('vehicle_verifications')
    op.drop_table('vehicle_verification_provider_configurations')
    op.drop_table('vehicle_verification_sources')
