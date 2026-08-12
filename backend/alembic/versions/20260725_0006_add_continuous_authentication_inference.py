"""Add continuous authentication inference persistence.

Revision ID: 20260725_0006
Revises: 20260725_0005
Create Date: 2026-07-25 23:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260725_0006"
down_revision: str | None = "20260725_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("last_risk_action", sa.String(length=60), nullable=True),
    )
    op.add_column(
        "sessions",
        sa.Column(
            "continuous_auth_status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_sessions_continuous_auth_status",
        "sessions",
        "continuous_auth_status IN "
        "('pending', 'active', 'degraded', 'verification_required', "
        "'restricted', 'terminated')",
    )
    op.create_table(
        "continuous_auth_evaluations",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "experimental_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "experimental_sessions.id", ondelete="SET NULL"
            ),
        ),
        sa.Column(
            "participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "research_participants.id", ondelete="SET NULL"
            ),
        ),
        sa.Column(
            "facial_capture_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("facial_captures.id", ondelete="SET NULL"),
        ),
        sa.Column("behavioral_window_id", sa.String(length=100)),
        sa.Column("facial_available", sa.Boolean(), nullable=False),
        sa.Column("pad_available", sa.Boolean(), nullable=False),
        sa.Column("behavioral_available", sa.Boolean(), nullable=False),
        sa.Column("facial_score", sa.Numeric(20, 10)),
        sa.Column("pad_score", sa.Numeric(20, 10)),
        sa.Column("behavioral_score", sa.Numeric(20, 10)),
        sa.Column("facial_risk", sa.Numeric(6, 5)),
        sa.Column("pad_risk", sa.Numeric(6, 5)),
        sa.Column("behavioral_risk", sa.Numeric(6, 5)),
        sa.Column("combined_risk", sa.Numeric(6, 5), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column(
            "authentication_level", sa.String(length=50), nullable=False
        ),
        sa.Column(
            "recommended_action", sa.String(length=60), nullable=False
        ),
        sa.Column("applied_action", sa.String(length=60), nullable=False),
        sa.Column(
            "model_versions", postgresql.JSONB(), nullable=False
        ),
        sa.Column("latency_ms", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "latency_breakdown", postgresql.JSONB(), nullable=False
        ),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "combined_risk >= 0 AND combined_risk <= 1",
            name="ck_continuous_auth_evaluations_combined_risk",
        ),
        sa.CheckConstraint(
            "facial_risk IS NULL OR "
            "(facial_risk >= 0 AND facial_risk <= 1)",
            name="ck_continuous_auth_evaluations_facial_risk",
        ),
        sa.CheckConstraint(
            "pad_risk IS NULL OR (pad_risk >= 0 AND pad_risk <= 1)",
            name="ck_continuous_auth_evaluations_pad_risk",
        ),
        sa.CheckConstraint(
            "behavioral_risk IS NULL OR "
            "(behavioral_risk >= 0 AND behavioral_risk <= 1)",
            name="ck_continuous_auth_evaluations_behavioral_risk",
        ),
        sa.CheckConstraint(
            "latency_ms >= 0",
            name="ck_continuous_auth_evaluations_latency",
        ),
        sa.CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="ck_continuous_auth_evaluations_risk_level",
        ),
        sa.CheckConstraint(
            "authentication_level IN "
            "('traditional', 'continuously_verified', "
            "'verification_required', 'restricted', 'terminated')",
            name="ck_continuous_auth_evaluations_authentication_level",
        ),
    )
    for column in (
        "user_id",
        "session_id",
        "experimental_session_id",
        "participant_id",
        "facial_capture_id",
        "risk_level",
        "authentication_level",
        "evaluated_at",
    ):
        op.create_index(
            f"ix_continuous_auth_evaluations_{column}",
            "continuous_auth_evaluations",
            [column],
        )
    op.create_index(
        "ix_continuous_auth_evaluations_session_evaluated",
        "continuous_auth_evaluations",
        ["session_id", "evaluated_at"],
    )
    op.create_index(
        "ix_continuous_auth_evaluations_user_evaluated",
        "continuous_auth_evaluations",
        ["user_id", "evaluated_at"],
    )
    op.create_table(
        "risk_events",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True
        ),
        sa.Column(
            "continuous_auth_evaluation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "continuous_auth_evaluations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("previous_risk_level", sa.String(length=20)),
        sa.Column("new_risk_level", sa.String(length=20), nullable=False),
        sa.Column(
            "recommended_action", sa.String(length=60), nullable=False
        ),
        sa.Column("applied_action", sa.String(length=60), nullable=False),
        sa.Column("reason_code", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "previous_risk_level IS NULL OR previous_risk_level IN "
            "('low', 'medium', 'high', 'critical')",
            name="ck_risk_events_previous_level",
        ),
        sa.CheckConstraint(
            "new_risk_level IN ('low', 'medium', 'high', 'critical')",
            name="ck_risk_events_new_level",
        ),
    )
    for column in (
        "continuous_auth_evaluation_id",
        "user_id",
        "session_id",
        "created_at",
    ):
        op.create_index(
            f"ix_risk_events_{column}", "risk_events", [column]
        )
    op.create_index(
        "ix_risk_events_session_created",
        "risk_events",
        ["session_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("risk_events")
    op.drop_table("continuous_auth_evaluations")
    op.drop_constraint(
        "ck_sessions_continuous_auth_status",
        "sessions",
        type_="check",
    )
    op.drop_column("sessions", "continuous_auth_status")
    op.drop_column("sessions", "last_risk_action")
