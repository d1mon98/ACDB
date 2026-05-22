"""Initial schema — all CLASS A and CLASS B tables.

Revision ID: 0001
Revises:
Create Date: 2026-05-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- CLASS A ---
    op.create_table(
        "equip_catalog",
        sa.Column("equip_catalog_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("manufacturer", sa.String(100)),
        sa.Column("model", sa.String(100)),
        sa.Column("description", sa.String(255)),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("voltage_rating_v", sa.Integer),
        sa.Column("current_rating_a", sa.Float),
        sa.Column("ic_rating_ka", sa.Float),
        sa.Column("interrupting_type", sa.String(50)),
        sa.Column("enclosure_nema", sa.String(20)),
        sa.Column("weight_lbs", sa.Float),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "cable_catalog",
        sa.Column("cable_catalog_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("manufacturer", sa.String(100)),
        sa.Column("trade_name", sa.String(100)),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("conductor_material", sa.String(10), nullable=False),
        sa.Column("insulation", sa.String(20), nullable=False),
        sa.Column("voltage_rating_v", sa.Integer),
        sa.Column("num_conductors", sa.Integer),
        sa.Column("awg_kcmil", sa.String(20)),
        sa.Column("shield", sa.Boolean, default=False),
        sa.Column("armor", sa.Boolean, default=False),
        sa.Column("ampacity_conduit_a", sa.Float),
        sa.Column("ampacity_tray_a", sa.Float),
        sa.Column("od_inches", sa.Float),
        sa.Column("weight_lbft", sa.Float),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "instrument_catalog",
        sa.Column("instrument_catalog_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("manufacturer", sa.String(100)),
        sa.Column("model", sa.String(100)),
        sa.Column("description", sa.String(255)),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("signal_type", sa.String(20)),
        sa.Column("supply_vdc", sa.Float),
        sa.Column("enclosure_nema", sa.String(20)),
        sa.Column("hazardous_area_rating", sa.String(50)),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "conduit_catalog",
        sa.Column("conduit_catalog_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("trade_size_in", sa.Float),
        sa.Column("od_inches", sa.Float),
        sa.Column("id_inches", sa.Float),
        sa.Column("notes", sa.Text),
    )

    # --- CLASS B ---
    op.create_table(
        "projects",
        sa.Column("project_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_number", sa.String(50), unique=True, nullable=False),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("client", sa.String(255)),
        sa.Column("location", sa.String(255)),
        sa.Column("engineer_of_record", sa.String(100)),
        sa.Column("issue_date", sa.Date),
        sa.Column("nec_edition", sa.String(10)),
        sa.Column("voltage_system", sa.String(20)),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "locations",
        sa.Column("location_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("location_tag", sa.String(50), nullable=False),
        sa.Column("building", sa.String(100)),
        sa.Column("room", sa.String(100)),
        sa.Column("elevation_ft", sa.Float),
        sa.Column("area_classification", sa.String(30), default="ORDINARY"),
        sa.Column("nfpa_classification", sa.String(50)),
        sa.Column("description", sa.String(255)),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "equipment",
        sa.Column("equip_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("equip_catalog_id", sa.Integer, sa.ForeignKey("equip_catalog.equip_catalog_id")),
        sa.Column("tag", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("location_id", sa.Integer, sa.ForeignKey("locations.location_id")),
        sa.Column("bus_voltage_v", sa.Integer),
        sa.Column("rated_current_a", sa.Float),
        sa.Column("ic_rating_ka", sa.Float),
        sa.Column("fed_from_tag", sa.String(50)),
        sa.Column("breaker_trip_a", sa.Float),
        sa.Column("breaker_frame_a", sa.Float),
        sa.Column("drawing_ref", sa.String(100)),
        sa.Column("sheet_number", sa.String(50)),
        sa.Column("one_line_ref", sa.String(100)),
        sa.Column("status", sa.String(20), default="DESIGN"),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "instruments",
        sa.Column("instrument_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("instrument_catalog_id", sa.Integer, sa.ForeignKey("instrument_catalog.instrument_catalog_id")),
        sa.Column("tag", sa.String(50), nullable=False),
        sa.Column("service_description", sa.String(255)),
        sa.Column("location_id", sa.Integer, sa.ForeignKey("locations.location_id")),
        sa.Column("loop_number", sa.String(50)),
        sa.Column("p_and_id_ref", sa.String(100)),
        sa.Column("panel_tag", sa.String(50)),
        sa.Column("signal_type", sa.String(20)),
        sa.Column("supply_source_tag", sa.String(50)),
        sa.Column("drawing_ref", sa.String(100)),
        sa.Column("sheet_number", sa.String(50)),
        sa.Column("status", sa.String(20), default="DESIGN"),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "cables",
        sa.Column("cable_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("cable_catalog_id", sa.Integer, sa.ForeignKey("cable_catalog.cable_catalog_id")),
        sa.Column("cable_tag", sa.String(50), nullable=False),
        sa.Column("service_description", sa.String(255)),
        sa.Column("from_equipment_id", sa.Integer, sa.ForeignKey("equipment.equip_id"), nullable=True),
        sa.Column("from_instrument_id", sa.Integer, sa.ForeignKey("instruments.instrument_id"), nullable=True),
        sa.Column("from_terminal", sa.String(50)),
        sa.Column("to_equipment_id", sa.Integer, sa.ForeignKey("equipment.equip_id"), nullable=True),
        sa.Column("to_instrument_id", sa.Integer, sa.ForeignKey("instruments.instrument_id"), nullable=True),
        sa.Column("to_terminal", sa.String(50)),
        sa.Column("from_location_id", sa.Integer, sa.ForeignKey("locations.location_id")),
        sa.Column("to_location_id", sa.Integer, sa.ForeignKey("locations.location_id")),
        sa.Column("conduit_tag", sa.String(50)),
        sa.Column("routing_description", sa.Text),
        sa.Column("length_ft", sa.Float),
        sa.Column("length_ft_actual", sa.Float),
        sa.Column("num_conductors_used", sa.Integer),
        sa.Column("conductor_size_awg_kcmil", sa.String(20)),
        sa.Column("voltage_drop_pct", sa.Float),
        sa.Column("drawing_ref", sa.String(100)),
        sa.Column("sheet_number", sa.String(50)),
        sa.Column("status", sa.String(20), default="DESIGN"),
        sa.Column("notes", sa.Text),
        sa.CheckConstraint(
            "(from_equipment_id IS NOT NULL) != (from_instrument_id IS NOT NULL)",
            name="ck_cables_from_endpoint",
        ),
        sa.CheckConstraint(
            "(to_equipment_id IS NOT NULL) != (to_instrument_id IS NOT NULL)",
            name="ck_cables_to_endpoint",
        ),
    )
    op.create_table(
        "conduits",
        sa.Column("conduit_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("conduit_catalog_id", sa.Integer, sa.ForeignKey("conduit_catalog.conduit_catalog_id")),
        sa.Column("conduit_tag", sa.String(50), nullable=False),
        sa.Column("from_location_id", sa.Integer, sa.ForeignKey("locations.location_id")),
        sa.Column("to_location_id", sa.Integer, sa.ForeignKey("locations.location_id")),
        sa.Column("length_ft", sa.Float),
        sa.Column("fill_pct", sa.Float),
        sa.Column("routing_description", sa.Text),
        sa.Column("drawing_ref", sa.String(100)),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "panel_schedules",
        sa.Column("schedule_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.project_id"), nullable=False),
        sa.Column("panel_equip_id", sa.Integer, sa.ForeignKey("equipment.equip_id"), nullable=False),
        sa.Column("circuit_number", sa.String(10), nullable=False),
        sa.Column("phase", sa.String(10)),
        sa.Column("breaker_trip_a", sa.Float),
        sa.Column("breaker_poles", sa.Integer),
        sa.Column("load_equip_id", sa.Integer, sa.ForeignKey("equipment.equip_id"), nullable=True),
        sa.Column("load_instrument_id", sa.Integer, sa.ForeignKey("instruments.instrument_id"), nullable=True),
        sa.Column("load_description", sa.String(255)),
        sa.Column("load_kva", sa.Float),
        sa.Column("load_kw", sa.Float),
        sa.Column("load_pf", sa.Float),
        sa.Column("notes", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("panel_schedules")
    op.drop_table("conduits")
    op.drop_table("cables")
    op.drop_table("instruments")
    op.drop_table("equipment")
    op.drop_table("locations")
    op.drop_table("projects")
    op.drop_table("conduit_catalog")
    op.drop_table("instrument_catalog")
    op.drop_table("cable_catalog")
    op.drop_table("equip_catalog")
