"""Add document template and version tables (Phase 014).

Revision ID: e440750014dc
Revises: d330640013dc
Create Date: 2026-07-26 22:12:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e440750014dc'
down_revision: Union[str, None] = 'd330640013dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'document_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('template_key', sa.String(length=128), nullable=False),
        sa.Column('document_family_code', sa.String(length=64), nullable=False),
        sa.Column('document_type_code', sa.String(length=32), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_document_templates_template_key', 'document_templates', ['template_key'], unique=True)
    op.create_index('ix_document_templates_family', 'document_templates', ['document_family_code'])
    op.create_index('ix_document_templates_status', 'document_templates', ['status'])

    op.create_table(
        'document_template_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False),
        sa.Column('engine', sa.String(length=64), nullable=False, server_default='Jinja2+WeasyPrint'),
        sa.Column('engine_version', sa.String(length=32), nullable=False, server_default='1.0.0'),
        sa.Column('html_path', sa.String(length=256), nullable=False),
        sa.Column('css_paths', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('schema_version', sa.String(length=32), nullable=False, server_default='1.0.0'),
        sa.Column('content_hash', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('template_id', 'version', name='uq_template_version'),
    )
    op.create_index('ix_document_template_versions_template_id', 'document_template_versions', ['template_id'])
    op.create_index('ix_document_template_versions_status', 'document_template_versions', ['status'])

    op.create_table(
        'document_template_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('template_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_template_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_key', sa.String(length=128), nullable=False),
        sa.Column('asset_type', sa.String(length=32), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('content_hash', sa.String(length=128), nullable=False),
        sa.Column('storage_reference', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_document_template_assets_version_id', 'document_template_assets', ['template_version_id'])


def downgrade() -> None:
    op.drop_table('document_template_assets')
    op.drop_table('document_template_versions')
    op.drop_table('document_templates')
