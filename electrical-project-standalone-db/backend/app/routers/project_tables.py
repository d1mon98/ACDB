"""REST routers for the Class B project tables (excluding ``projects`` itself).

The ``projects`` registry has its own hand-written router (cascade delete,
dashboard, full-export endpoints) -- see ``routers/projects.py``.

The five catalog-linked tables also receive ``/merged`` routes; because the
catalog now lives in a separate database, those routes do a cross-DB lookup
via :func:`make_crud_router`'s ``catalog_model`` / ``catalog_id_field`` /
``catalog_read_schema`` parameters.
"""

from ..database import get_project_db
from ..models.catalogs import (
    CatalogCable,
    CatalogDevice,
    CatalogEquipment,
    CatalogInstrument,
    CatalogIOModule,
)
from ..models.projects import (
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
from ..schemas import catalogs as cs
from ..schemas import projects as s
from .factory import make_crud_router


def _proj(**kw):
    """Helper -- every project-table router uses the project DB."""
    kw.setdefault("db_dep", get_project_db)
    return make_crud_router(**kw)


routers = [
    _proj(
        model=ProjectLocation,
        prefix="/api/project-locations",
        label="Project location",
        create_schema=s.LocationCreate,
        read_schema=s.LocationRead,
        update_schema=s.LocationUpdate,
    ),
    _proj(
        model=ProjectFeeder,
        prefix="/api/project-feeders",
        label="Feeder",
        create_schema=s.FeederCreate,
        read_schema=s.FeederRead,
        update_schema=s.FeederUpdate,
    ),
    _proj(
        model=ProjectEquipment,
        prefix="/api/project-equipment",
        label="Project equipment",
        create_schema=s.ProjectEquipmentCreate,
        read_schema=s.ProjectEquipmentRead,
        update_schema=s.ProjectEquipmentUpdate,
        merged_schema=s.ProjectEquipmentMerged,
        catalog_model=CatalogEquipment,
        catalog_id_field="catalog_equipment_id",
        catalog_read_schema=cs.EquipmentRead,
    ),
    _proj(
        model=ProjectPanelCircuit,
        prefix="/api/project-panel-circuits",
        label="Panel circuit",
        create_schema=s.PanelCircuitCreate,
        read_schema=s.PanelCircuitRead,
        update_schema=s.PanelCircuitUpdate,
    ),
    _proj(
        model=ProjectCable,
        prefix="/api/project-cables",
        label="Project cable",
        create_schema=s.ProjectCableCreate,
        read_schema=s.ProjectCableRead,
        update_schema=s.ProjectCableUpdate,
        merged_schema=s.ProjectCableMerged,
        catalog_model=CatalogCable,
        catalog_id_field="catalog_cable_id",
        catalog_read_schema=cs.CableRead,
    ),
    _proj(
        model=ProjectCableRoute,
        prefix="/api/project-cable-routes",
        label="Cable route",
        create_schema=s.CableRouteCreate,
        read_schema=s.CableRouteRead,
        update_schema=s.CableRouteUpdate,
    ),
    _proj(
        model=ProjectConduit,
        prefix="/api/project-conduits",
        label="Conduit / tray",
        create_schema=s.ConduitCreate,
        read_schema=s.ConduitRead,
        update_schema=s.ConduitUpdate,
    ),
    _proj(
        model=ProjectInstrument,
        prefix="/api/project-instruments",
        label="Project instrument",
        create_schema=s.ProjectInstrumentCreate,
        read_schema=s.ProjectInstrumentRead,
        update_schema=s.ProjectInstrumentUpdate,
        merged_schema=s.ProjectInstrumentMerged,
        catalog_model=CatalogInstrument,
        catalog_id_field="catalog_instrument_id",
        catalog_read_schema=cs.InstrumentRead,
    ),
    _proj(
        model=ProjectIOPoint,
        prefix="/api/project-io-list",
        label="I/O point",
        create_schema=s.IOPointCreate,
        read_schema=s.IOPointRead,
        update_schema=s.IOPointUpdate,
        merged_schema=s.IOPointMerged,
        catalog_model=CatalogIOModule,
        catalog_id_field="catalog_io_module_id",
        catalog_read_schema=cs.IOModuleRead,
    ),
    _proj(
        model=ProjectTerminalBlock,
        prefix="/api/project-terminal-blocks",
        label="Terminal block",
        create_schema=s.TerminalBlockCreate,
        read_schema=s.TerminalBlockRead,
        update_schema=s.TerminalBlockUpdate,
    ),
    _proj(
        model=ProjectTermination,
        prefix="/api/project-terminations",
        label="Termination",
        create_schema=s.TerminationCreate,
        read_schema=s.TerminationRead,
        update_schema=s.TerminationUpdate,
    ),
    _proj(
        model=ProjectControlPanel,
        prefix="/api/project-control-panels",
        label="Control panel",
        create_schema=s.ControlPanelCreate,
        read_schema=s.ControlPanelRead,
        update_schema=s.ControlPanelUpdate,
    ),
    _proj(
        model=ProjectPanelComponent,
        prefix="/api/project-panel-components",
        label="Panel component",
        create_schema=s.PanelComponentCreate,
        read_schema=s.PanelComponentRead,
        update_schema=s.PanelComponentUpdate,
        merged_schema=s.PanelComponentMerged,
        catalog_model=CatalogDevice,
        catalog_id_field="catalog_device_id",
        catalog_read_schema=cs.DeviceRead,
    ),
    _proj(
        model=ProjectNetworkDevice,
        prefix="/api/project-network-devices",
        label="Network device",
        create_schema=s.NetworkDeviceCreate,
        read_schema=s.NetworkDeviceRead,
        update_schema=s.NetworkDeviceUpdate,
    ),
    _proj(
        model=ProjectDrawing,
        prefix="/api/project-drawings",
        label="Drawing",
        create_schema=s.DrawingCreate,
        read_schema=s.DrawingRead,
        update_schema=s.DrawingUpdate,
    ),
    _proj(
        model=ProjectCalculation,
        prefix="/api/project-calculations",
        label="Calculation",
        create_schema=s.CalculationCreate,
        read_schema=s.CalculationRead,
        update_schema=s.CalculationUpdate,
    ),
    _proj(
        model=ProjectQAQCCheck,
        prefix="/api/project-qaqc-checks",
        label="QA/QC check",
        create_schema=s.QAQCCheckCreate,
        read_schema=s.QAQCCheckRead,
        update_schema=s.QAQCCheckUpdate,
    ),
]
