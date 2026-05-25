"""power_systems: add wires, system_config, voltage_class columns

Revision ID: d4e5f6a7b8c9
Revises: c7d2e3f4a5b6
Create Date: 2026-05-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c7d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("cat_power_systems") as batch_op:
        batch_op.add_column(sa.Column("wires",         sa.Integer(),    nullable=True))
        batch_op.add_column(sa.Column("system_config", sa.String(40),   nullable=True))
        batch_op.add_column(sa.Column("voltage_class", sa.String(40),   nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("cat_power_systems") as batch_op:
        batch_op.drop_column("voltage_class")
        batch_op.drop_column("system_config")
        batch_op.drop_column("wires")
