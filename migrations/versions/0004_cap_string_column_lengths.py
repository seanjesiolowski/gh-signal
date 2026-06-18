"""cap string column lengths

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-18

Bounds the previously unbounded String columns at 255 chars so a malformed
GitHub payload can't insert oversized rows.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLUMNS = (
    ("events", "id"),
    ("events", "type"),
    ("events", "actor"),
    ("events", "repo"),
    ("repos", "name"),
    ("repos", "language"),
)


def upgrade() -> None:
    for table, column in _COLUMNS:
        op.alter_column(table, column, type_=sa.String(255), existing_type=sa.String())


def downgrade() -> None:
    for table, column in _COLUMNS:
        op.alter_column(table, column, type_=sa.String(), existing_type=sa.String(255))
