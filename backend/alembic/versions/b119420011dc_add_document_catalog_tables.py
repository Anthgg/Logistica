"""add document catalog tables

Revision ID: b119420011dc
Revises: f0424c5e9d46
Create Date: 2026-07-26 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b119420011dc"
down_revision: Union[str, None] = "f0424c5e9d46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_families",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_module", sa.String(64), nullable=False, server_default="logistics"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_document_families_code", "document_families", ["code"])
    op.create_index("ix_document_families_status", "document_families", ["status"])

    op.create_table(
        "document_retention_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("minimum_retention_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("maximum_retention_days", sa.Integer(), nullable=True),
        sa.Column("archive_after_days", sa.Integer(), nullable=True),
        sa.Column("deletion_allowed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("legal_hold_supported", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_manual_review", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("applies_to_origin_type", sa.String(64), nullable=False, server_default="INTERNAL_GENERATED"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_document_retention_policies_code", "document_retention_policies", ["code"])

    op.create_table(
        "document_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("short_name", sa.String(64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_families.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("origin_type", sa.String(64), nullable=False),
        sa.Column("owner_module", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("operation_type", sa.String(64), nullable=False),
        sa.Column("catalog_status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_official_external", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supports_internal_number", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_external_number", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supports_series", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_talonario", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supports_preview", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_issue", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_download", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_bulk_download", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supports_reprint", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_cancel", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_public_verification", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_qr", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_signature", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_reason_on_reprint", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_reason_on_cancel", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_document_types_code", "document_types", ["code"])
    op.create_index("ix_document_types_family_id", "document_types", ["family_id"])

    op.create_table(
        "document_type_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("schema_version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("required_fields_schema", postgresql.JSONB(), nullable=False),
        sa.Column("optional_fields_schema", postgresql.JSONB(), nullable=True),
        sa.Column("sections_schema", postgresql.JSONB(), nullable=True),
        sa.Column("allowed_statuses", postgresql.JSONB(), nullable=False),
        sa.Column("permission_policy", postgresql.JSONB(), nullable=False),
        sa.Column("retention_policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_retention_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("template_key", sa.String(128), nullable=False, server_default="PENDING_PHASE_014"),
        sa.Column("template_version", sa.String(32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("document_type_id", "version", name="uq_document_type_version"),
    )
    op.create_index("ix_document_type_versions_document_type_id", "document_type_versions", ["document_type_id"])

    op.create_table(
        "document_catalog_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.String(32), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("manifest_data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_document_catalog_versions_version", "document_catalog_versions", ["version"])

    # Seed the stable family keys required by the following document-type
    # migrations.  The full catalog seeder can enrich these rows later.
    families = sa.table(
        "document_families",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("owner_module", sa.String()),
        sa.column("display_order", sa.Integer()),
        sa.column("status", sa.String()),
    )
    family_names = {
        "PURCHASING": "Compras",
        "INBOUND": "Recepción",
        "QUALITY": "Calidad",
        "INVENTORY": "Inventario",
        "OUTBOUND": "Salidas",
        "DISPATCH": "Despacho",
        "TRANSPORT": "Transporte",
        "DELIVERY": "Entrega",
        "REVERSE_LOGISTICS": "Logística inversa",
        "GENERIC": "Documentos generales",
    }
    for display_order, (code, name) in enumerate(family_names.items(), start=1):
        op.execute(
            postgresql.insert(families)
            .values(
                id=sa.text("gen_random_uuid()"),
                code=code,
                name=name,
                description=f"Familia documental {name}",
                owner_module="logistics",
                display_order=display_order,
                status="ACTIVE",
            )
            .on_conflict_do_nothing(index_elements=[families.c.code])
        )


def downgrade() -> None:
    op.drop_table("document_catalog_versions")
    op.drop_table("document_type_versions")
    op.drop_table("document_types")
    op.drop_table("document_retention_policies")
    op.drop_table("document_families")
