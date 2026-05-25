"""add catalog_column_defs and catalog_custom_rows tables

Revision ID: c7d2e3f4a5b6
Revises: af7e43fe52d7
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c7d2e3f4a5b6"
down_revision = "af7e43fe52d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_column_defs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "catalog_group_id",
            sa.Integer,
            sa.ForeignKey("catalog_groups.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("col_name", sa.String(100), nullable=False),
        sa.Column("col_label", sa.String(200), nullable=False),
        sa.Column("col_type", sa.String(20), nullable=False, server_default="text"),
        sa.Column("required", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "catalog_custom_rows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "catalog_group_id",
            sa.Integer,
            sa.ForeignKey("catalog_groups.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("row_data", sa.Text, nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("catalog_custom_rows")
    op.drop_table("catalog_column_defs")
