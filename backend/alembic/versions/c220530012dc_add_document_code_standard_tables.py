"""add document code standard tables

Revision ID: c220530012dc
Revises: b119420011dc
Create Date: 2026-07-26 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c220530012dc"
down_revision: Union[str, None] = "b119420011dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_code_standards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, server_default="STD_LOGISTICS_CODE"),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("name", sa.String(128), nullable=False, server_default="Estándar TIPO-SEDE-AÑO-CORRELATIVO"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pattern", sa.String(128), nullable=False, server_default="^[A-Z0-9]{2,8}-[A-Z0-9]{2,10}-[0-9]{4}-[0-9]{6}$"),
        sa.Column("separator", sa.String(4), nullable=False, server_default="-"),
        sa.Column("document_type_min_length", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("document_type_max_length", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("site_code_min_length", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("site_code_max_length", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("year_length", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("sequence_length", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("sequence_start", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sequence_max", sa.Integer(), nullable=False, server_default="999999"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", "version", name="uq_document_code_standard_version"),
    )
    op.create_index("ix_document_code_standards_status", "document_code_standards", ["status"])

    op.create_table(
        "document_site_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "code", name="uq_document_site_code_org"),
    )
    op.create_index("ix_document_site_codes_organization_id", "document_site_codes", ["organization_id"])
    op.create_index("ix_document_site_codes_branch_id", "document_site_codes", ["branch_id"])
    op.create_index("ix_document_site_codes_status", "document_site_codes", ["status"])

    op.create_table(
        "document_type_code_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code_standard_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_code_standards.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("uses_internal_code", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("uses_site_segment", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("uses_year_segment", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("uses_sequence_segment", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sequence_scope", sa.String(64), nullable=False, server_default="TYPE_SITE_YEAR"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("document_type_id", name="uq_document_type_code_policy"),
    )


def downgrade() -> None:
    op.drop_table("document_type_code_policies")
    op.drop_table("document_site_codes")
    op.drop_table("document_code_standards")
