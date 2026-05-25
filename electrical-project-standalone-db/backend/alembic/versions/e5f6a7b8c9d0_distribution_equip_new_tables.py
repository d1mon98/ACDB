"""distribution equipment: add bus_ducts, meters, capacitor_banks, pdus tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

_COMMON = [
    sa.Column("id",               sa.Integer,     primary_key=True),
    sa.Column("catalog_group_id", sa.Integer,     sa.ForeignKey("catalog_groups.id", ondelete="SET NULL"), nullable=True),
    sa.Column("code",             sa.String(60),  nullable=False),
    sa.Column("name",             sa.String(200), nullable=False),
    sa.Column("description",      sa.Text,        nullable=True),
    sa.Column("is_active",        sa.Boolean,     nullable=False, server_default="1"),
    sa.Column("notes",            sa.Text,        nullable=True),
    sa.Column("created_at",       sa.DateTime,    nullable=False),
    sa.Column("updated_at",       sa.DateTime,    nullable=False),
]


def upgrade() -> None:
    op.create_table(
        "cat_bus_ducts",
        *_COMMON,
        sa.Column("rated_voltage", sa.String(40), nullable=True),
        sa.Column("rated_current", sa.Integer,    nullable=True),
        sa.Column("phases",        sa.Integer,    nullable=True),
        sa.Column("bus_type",      sa.String(40), nullable=True),
    )
    op.create_table(
        "cat_meters",
        *_COMMON,
        sa.Column("meter_class",      sa.String(40), nullable=True),
        sa.Column("measurement_type", sa.String(60), nullable=True),
        sa.Column("accuracy_class",   sa.String(20), nullable=True),
        sa.Column("voltage_rating",   sa.String(40), nullable=True),
    )
    op.create_table(
        "cat_capacitor_banks",
        *_COMMON,
        sa.Column("voltage_rating",  sa.String(40), nullable=True),
        sa.Column("kvar_rating",     sa.Float,      nullable=True),
        sa.Column("phases",          sa.Integer,    nullable=True),
        sa.Column("connection_type", sa.String(20), nullable=True),
    )
    op.create_table(
        "cat_pdus",
        *_COMMON,
        sa.Column("input_voltage",  sa.String(40), nullable=True),
        sa.Column("output_voltage", sa.String(40), nullable=True),
        sa.Column("capacity_kva",   sa.Float,      nullable=True),
        sa.Column("outlet_type",    sa.String(60), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("cat_pdus")
    op.drop_table("cat_capacitor_banks")
    op.drop_table("cat_meters")
    op.drop_table("cat_bus_ducts")
