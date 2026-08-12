"""add document series and talonario tables

Revision ID: d330640013dc
Revises: c220530012dc
Create Date: 2026-07-26 22:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d330640013dc"
down_revision: Union[str, None] = "c220530012dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_series",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("document_site_code_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_site_codes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_types.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("document_year", sa.Integer(), nullable=False),
        sa.Column("code_standard_version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("sequence_scope", sa.String(64), nullable=False, server_default="TYPE_SITE_YEAR"),
        sa.Column("prefix", sa.String(64), nullable=False),
        sa.Column("sequence_start", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("next_sequence", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sequence_max", sa.Integer(), nullable=False, server_default="999999"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("lock_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("close_reason", sa.Text(), nullable=True),
        sa.Column("exhausted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "document_type_id", "document_site_code_id", "document_year", name="uq_document_series_scope"),
        sa.CheckConstraint("next_sequence >= sequence_start", name="ck_series_next_seq_ge_start"),
        sa.CheckConstraint("next_sequence <= sequence_max + 1", name="ck_series_next_seq_le_max"),
    )
    op.create_index("ix_document_series_org", "document_series", ["organization_id"])
    op.create_index("ix_document_series_branch", "document_series", ["branch_id"])
    op.create_index("ix_document_series_status", "document_series", ["status"])

    op.create_table(
        "document_talonarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("series_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_series.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("talonario_code", sa.String(128), nullable=False),
        sa.Column("range_start", sa.Integer(), nullable=False),
        sa.Column("range_end", sa.Integer(), nullable=False),
        sa.Column("total_numbers", sa.Integer(), nullable=False),
        sa.Column("reserved_numbers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assigned_numbers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("issued_numbers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancelled_numbers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("voided_numbers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_numbers", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="RESERVED"),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reserved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("exhausted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("request_hash", sa.String(128), nullable=True),
        sa.Column("manifest_version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "talonario_code", name="uq_document_talonario_code"),
        sa.CheckConstraint("range_end >= range_start", name="ck_talonario_range_end_ge_start"),
        sa.CheckConstraint("total_numbers > 0", name="ck_talonario_total_gt_zero"),
    )
    op.create_index("ix_document_talonarios_series_id", "document_talonarios", ["series_id"])
    op.create_index("ix_document_talonarios_status", "document_talonarios", ["status"])

    op.create_table(
        "document_numbers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("series_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_series.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("talonario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_talonarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("full_document_code", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="RESERVED"),
        sa.Column("reservation_type", sa.String(32), nullable=False, server_default="INDIVIDUAL"),
        sa.Column("reservation_purpose", sa.Text(), nullable=True),
        sa.Column("reserved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reserved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("assigned_resource_type", sa.String(64), nullable=True),
        sa.Column("assigned_resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("correlation_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("series_id", "sequence_number", name="uq_document_number_series_seq"),
        sa.UniqueConstraint("organization_id", "full_document_code", name="uq_document_number_org_code"),
        sa.CheckConstraint("sequence_number >= 1", name="ck_document_number_seq_ge_1"),
    )
    op.create_index("ix_document_numbers_series_id", "document_numbers", ["series_id"])
    op.create_index("ix_document_numbers_talonario_id", "document_numbers", ["talonario_id"])
    op.create_index("ix_document_numbers_status", "document_numbers", ["status"])

    op.create_table(
        "idempotency_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(128), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="COMPLETED"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "operation", "idempotency_key", name="uq_idempotency_record"),
    )


def downgrade() -> None:
    op.drop_table("idempotency_records")
    op.drop_table("document_numbers")
    op.drop_table("document_talonarios")
    op.drop_table("document_series")
