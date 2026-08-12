"""Merge Phase 044 ledger and the deployed driver-schema repair branch.

Revision ID: gh440210044mg
Revises: gg440110044dc, ad390210039dr
Create Date: 2026-08-10 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

revision: str = "gh440210044mg"
down_revision: Union[str, Sequence[str], None] = (
    "gg440110044dc",
    "ad390210039dr",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge-only revision; both parent branches retain their operations."""


def downgrade() -> None:
    """Downgrading the merge exposes both parent heads again."""
