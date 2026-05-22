"""Table registry -- the single source of truth for the import subsystem.

Maps each table's URL slug to its ORM model, its create schema (used to
validate imported rows), and its *natural key* -- the human-readable column by
which the table is referenced (e.g. an equipment tag, a location code, a
catalog model number).  The Excel importer resolves foreign keys by these
natural keys rather than by raw id.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models.catalogs import (
    CatalogCable,
    CatalogDevice,
    CatalogEquipment,
    CatalogInstrument,
    CatalogIOModule,
    CatalogManufacturer,
)
from .models.projects import (
    Project,
    ProjectCable,
    ProjectCableRoute,
    ProjectCalculation,
    ProjectConduit,
    ProjectControlPanel,
    ProjectDrawing,
    ProjectEquipment,
    ProjectFeeder,
    ProjectInstrument,
    ProjectIOPoint,
    ProjectLocation,
    ProjectNetworkDevice,
    ProjectPanelCircuit,
    ProjectPanelComponent,
    ProjectQAQCCheck,
    ProjectTerminalBlock,
    ProjectTermination,
)
from .schemas import catalogs as cs
from .schemas import projects as ps


@dataclass(frozen=True)
class TableSpec:
    """Everything the import / pipeline subsystem needs to know about a table."""

    slug: str
    model: type
    create_schema: type
    natural_key: str  # human-readable key column
    label: str

    @property
    def table_name(self) -> str:
        return self.model.__tablename__

    @property
    def project_scoped(self) -> bool:
        return hasattr(self.model, "project_id")


TABLES: dict[str, TableSpec] = {
    # --- Class A catalogs ---
    "catalog-manufacturers": TableSpec(
        "catalog-manufacturers", CatalogManufacturer, cs.ManufacturerCreate,
        "name", "Manufacturers",
    ),
    "catalog-equipment": TableSpec(
        "catalog-equipment", CatalogEquipment, cs.EquipmentCreate,
        "model_series", "Equipment (catalog)",
    ),
    "catalog-cables": TableSpec(
        "catalog-cables", CatalogCable, cs.CableCreate,
        "cable_type_code", "Cables (catalog)",
    ),
    "catalog-instruments": TableSpec(
        "catalog-instruments", CatalogInstrument, cs.InstrumentCreate,
        "model_series", "Instruments (catalog)",
    ),
    "catalog-io-modules": TableSpec(
        "catalog-io-modules", CatalogIOModule, cs.IOModuleCreate,
        "module_model", "I/O Modules (catalog)",
    ),
    "catalog-devices": TableSpec(
        "catalog-devices", CatalogDevice, cs.DeviceCreate,
        "model", "Devices (catalog)",
    ),
    # --- Class B project tables ---
    "projects": TableSpec(
        "projects", Project, ps.ProjectCreate, "project_number", "Projects",
    ),
    "project-locations": TableSpec(
        "project-locations", ProjectLocation, ps.LocationCreate,
        "location_code", "Locations / Areas",
    ),
    "project-equipment": TableSpec(
        "project-equipment", ProjectEquipment, ps.ProjectEquipmentCreate,
        "equipment_tag", "Power Distribution Equipment",
    ),
    "project-panel-circuits": TableSpec(
        "project-panel-circuits", ProjectPanelCircuit, ps.PanelCircuitCreate,
        "circuit_number", "Panel Circuits",
    ),
    "project-feeders": TableSpec(
        "project-feeders", ProjectFeeder, ps.FeederCreate,
        "feeder_tag", "Power Distribution (feeders)",
    ),
    "project-cables": TableSpec(
        "project-cables", ProjectCable, ps.ProjectCableCreate,
        "cable_tag", "Cables",
    ),
    "project-cable-routes": TableSpec(
        "project-cable-routes", ProjectCableRoute, ps.CableRouteCreate,
        "route_tag", "Cable Routes",
    ),
    "project-conduits": TableSpec(
        "project-conduits", ProjectConduit, ps.ConduitCreate,
        "conduit_tag", "Conduits / Trays",
    ),
    "project-instruments": TableSpec(
        "project-instruments", ProjectInstrument, ps.ProjectInstrumentCreate,
        "instrument_tag", "Instruments",
    ),
    "project-io-list": TableSpec(
        "project-io-list", ProjectIOPoint, ps.IOPointCreate,
        "io_tag", "I/O List",
    ),
    "project-control-panels": TableSpec(
        "project-control-panels", ProjectControlPanel, ps.ControlPanelCreate,
        "panel_tag", "Control Panels",
    ),
    "project-panel-components": TableSpec(
        "project-panel-components", ProjectPanelComponent, ps.PanelComponentCreate,
        "component_tag", "Panel Components",
    ),
    "project-terminal-blocks": TableSpec(
        "project-terminal-blocks", ProjectTerminalBlock, ps.TerminalBlockCreate,
        "terminal_number", "Terminal Blocks",
    ),
    "project-terminations": TableSpec(
        "project-terminations", ProjectTermination, ps.TerminationCreate,
        "device_tag", "Terminations",
    ),
    "project-network-devices": TableSpec(
        "project-network-devices", ProjectNetworkDevice, ps.NetworkDeviceCreate,
        "device_tag", "Network Devices",
    ),
    "project-drawings": TableSpec(
        "project-drawings", ProjectDrawing, ps.DrawingCreate,
        "drawing_number", "Drawings",
    ),
    "project-calculations": TableSpec(
        "project-calculations", ProjectCalculation, ps.CalculationCreate,
        "calc_number", "Calculations",
    ),
    "project-qaqc-checks": TableSpec(
        "project-qaqc-checks", ProjectQAQCCheck, ps.QAQCCheckCreate,
        "check_item", "QA/QC Checks",
    ),
}

# Index by SQL table name, for resolving foreign-key targets.
_BY_TABLE_NAME: dict[str, TableSpec] = {spec.table_name: spec for spec in TABLES.values()}


def get_table(slug: str) -> TableSpec:
    """Return the spec for a slug, or raise KeyError."""
    if slug not in TABLES:
        raise KeyError(f"Unknown table: {slug}")
    return TABLES[slug]


def spec_for_table_name(table_name: str) -> TableSpec | None:
    """Return the spec for a SQL table name (used for FK-target lookups)."""
    return _BY_TABLE_NAME.get(table_name)


def fk_target_table_name(model: type, column_name: str) -> str | None:
    """Name of the table a column points at, or None if it is not a foreign key."""
    column = model.__table__.columns.get(column_name)
    if column is None:
        return None
    for fk in column.foreign_keys:
        return fk.column.table.name
    return None
