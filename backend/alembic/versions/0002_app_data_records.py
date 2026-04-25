"""add app data records

Revision ID: 0002_app_data_records
Revises: 0001_initial_schema
Create Date: 2026-04-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_app_data_records"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_data_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("app_id", sa.String(length=36), nullable=False),
        sa.Column("collection", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["app_id"], ["apps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_app_data_records_app_collection_created",
        "app_data_records",
        ["app_id", "collection", "created_at"],
    )
    op.create_index(
        "ix_app_data_records_app_collection",
        "app_data_records",
        ["app_id", "collection"],
    )


def downgrade() -> None:
    op.drop_index("ix_app_data_records_app_collection", table_name="app_data_records")
    op.drop_index("ix_app_data_records_app_collection_created", table_name="app_data_records")
    op.drop_table("app_data_records")
