"""add llm settings

Revision ID: 0003_llm_settings
Revises: 0002_app_data_records
Create Date: 2026-04-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import DATETIME as SQLiteDateTime

revision: str = "0003_llm_settings"
down_revision: Union[str, Sequence[str], None] = "0002_app_data_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DB_DATETIME = sa.DateTime().with_variant(
    SQLiteDateTime(storage_format="%(year)04d-%(month)02d-%(day)02d %(hour)02d:%(minute)02d:%(second)02d"),
    "sqlite",
)


def upgrade() -> None:
    op.create_table(
        "llm_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("created_at", DB_DATETIME, nullable=False),
        sa.Column("updated_at", DB_DATETIME, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("llm_settings")
