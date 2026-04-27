"""initial: events table

Revision ID: 0001
Revises:
Create Date: 2026-04-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("repo", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_id", "events", ["id"])
    op.create_index("ix_events_type", "events", ["type"])
    op.create_index("ix_events_actor", "events", ["actor"])
    op.create_index("ix_events_repo", "events", ["repo"])


def downgrade() -> None:
    op.drop_index("ix_events_repo", table_name="events")
    op.drop_index("ix_events_actor", table_name="events")
    op.drop_index("ix_events_type", table_name="events")
    op.drop_index("ix_events_id", table_name="events")
    op.drop_table("events")
