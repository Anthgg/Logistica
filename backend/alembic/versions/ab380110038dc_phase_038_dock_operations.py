"""Phase 038 dock assignment and unloading execution schema.

Revision ID: ab380110038dc
Revises: aa370110037dc
Create Date: 2026-08-01

The ordered table manifest is intentionally explicit.  Column, constraint and
index definitions are sourced from the Phase 038 ORM metadata so the migration
and runtime model cannot silently disagree in this delivery.
"""

from typing import Sequence, Union

from alembic import op

from app.database.base import Base
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence import models as _phase_038_models  # noqa: F401
from app.modules.logistics.warehouses import models as _warehouse_models  # noqa: F401


revision: str = "ab380110038dc"
down_revision: Union[str, Sequence[str], None] = "aa370110037dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PHASE_038_TABLES = (
    "warehouse_docks",
    "warehouse_dock_capabilities",
    "warehouse_dock_operating_windows",
    "warehouse_dock_blackouts",
    "inbound_dock_queue_entries",
    "dock_assignment_plans",
    "inbound_dock_assignments",
    "dock_occupancy_intervals",
    "unloading_operations",
    "unloading_readiness_check_definitions",
    "unloading_readiness_check_results",
    "unloading_completion_check_definitions",
    "unloading_completion_check_results",
    "unloading_responsible_assignments",
    "unloading_equipment_assignments",
    "unloading_seal_opening_events",
    "unloading_pauses",
    "dock_operational_events",
    "dock_operational_time_corrections",
    "dock_operation_metrics_projection",
    "dock_operation_export_jobs",
)


def upgrade() -> None:
    bind = op.get_bind()
    for table_name in PHASE_038_TABLES:
        Base.metadata.tables[table_name].create(bind=bind, checkfirst=False)


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in reversed(PHASE_038_TABLES):
        Base.metadata.tables[table_name].drop(bind=bind, checkfirst=False)
