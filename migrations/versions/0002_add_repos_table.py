"""add repos table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repos",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("topics", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_index("ix_repos_name", "repos", ["name"])
    op.create_index("ix_repos_language", "repos", ["language"])


def downgrade() -> None:
    op.drop_index("ix_repos_language", table_name="repos")
    op.drop_index("ix_repos_name", table_name="repos")
    op.drop_table("repos")
