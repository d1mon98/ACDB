"""Request / response schemas for the Class B project tables.

Catalog-linked tables (equipment, cables, instruments, I/O points, panel
components) additionally define:

* a ``model_validator`` enforcing the merge rule on *create* -- a row must
  reference a catalog record OR supply the required local permanent field;
* an ``XMerged`` schema that nests the full catalog record alongside the project
  row -- the joined representation the UI renders.

The remaining project tables (feeders, cable routes, conduits, terminal blocks,
terminations, network devices, drawings, calculations, QA/QC checks) are plain
project tables with no catalog merge.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import model_validator

from ..models.enums import (
    AlarmPriority,
    CableEnd,
    CalcStatus,
    CalcType,
    ConductorMaterial,
    ConduitMaterial,
    ConduitType,
    DeviceCategory,
    DrawingStatus,
    DrawingType,
    EquipmentCategory,
    IndoorOutdoor,
    InstrumentType,
    IOType,
    IssueStage,
    NetworkDeviceType,
    NetworkProtocol,
    ProjectStatus,
    QAQCCategory,
    QAQCSeverity,
    QAQCStatus,
    RouteType,
    TerminationType,
    UL508AStatus,
)
from .catalogs import (
    CableRead,
    DeviceRead,
    EquipmentRead,
    InstrumentRead,
    IOModuleRead,
)
from .common import ORMModel, make_optional

# --------------------------------------------------------------------------
# projects
# --------------------------------------------------------------------------


class ProjectCreate(ORMModel):
    project_number: str
    name: str
    client: str | None = None
    facility: str | None = None
    location: str | None = None
    voltage_system: str | None = None
    issue_stage: IssueStage | None = None
    description: str | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    notes: str | None = None


class ProjectRead(ProjectCreate):
    id: int
    created_at: datetime
    updated_at: datetime


ProjectUpdate = make_optional(ProjectCreate, "ProjectUpdate")


# --------------------------------------------------------------------------
# project_locations
# --------------------------------------------------------------------------


class LocationCreate(ORMModel):
    project_id: int
    location_code: str
    description: str | None = None
    area_classification: str | None = None
    building: str | None = None
    room: str | None = None
    area: str | None = None
    process_system: str | None = None
    indoor_outdoor: IndoorOutdoor | None = None
    parent_location_id: int | None = None
    notes: str | None = None


class LocationRead(LocationCreate):
    id: int
    created_at: datetime
    updated_at: datetime


LocationUpdate = make_optional(LocationCreate, "LocationUpdate")


# --------------------------------------------------------------------------
# project_equipment  (catalog-linked: catalog_equipment)
# --------------------------------------------------------------------------


class ProjectEquipmentCreate(ORMModel):
    project_id: int
    catalog_equipment_id: int | None = None
    equipment_tag: str
    equipment_type: str | None = None
    location_id: int | None = None
    voltage: str | None = None
    phase: str | None = None
    hp_kw: str | None = None
    fla: float | None = None
    fed_from_id: int | None = None
    feeder_cable_id: int | None = None
    drawing_reference: str | None = None
    project_settings: str | None = None
    description: str | None = None
    # local permanent attributes (custom / one-off path)
    local_manufacturer: str | None = None
    local_category: EquipmentCategory | None = None
    local_model: str | None = None
    local_rated_voltage: str | None = None
    local_rated_current: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _check_merge(self) -> "ProjectEquipmentCreate":
        if self.catalog_equipment_id is None and not self.local_model:
            raise ValueError(
                "Provide a catalog equipment reference, or fill in the custom "
                "details (local_model is required for a one-off item)."
            )
        return self


class ProjectEquipmentRead(ProjectEquipmentCreate):
    id: int
    is_custom: bool
    created_at: datetime
    updated_at: datetime


class ProjectEquipmentMerged(ProjectEquipmentRead):
    """Project equipment row with its catalog record joined in."""

    catalog: EquipmentRead | None = None


ProjectEquipmentUpdate = make_optional(ProjectEquipmentCreate, "ProjectEquipmentUpdate")


# --------------------------------------------------------------------------
# project_panel_circuits  (no catalog link)
# --------------------------------------------------------------------------


class PanelCircuitCreate(ORMModel):
    project_id: int
    panel_id: int
    circuit_number: str
    load_description: str | None = None
    connected_load: float | None = None
    phases: str | None = None
    breaker_size: str | None = None
    cable_id: int | None = None
    destination_equipment_id: int | None = None
    notes: str | None = None


class PanelCircuitRead(PanelCircuitCreate):
    id: int
    created_at: datetime
    updated_at: datetime


PanelCircuitUpdate = make_optional(PanelCircuitCreate, "PanelCircuitUpdate")


# --------------------------------------------------------------------------
# project_cables  (catalog-linked: catalog_cables)
# --------------------------------------------------------------------------


class ProjectCableCreate(ORMModel):
    project_id: int
    catalog_cable_id: int | None = None
    cable_tag: str
    from_equipment_id: int | None = None
    to_equipment_id: int | None = None
    from_location_id: int | None = None
    to_location_id: int | None = None
    length: float | None = None
    routing: str | None = None
    route_id: int | None = None
    voltage_class: str | None = None
    drawing_reference: str | None = None
    description: str | None = None
    # local permanent attributes (custom / one-off path)
    local_cable_type_code: str | None = None
    local_conductor_material: ConductorMaterial | None = None
    local_conductor_size: str | None = None
    local_conductor_count: int | None = None
    local_insulation_type: str | None = None
    local_voltage_rating: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _check_merge(self) -> "ProjectCableCreate":
        if self.catalog_cable_id is None and not self.local_cable_type_code:
            raise ValueError(
                "Provide a catalog cable reference, or fill in the custom "
                "details (local_cable_type_code is required for a one-off item)."
            )
        return self


class ProjectCableRead(ProjectCableCreate):
    id: int
    is_custom: bool
    created_at: datetime
    updated_at: datetime


class ProjectCableMerged(ProjectCableRead):
    """Project cable row with its catalog record joined in."""

    catalog: CableRead | None = None


ProjectCableUpdate = make_optional(ProjectCableCreate, "ProjectCableUpdate")


# --------------------------------------------------------------------------
# project_instruments  (catalog-linked: catalog_instruments)
# --------------------------------------------------------------------------


class ProjectInstrumentCreate(ORMModel):
    project_id: int
    catalog_instrument_id: int | None = None
    instrument_tag: str
    location_id: int | None = None
    measured_variable: str | None = None
    pid_reference: str | None = None
    loop_number: str | None = None
    calibrated_range: str | None = None
    set_point: str | None = None
    power_source: str | None = None
    process_connection: str | None = None
    associated_equipment_id: int | None = None
    cable_id: int | None = None
    plc_panel_id: int | None = None
    description: str | None = None
    # local permanent attributes (custom / one-off path)
    local_manufacturer: str | None = None
    local_instrument_type: InstrumentType | None = None
    local_model: str | None = None
    local_signal_type: str | None = None
    local_accuracy: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _check_merge(self) -> "ProjectInstrumentCreate":
        if self.catalog_instrument_id is None and not self.local_model:
            raise ValueError(
                "Provide a catalog instrument reference, or fill in the custom "
                "details (local_model is required for a one-off item)."
            )
        return self


class ProjectInstrumentRead(ProjectInstrumentCreate):
    id: int
    is_custom: bool
    created_at: datetime
    updated_at: datetime


class ProjectInstrumentMerged(ProjectInstrumentRead):
    """Project instrument row with its catalog record joined in."""

    catalog: InstrumentRead | None = None


ProjectInstrumentUpdate = make_optional(
    ProjectInstrumentCreate, "ProjectInstrumentUpdate"
)


# --------------------------------------------------------------------------
# project_io_list  (catalog-linked: catalog_io_modules)
# --------------------------------------------------------------------------


class IOPointCreate(ORMModel):
    project_id: int
    catalog_io_module_id: int | None = None
    io_tag: str | None = None
    project_instrument_id: int | None = None
    project_panel_component_id: int | None = None
    io_type: IOType
    plc_panel_id: int | None = None
    rack: str | None = None
    slot: str | None = None
    channel: str | None = None
    plc_address: str | None = None
    signal_range: str | None = None
    fail_state: str | None = None
    alarm_priority: AlarmPriority | None = None
    scada_tag: str | None = None
    cable_id: int | None = None
    description: str | None = None
    # local permanent attribute (custom / one-off path)
    local_io_module_model: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _check_merge(self) -> "IOPointCreate":
        if self.catalog_io_module_id is None and not self.local_io_module_model:
            raise ValueError(
                "Provide a catalog I/O module reference, or fill in the custom "
                "details (local_io_module_model is required for a one-off item)."
            )
        return self


class IOPointRead(IOPointCreate):
    id: int
    is_custom: bool
    created_at: datetime
    updated_at: datetime


class IOPointMerged(IOPointRead):
    """I/O list row with its catalog module record joined in."""

    catalog: IOModuleRead | None = None


IOPointUpdate = make_optional(IOPointCreate, "IOPointUpdate")


# --------------------------------------------------------------------------
# project_control_panels  (no catalog link)
# --------------------------------------------------------------------------


class ControlPanelCreate(ORMModel):
    project_id: int
    panel_tag: str
    panel_type: str | None = None
    voltage: str | None = None
    enclosure_type: str | None = None
    sccr: str | None = None
    manufacturer: str | None = None
    ul508a_status: UL508AStatus | None = None
    location_id: int | None = None
    description: str | None = None
    notes: str | None = None


class ControlPanelRead(ControlPanelCreate):
    id: int
    created_at: datetime
    updated_at: datetime


ControlPanelUpdate = make_optional(ControlPanelCreate, "ControlPanelUpdate")


# --------------------------------------------------------------------------
# project_panel_components  (catalog-linked: catalog_devices)
# --------------------------------------------------------------------------


class PanelComponentCreate(ORMModel):
    project_id: int
    control_panel_id: int
    catalog_device_id: int | None = None
    component_tag: str | None = None
    component_type: str | None = None
    part_number: str | None = None
    voltage: str | None = None
    power_supply_source: str | None = None
    terminal_block_reference: str | None = None
    mounting_reference: str | None = None
    quantity: int = 1
    description: str | None = None
    # local permanent attributes (custom / one-off path)
    local_manufacturer: str | None = None
    local_device_category: DeviceCategory | None = None
    local_model: str | None = None
    local_ratings: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _check_merge(self) -> "PanelComponentCreate":
        if self.catalog_device_id is None and not self.local_model:
            raise ValueError(
                "Provide a catalog device reference, or fill in the custom "
                "details (local_model is required for a one-off item)."
            )
        return self


class PanelComponentRead(PanelComponentCreate):
    id: int
    is_custom: bool
    created_at: datetime
    updated_at: datetime


class PanelComponentMerged(PanelComponentRead):
    """Panel component row with its catalog device record joined in."""

    catalog: DeviceRead | None = None


PanelComponentUpdate = make_optional(PanelComponentCreate, "PanelComponentUpdate")


# --------------------------------------------------------------------------
# project_feeders  (Power Distribution -- no catalog link)
# --------------------------------------------------------------------------


class FeederCreate(ORMModel):
    project_id: int
    feeder_tag: str
    source_equipment_id: int | None = None
    load_equipment_id: int | None = None
    voltage: str | None = None
    phases: str | None = None
    ampacity: str | None = None
    ocpd_type: str | None = None
    ocpd_rating: str | None = None
    feeder_cable_id: int | None = None
    drawing_reference: str | None = None
    description: str | None = None
    notes: str | None = None


class FeederRead(FeederCreate):
    id: int
    created_at: datetime
    updated_at: datetime


FeederUpdate = make_optional(FeederCreate, "FeederUpdate")


# --------------------------------------------------------------------------
# project_cable_routes  (no catalog link)
# --------------------------------------------------------------------------


class CableRouteCreate(ORMModel):
    project_id: int
    route_tag: str
    route_type: RouteType | None = None
    from_location_id: int | None = None
    to_location_id: int | None = None
    total_length: float | None = None
    description: str | None = None
    notes: str | None = None


class CableRouteRead(CableRouteCreate):
    id: int
    created_at: datetime
    updated_at: datetime


CableRouteUpdate = make_optional(CableRouteCreate, "CableRouteUpdate")


# --------------------------------------------------------------------------
# project_conduits  (Conduits / Trays -- no catalog link)
# --------------------------------------------------------------------------


class ConduitCreate(ORMModel):
    project_id: int
    conduit_tag: str
    conduit_type: ConduitType | None = None
    trade_size: str | None = None
    material: ConduitMaterial | None = None
    route_id: int | None = None
    from_location_id: int | None = None
    to_location_id: int | None = None
    length: float | None = None
    fill_percent: float | None = None
    description: str | None = None
    notes: str | None = None


class ConduitRead(ConduitCreate):
    id: int
    created_at: datetime
    updated_at: datetime


ConduitUpdate = make_optional(ConduitCreate, "ConduitUpdate")


# --------------------------------------------------------------------------
# project_terminal_blocks  (no catalog link)
# --------------------------------------------------------------------------


class TerminalBlockCreate(ORMModel):
    project_id: int
    control_panel_id: int | None = None
    terminal_strip: str
    terminal_number: str
    wire_number: str | None = None
    cable_id: int | None = None
    conductor_core: str | None = None
    device_tag: str | None = None
    signal_description: str | None = None
    description: str | None = None
    notes: str | None = None


class TerminalBlockRead(TerminalBlockCreate):
    id: int
    created_at: datetime
    updated_at: datetime


TerminalBlockUpdate = make_optional(TerminalBlockCreate, "TerminalBlockUpdate")


# --------------------------------------------------------------------------
# project_terminations  (no catalog link)
# --------------------------------------------------------------------------


class TerminationCreate(ORMModel):
    project_id: int
    cable_id: int
    cable_end: CableEnd | None = None
    conductor_core: str | None = None
    termination_type: TerminationType | None = None
    equipment_id: int | None = None
    terminal_block_id: int | None = None
    device_tag: str | None = None
    drawing_reference: str | None = None
    description: str | None = None
    notes: str | None = None


class TerminationRead(TerminationCreate):
    id: int
    created_at: datetime
    updated_at: datetime


TerminationUpdate = make_optional(TerminationCreate, "TerminationUpdate")


# --------------------------------------------------------------------------
# project_network_devices  (no catalog link)
# --------------------------------------------------------------------------


class NetworkDeviceCreate(ORMModel):
    project_id: int
    device_tag: str
    device_type: NetworkDeviceType | None = None
    manufacturer: str | None = None
    model: str | None = None
    ip_address: str | None = None
    subnet_mask: str | None = None
    protocol: NetworkProtocol | None = None
    port_count: int | None = None
    location_id: int | None = None
    control_panel_id: int | None = None
    description: str | None = None
    notes: str | None = None


class NetworkDeviceRead(NetworkDeviceCreate):
    id: int
    created_at: datetime
    updated_at: datetime


NetworkDeviceUpdate = make_optional(NetworkDeviceCreate, "NetworkDeviceUpdate")


# --------------------------------------------------------------------------
# project_drawings  (no catalog link)
# --------------------------------------------------------------------------


class DrawingCreate(ORMModel):
    project_id: int
    drawing_number: str
    title: str | None = None
    drawing_type: DrawingType | None = None
    revision: str | None = None
    status: DrawingStatus | None = None
    discipline: str | None = None
    sheet_size: str | None = None
    scale: str | None = None
    description: str | None = None
    notes: str | None = None


class DrawingRead(DrawingCreate):
    id: int
    created_at: datetime
    updated_at: datetime


DrawingUpdate = make_optional(DrawingCreate, "DrawingUpdate")


# --------------------------------------------------------------------------
# project_calculations  (no catalog link)
# --------------------------------------------------------------------------


class CalculationCreate(ORMModel):
    project_id: int
    calc_number: str
    title: str | None = None
    calc_type: CalcType | None = None
    revision: str | None = None
    status: CalcStatus | None = None
    result_summary: str | None = None
    performed_by: str | None = None
    description: str | None = None
    notes: str | None = None


class CalculationRead(CalculationCreate):
    id: int
    created_at: datetime
    updated_at: datetime


CalculationUpdate = make_optional(CalculationCreate, "CalculationUpdate")


# --------------------------------------------------------------------------
# project_qaqc_checks  (no catalog link)
# --------------------------------------------------------------------------


class QAQCCheckCreate(ORMModel):
    project_id: int
    check_item: str
    category: QAQCCategory | None = None
    severity: QAQCSeverity | None = None
    status: QAQCStatus = QAQCStatus.OPEN
    related_reference: str | None = None
    finding: str | None = None
    resolution: str | None = None
    checked_by: str | None = None
    description: str | None = None
    notes: str | None = None


class QAQCCheckRead(QAQCCheckCreate):
    id: int
    created_at: datetime
    updated_at: datetime


QAQCCheckUpdate = make_optional(QAQCCheckCreate, "QAQCCheckUpdate")
