"""Align legacy warehouse address columns with the Phase 022 contract.

Revision ID: u310110030dc
Revises: t310110029dc
Create Date: 2026-07-28 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "u310110030dc"
down_revision: Union[str, None] = "t310110029dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 022 accepts either free-form address fields, an address_id, or no
    # address while a warehouse is still being configured.  The legacy table
    # predated that workflow and incorrectly kept these columns NOT NULL.
    with op.batch_alter_table("warehouses") as batch_op:
        batch_op.alter_column(
            "address", existing_type=sa.String(255), nullable=True
        )
        batch_op.alter_column(
            "district", existing_type=sa.String(100), nullable=True
        )
        batch_op.alter_column(
            "province", existing_type=sa.String(100), nullable=True
        )
        batch_op.alter_column(
            "department", existing_type=sa.String(100), nullable=True
        )


def downgrade() -> None:
    # A safe downgrade requires values for rows created under the optional
    # contract before restoring the original NOT NULL constraints.
    op.execute(
        """
        UPDATE warehouses
        SET address = COALESCE(address, ''),
            district = COALESCE(district, ''),
            province = COALESCE(province, ''),
            department = COALESCE(department, '')
        """
    )
    with op.batch_alter_table("warehouses") as batch_op:
        batch_op.alter_column(
            "department", existing_type=sa.String(100), nullable=False
        )
        batch_op.alter_column(
            "province", existing_type=sa.String(100), nullable=False
        )
        batch_op.alter_column(
            "district", existing_type=sa.String(100), nullable=False
        )
        batch_op.alter_column(
            "address", existing_type=sa.String(255), nullable=False
        )
