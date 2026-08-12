"""Enforce consistency of controlled research annotations.

Revision ID: 20260725_0004
Revises: 20260725_0003
Create Date: 2026-07-25 21:50:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260725_0004"
down_revision: str | None = "20260725_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_experimental_sessions_pad_consistency",
        "experimental_sessions",
        "(presentation_label IS NULL AND attack_type IS NULL) OR "
        "(presentation_label = 'bona_fide' AND attack_type = 'none') OR "
        "(presentation_label = 'attack' AND attack_type IN "
        "('printed_photo', 'screen_photo', 'replayed_video'))",
    )
    op.create_check_constraint(
        "ck_experimental_sessions_operator_change_consistency",
        "experimental_sessions",
        "(sample_role = 'change_operator' AND operator_change_at IS NOT NULL) OR "
        "(sample_role <> 'change_operator' AND operator_change_at IS NULL)",
    )
    op.create_check_constraint(
        "ck_experimental_sessions_annotation_confirmation",
        "experimental_sessions",
        "annotation_status = 'pending' OR "
        "(annotated_by IS NOT NULL AND annotated_at IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_experimental_sessions_annotation_notes_length",
        "experimental_sessions",
        "annotation_notes IS NULL OR char_length(annotation_notes) <= 500",
    )


def downgrade() -> None:
    for name in (
        "ck_experimental_sessions_annotation_notes_length",
        "ck_experimental_sessions_annotation_confirmation",
        "ck_experimental_sessions_operator_change_consistency",
        "ck_experimental_sessions_pad_consistency",
    ):
        op.drop_constraint(name, "experimental_sessions", type_="check")
