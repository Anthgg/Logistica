"""Phase 039 inbound receiving by scanning.

Revision ID: ac390110039dc
Revises: ab380110038dc
Deployment remains an explicit operational action; the migration itself is safe
to apply through the normal Alembic chain.
"""
from typing import Sequence, Union

from alembic import op

from app.database.base import Base
from app.models import registry as _registry  # noqa: F401
from app.modules.logistics.inbound.receiving.infrastructure.persistence.models import PHASE_039_TABLES

revision: str = "ac390110039dc"
down_revision: Union[str, Sequence[str], None] = "ab380110038dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    for table_name in PHASE_039_TABLES:
        Base.metadata.tables[table_name].create(bind=bind, checkfirst=False)


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in reversed(PHASE_039_TABLES):
        Base.metadata.tables[table_name].drop(bind=bind, checkfirst=False)
