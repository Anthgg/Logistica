"""Add controlled research protocol metadata.

Revision ID: 20260725_0003
Revises: cac33004e190
Create Date: 2026-07-25 21:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260725_0003"
down_revision: str | None = "cac33004e190"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "experimental_sessions",
        sa.Column(
            "protocol_version",
            sa.String(length=50),
            nullable=False,
            server_default="pilot-protocol-v0.1.0",
        ),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column(
            "collector_version",
            sa.String(length=50),
            nullable=False,
            server_default="web-v0.1.0",
        ),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("identity_label", sa.String(length=20), nullable=False, server_default="genuine"),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column(
            "sample_role", sa.String(length=30), nullable=False, server_default="verification"
        ),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("operator_change_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("presentation_label", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("attack_type", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("source_device", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("pad_source_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column(
            "annotation_status", sa.String(length=20), nullable=False, server_default="pending"
        ),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("annotated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("annotated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "experimental_sessions", sa.Column("annotation_notes", sa.Text(), nullable=True)
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("capture_interval_seconds", sa.Integer(), nullable=False, server_default="5"),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("batch_interval_seconds", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("max_batch_events", sa.Integer(), nullable=False, server_default="100"),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column(
            "max_image_size_bytes", sa.Integer(), nullable=False, server_default="1048576"
        ),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("client_timezone_offset_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("client_language", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "experimental_sessions",
        sa.Column("screen_pixel_ratio", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    if op.get_bind().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_experimental_sessions_annotated_by_users",
            "experimental_sessions",
            "users",
            ["annotated_by"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_experimental_sessions_annotation_status",
        "experimental_sessions",
        ["annotation_status"],
    )
    op.create_index(
        "ix_experimental_sessions_annotated_by",
        "experimental_sessions",
        ["annotated_by"],
    )
    if op.get_bind().dialect.name != "sqlite":
        op.create_check_constraint(
            "ck_experimental_sessions_identity_label",
            "experimental_sessions",
            "identity_label IN ('genuine', 'impostor')",
        )
        op.create_check_constraint(
            "ck_experimental_sessions_sample_role",
            "experimental_sessions",
            "sample_role IN ('enrollment', 'verification', 'change_operator')",
        )
        op.create_check_constraint(
            "ck_experimental_sessions_annotation_status",
            "experimental_sessions",
            "annotation_status IN ('pending', 'confirmed')",
        )
        op.create_check_constraint(
            "ck_experimental_sessions_presentation_label",
            "experimental_sessions",
            "presentation_label IS NULL OR presentation_label IN ('bona_fide', 'attack')",
        )
        op.create_check_constraint(
            "ck_experimental_sessions_attack_type",
            "experimental_sessions",
            "attack_type IS NULL OR attack_type IN "
            "('none', 'printed_photo', 'screen_photo', 'replayed_video')",
        )
        op.create_check_constraint(
            "ck_experimental_sessions_timezone_offset",
            "experimental_sessions",
            "client_timezone_offset_minutes IS NULL OR "
            "client_timezone_offset_minutes BETWEEN -840 AND 840",
        )

    op.add_column(
        "facial_captures",
        sa.Column("client_timezone_offset_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "facial_captures",
        sa.Column("capture_source", sa.String(length=30), nullable=False, server_default="webcam"),
    )
    op.add_column(
        "facial_captures",
        sa.Column("camera_facing_mode", sa.String(length=20), nullable=True),
    )
    if op.get_bind().dialect.name != "sqlite":
        op.create_check_constraint(
            "ck_facial_captures_timezone_offset",
            "facial_captures",
            "client_timezone_offset_minutes IS NULL OR "
            "client_timezone_offset_minutes BETWEEN -840 AND 840",
        )
        op.create_check_constraint(
            "ck_facial_captures_source",
            "facial_captures",
            "capture_source IN ('webcam', 'controlled_upload')",
        )

    op.add_column(
        "behavioral_batches",
        sa.Column("visibility_state", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "behavioral_batches",
        sa.Column("client_timezone_offset_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "behavioral_batches",
        sa.Column("dropped_event_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "behavioral_batches",
        sa.Column("collector_error_count", sa.Integer(), nullable=False, server_default="0"),
    )
    if op.get_bind().dialect.name != "sqlite":
        op.create_check_constraint(
            "ck_behavioral_batches_timezone_offset",
            "behavioral_batches",
            "client_timezone_offset_minutes IS NULL OR "
            "client_timezone_offset_minutes BETWEEN -840 AND 840",
        )
        op.create_check_constraint(
            "ck_behavioral_batches_dropped_events",
            "behavioral_batches",
            "dropped_event_count >= 0",
        )
        op.create_check_constraint(
            "ck_behavioral_batches_collector_errors",
            "behavioral_batches",
            "collector_error_count >= 0",
        )


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(
            "ck_behavioral_batches_collector_errors",
            "behavioral_batches",
            type_="check",
        )
        op.drop_constraint(
            "ck_behavioral_batches_dropped_events",
            "behavioral_batches",
            type_="check",
        )
        op.drop_constraint(
            "ck_behavioral_batches_timezone_offset",
            "behavioral_batches",
            type_="check",
        )
    op.drop_column("behavioral_batches", "collector_error_count")
    op.drop_column("behavioral_batches", "dropped_event_count")
    op.drop_column("behavioral_batches", "client_timezone_offset_minutes")
    op.drop_column("behavioral_batches", "visibility_state")

    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint("ck_facial_captures_source", "facial_captures", type_="check")
        op.drop_constraint(
            "ck_facial_captures_timezone_offset", "facial_captures", type_="check"
        )
    op.drop_column("facial_captures", "camera_facing_mode")
    op.drop_column("facial_captures", "capture_source")
    op.drop_column("facial_captures", "client_timezone_offset_minutes")

    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(
            "ck_experimental_sessions_timezone_offset",
            "experimental_sessions",
            type_="check",
        )
        op.drop_constraint(
            "ck_experimental_sessions_attack_type",
            "experimental_sessions",
            type_="check",
        )
        op.drop_constraint(
            "ck_experimental_sessions_presentation_label",
            "experimental_sessions",
            type_="check",
        )
        op.drop_constraint(
            "ck_experimental_sessions_annotation_status",
            "experimental_sessions",
            type_="check",
        )
        op.drop_constraint(
            "ck_experimental_sessions_sample_role",
            "experimental_sessions",
            type_="check",
        )
        op.drop_constraint(
            "ck_experimental_sessions_identity_label",
            "experimental_sessions",
            type_="check",
        )
    op.drop_index("ix_experimental_sessions_annotated_by", table_name="experimental_sessions")
    op.drop_index(
        "ix_experimental_sessions_annotation_status", table_name="experimental_sessions"
    )
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(
            "fk_experimental_sessions_annotated_by_users",
            "experimental_sessions",
            type_="foreignkey",
        )
    for column in (
        "screen_pixel_ratio",
        "client_language",
        "client_timezone_offset_minutes",
        "max_image_size_bytes",
        "max_batch_events",
        "batch_interval_seconds",
        "capture_interval_seconds",
        "annotation_notes",
        "annotated_at",
        "annotated_by",
        "annotation_status",
        "pad_source_id",
        "source_device",
        "attack_type",
        "presentation_label",
        "operator_change_at",
        "sample_role",
        "identity_label",
        "collector_version",
        "protocol_version",
    ):
        op.drop_column("experimental_sessions", column)
