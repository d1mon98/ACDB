"""Class B -- Project tables.

Project tables hold the actual equipment, tags, locations and connections of one
specific project.  Every row carries a ``project_id``.

The Merge Principle
-------------------
A project row is created by *merging* a catalog record (permanent data) with
project-specific data (tags, locations, references, settings).  That merge is a
**foreign key** -- e.g. ``project_equipment.catalog_equipment_id`` -- never a
copy of the catalog's columns.  The catalog stays the single source of truth.

Each catalog-linked table also supports a **custom / one-off path**: the catalog
FK is nullable, and the row carries ``local_*`` columns that hold the permanent
attributes directly when no catalog record fits.  A named CHECK constraint
("catalog reference OR custom data, not empty") guarantees a row always has one
or the other.
"""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import CommonMixin
from .catalogs import (
    CatalogCable,
    CatalogDevice,
    CatalogEquipment,
    CatalogInstrument,
    CatalogIOModule,
)
from .enums import (
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


class Project(Base, CommonMixin):
    """The project registry.  Every Class B row references one of these."""

    __tablename__ = "projects"

    project_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    client: Mapped[str | None] = mapped_column(String(160))
    facility: Mapped[str | None] = mapped_column(String(160))
    location: Mapped[str | None] = mapped_column(String(160))
    voltage_system: Mapped[str | None] = mapped_column(String(80))
    issue_stage: Mapped[IssueStage | None] = mapped_column(
        Enum(IssueStage, native_enum=False)
    )
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False),
        nullable=False,
        default=ProjectStatus.PLANNING,
    )


class ProjectLocation(Base, CommonMixin):
    """Area / room / building / process area within a project (hierarchical)."""

    __tablename__ = "project_locations"
    __table_args__ = (
        UniqueConstraint("project_id", "location_code", name="uq_project_location_code"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    location_code: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    area_classification: Mapped[str | None] = mapped_column(String(80))
    building: Mapped[str | None] = mapped_column(String(80))
    room: Mapped[str | None] = mapped_column(String(80))
    area: Mapped[str | None] = mapped_column(String(80))
    process_system: Mapped[str | None] = mapped_column(String(120))
    indoor_outdoor: Mapped[IndoorOutdoor | None] = mapped_column(
        Enum(IndoorOutdoor, native_enum=False)
    )
    # Self-reference for a location hierarchy (a room inside a building, ...).
    parent_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )


class ProjectEquipment(Base, CommonMixin):
    """Power-distribution equipment instance in a project.

    Merges ``catalog_equipment`` (permanent ratings) with project data (tag,
    location, one-line topology via ``fed_from_id``).
    """

    __tablename__ = "project_equipment"
    __table_args__ = (
        UniqueConstraint("project_id", "equipment_tag", name="uq_project_equipment_tag"),
        CheckConstraint(
            "catalog_equipment_id IS NOT NULL OR local_model IS NOT NULL",
            name="ck_project_equipment_catalog_or_custom",
        ),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    # Merge link to the catalog (NULL => custom / one-off item).
    catalog_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_equipment.id", ondelete="RESTRICT")
    )

    # --- project-specific fields ---
    equipment_tag: Mapped[str] = mapped_column(String(60), nullable=False)
    equipment_type: Mapped[str | None] = mapped_column(String(80))
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    voltage: Mapped[str | None] = mapped_column(String(40))
    phase: Mapped[str | None] = mapped_column(String(20))
    hp_kw: Mapped[str | None] = mapped_column(String(40))  # motor HP or load kW
    fla: Mapped[float | None] = mapped_column(Float)  # full-load amps
    # One-line topology: which upstream equipment feeds this one.
    fed_from_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="SET NULL")
    )
    feeder_cable_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_cables.id", ondelete="SET NULL")
    )
    drawing_reference: Mapped[str | None] = mapped_column(String(80))
    project_settings: Mapped[str | None] = mapped_column(Text)  # ratings/settings overrides
    description: Mapped[str | None] = mapped_column(Text)

    # --- local permanent attributes (used when catalog_equipment_id is NULL) ---
    local_manufacturer: Mapped[str | None] = mapped_column(String(120))
    local_category: Mapped[EquipmentCategory | None] = mapped_column(
        Enum(EquipmentCategory, native_enum=False)
    )
    local_model: Mapped[str | None] = mapped_column(String(120))
    local_rated_voltage: Mapped[str | None] = mapped_column(String(40))
    local_rated_current: Mapped[str | None] = mapped_column(String(40))

    catalog: Mapped[CatalogEquipment | None] = relationship()

    @property
    def is_custom(self) -> bool:
        """True when this row has no catalog link (a one-off item)."""
        return self.catalog_equipment_id is None


class ProjectPanelCircuit(Base, CommonMixin):
    """A circuit / feeder within a panelboard or MCC."""

    __tablename__ = "project_panel_circuits"
    __table_args__ = (
        UniqueConstraint(
            "panel_id", "circuit_number", name="uq_project_panel_circuit_number"
        ),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    # The parent panelboard / MCC (a project_equipment row).
    panel_id: Mapped[int] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="RESTRICT"), nullable=False
    )
    circuit_number: Mapped[str] = mapped_column(String(20), nullable=False)
    load_description: Mapped[str | None] = mapped_column(String(160))
    connected_load: Mapped[float | None] = mapped_column(Float)  # VA or kW
    phases: Mapped[str | None] = mapped_column(String(20))  # e.g. "A", "A-B-C"
    breaker_size: Mapped[str | None] = mapped_column(String(40))  # breaker / starter size
    cable_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_cables.id", ondelete="SET NULL")
    )
    destination_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="SET NULL")
    )


class ProjectCable(Base, CommonMixin):
    """A cable instance -- one row of the FROM-TO cable schedule.

    Merges ``catalog_cables`` (permanent construction) with project data
    (tag, routing, endpoints).
    """

    __tablename__ = "project_cables"
    __table_args__ = (
        UniqueConstraint("project_id", "cable_tag", name="uq_project_cable_tag"),
        CheckConstraint(
            "catalog_cable_id IS NOT NULL OR local_cable_type_code IS NOT NULL",
            name="ck_project_cable_catalog_or_custom",
        ),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    catalog_cable_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_cables.id", ondelete="RESTRICT")
    )

    # --- project-specific fields ---
    cable_tag: Mapped[str] = mapped_column(String(60), nullable=False)
    from_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="SET NULL")
    )
    to_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="SET NULL")
    )
    from_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    to_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    length: Mapped[float | None] = mapped_column(Float)
    routing: Mapped[str | None] = mapped_column(String(160))  # free-text raceway note
    route_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_cable_routes.id", ondelete="SET NULL")
    )
    voltage_class: Mapped[str | None] = mapped_column(String(40))
    drawing_reference: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)

    # --- local permanent attributes (used when catalog_cable_id is NULL) ---
    local_cable_type_code: Mapped[str | None] = mapped_column(String(60))
    local_conductor_material: Mapped[ConductorMaterial | None] = mapped_column(
        Enum(ConductorMaterial, native_enum=False)
    )
    local_conductor_size: Mapped[str | None] = mapped_column(String(40))
    local_conductor_count: Mapped[int | None] = mapped_column(Integer)
    local_insulation_type: Mapped[str | None] = mapped_column(String(40))
    local_voltage_rating: Mapped[str | None] = mapped_column(String(40))

    catalog: Mapped[CatalogCable | None] = relationship()

    @property
    def is_custom(self) -> bool:
        return self.catalog_cable_id is None


class ProjectInstrument(Base, CommonMixin):
    """A field instrument instance.

    Merges ``catalog_instruments`` (permanent model data) with project data
    (ISA tag, loop, calibrated range, set point).
    """

    __tablename__ = "project_instruments"
    __table_args__ = (
        UniqueConstraint("project_id", "instrument_tag", name="uq_project_instrument_tag"),
        CheckConstraint(
            "catalog_instrument_id IS NOT NULL OR local_model IS NOT NULL",
            name="ck_project_instrument_catalog_or_custom",
        ),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    catalog_instrument_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_instruments.id", ondelete="RESTRICT")
    )

    # --- project-specific fields ---
    instrument_tag: Mapped[str] = mapped_column(String(60), nullable=False)  # ISA tag
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    measured_variable: Mapped[str | None] = mapped_column(String(80))
    pid_reference: Mapped[str | None] = mapped_column(String(60))  # P&ID drawing ref
    loop_number: Mapped[str | None] = mapped_column(String(40))
    calibrated_range: Mapped[str | None] = mapped_column(String(80))
    set_point: Mapped[str | None] = mapped_column(String(80))
    power_source: Mapped[str | None] = mapped_column(String(80))
    process_connection: Mapped[str | None] = mapped_column(String(60))
    associated_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="SET NULL")
    )
    cable_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_cables.id", ondelete="SET NULL")
    )
    plc_panel_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_control_panels.id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(Text)

    # --- local permanent attributes (used when catalog_instrument_id is NULL) ---
    local_manufacturer: Mapped[str | None] = mapped_column(String(120))
    local_instrument_type: Mapped[InstrumentType | None] = mapped_column(
        Enum(InstrumentType, native_enum=False)
    )
    local_model: Mapped[str | None] = mapped_column(String(120))
    local_signal_type: Mapped[str | None] = mapped_column(String(40))
    local_accuracy: Mapped[str | None] = mapped_column(String(60))

    catalog: Mapped[CatalogInstrument | None] = relationship()

    @property
    def is_custom(self) -> bool:
        return self.catalog_instrument_id is None


class ProjectIOPoint(Base, CommonMixin):
    """One row of the I/O list -- ties an instrument or device to a PLC point.

    Merges ``catalog_io_modules`` (the standard module) with project data
    (PLC address, signal range, wiring).
    """

    __tablename__ = "project_io_list"
    __table_args__ = (
        CheckConstraint(
            "catalog_io_module_id IS NOT NULL OR local_io_module_model IS NOT NULL",
            name="ck_project_io_catalog_or_custom",
        ),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    catalog_io_module_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_io_modules.id", ondelete="RESTRICT")
    )

    # --- project-specific fields ---
    io_tag: Mapped[str | None] = mapped_column(String(60))
    # The point usually originates at an instrument; a device-sourced point uses
    # project_panel_component_id instead.  Both are optional.
    project_instrument_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_instruments.id", ondelete="SET NULL")
    )
    project_panel_component_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_panel_components.id", ondelete="SET NULL")
    )
    io_type: Mapped[IOType] = mapped_column(
        Enum(IOType, native_enum=False), nullable=False
    )
    plc_panel_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_control_panels.id", ondelete="SET NULL")
    )
    rack: Mapped[str | None] = mapped_column(String(20))
    slot: Mapped[str | None] = mapped_column(String(20))
    channel: Mapped[str | None] = mapped_column(String(20))
    plc_address: Mapped[str | None] = mapped_column(String(60))  # combined rack-slot-ch
    signal_range: Mapped[str | None] = mapped_column(String(60))
    fail_state: Mapped[str | None] = mapped_column(String(40))
    alarm_priority: Mapped[AlarmPriority | None] = mapped_column(
        Enum(AlarmPriority, native_enum=False)
    )
    scada_tag: Mapped[str | None] = mapped_column(String(60))
    cable_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_cables.id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(Text)

    # --- local permanent attributes (used when catalog_io_module_id is NULL) ---
    local_io_module_model: Mapped[str | None] = mapped_column(String(120))

    catalog: Mapped[CatalogIOModule | None] = relationship()

    @property
    def is_custom(self) -> bool:
        return self.catalog_io_module_id is None


class ProjectControlPanel(Base, CommonMixin):
    """A control / instrumentation panel instance."""

    __tablename__ = "project_control_panels"
    __table_args__ = (
        UniqueConstraint("project_id", "panel_tag", name="uq_project_control_panel_tag"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    panel_tag: Mapped[str] = mapped_column(String(60), nullable=False)
    panel_type: Mapped[str | None] = mapped_column(String(80))
    voltage: Mapped[str | None] = mapped_column(String(40))
    enclosure_type: Mapped[str | None] = mapped_column(String(40))  # NEMA type
    sccr: Mapped[str | None] = mapped_column(String(40))  # short-circuit current rating
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    ul508a_status: Mapped[UL508AStatus | None] = mapped_column(
        Enum(UL508AStatus, native_enum=False)
    )
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(Text)


class ProjectPanelComponent(Base, CommonMixin):
    """A device placed inside a control panel.

    Merges ``catalog_devices`` (permanent device data) with project data
    (component tag, mounting reference, quantity).
    """

    __tablename__ = "project_panel_components"
    __table_args__ = (
        CheckConstraint(
            "catalog_device_id IS NOT NULL OR local_model IS NOT NULL",
            name="ck_project_panel_component_catalog_or_custom",
        ),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    # The parent control panel.
    control_panel_id: Mapped[int] = mapped_column(
        ForeignKey("project_control_panels.id", ondelete="RESTRICT"), nullable=False
    )
    catalog_device_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_devices.id", ondelete="RESTRICT")
    )

    # --- project-specific fields ---
    component_tag: Mapped[str | None] = mapped_column(String(60))
    component_type: Mapped[str | None] = mapped_column(String(80))
    part_number: Mapped[str | None] = mapped_column(String(120))
    voltage: Mapped[str | None] = mapped_column(String(40))
    power_supply_source: Mapped[str | None] = mapped_column(String(120))
    terminal_block_reference: Mapped[str | None] = mapped_column(String(80))
    mounting_reference: Mapped[str | None] = mapped_column(String(80))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(Text)

    # --- local permanent attributes (used when catalog_device_id is NULL) ---
    local_manufacturer: Mapped[str | None] = mapped_column(String(120))
    local_device_category: Mapped[DeviceCategory | None] = mapped_column(
        Enum(DeviceCategory, native_enum=False)
    )
    local_model: Mapped[str | None] = mapped_column(String(120))
    local_ratings: Mapped[str | None] = mapped_column(String(120))

    catalog: Mapped[CatalogDevice | None] = relationship()

    @property
    def is_custom(self) -> bool:
        return self.catalog_device_id is None


# ==========================================================================
# Class B -- additional project tables (no catalog merge)
# ==========================================================================


class ProjectFeeder(Base, CommonMixin):
    """A power-distribution feeder -- one row of the feeder / one-line schedule."""

    __tablename__ = "project_feeders"
    __table_args__ = (
        UniqueConstraint("project_id", "feeder_tag", name="uq_project_feeder_tag"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    feeder_tag: Mapped[str] = mapped_column(String(60), nullable=False)
    source_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="SET NULL")
    )
    load_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="SET NULL")
    )
    voltage: Mapped[str | None] = mapped_column(String(40))
    phases: Mapped[str | None] = mapped_column(String(20))
    ampacity: Mapped[str | None] = mapped_column(String(40))
    ocpd_type: Mapped[str | None] = mapped_column(String(60))  # breaker / fuse / MCP
    ocpd_rating: Mapped[str | None] = mapped_column(String(40))
    feeder_cable_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_cables.id", ondelete="SET NULL")
    )
    drawing_reference: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)


class ProjectCableRoute(Base, CommonMixin):
    """A named cable routing path between two locations."""

    __tablename__ = "project_cable_routes"
    __table_args__ = (
        UniqueConstraint("project_id", "route_tag", name="uq_project_cable_route_tag"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    route_tag: Mapped[str] = mapped_column(String(60), nullable=False)
    route_type: Mapped[RouteType | None] = mapped_column(
        Enum(RouteType, native_enum=False)
    )
    from_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    to_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    total_length: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)


class ProjectConduit(Base, CommonMixin):
    """A conduit, cable tray or duct-bank segment."""

    __tablename__ = "project_conduits"
    __table_args__ = (
        UniqueConstraint("project_id", "conduit_tag", name="uq_project_conduit_tag"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    conduit_tag: Mapped[str] = mapped_column(String(60), nullable=False)
    conduit_type: Mapped[ConduitType | None] = mapped_column(
        Enum(ConduitType, native_enum=False)
    )
    trade_size: Mapped[str | None] = mapped_column(String(40))
    material: Mapped[ConduitMaterial | None] = mapped_column(
        Enum(ConduitMaterial, native_enum=False)
    )
    route_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_cable_routes.id", ondelete="SET NULL")
    )
    from_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    to_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    length: Mapped[float | None] = mapped_column(Float)
    fill_percent: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)


class ProjectTerminalBlock(Base, CommonMixin):
    """One terminal point on a terminal strip inside a control panel."""

    __tablename__ = "project_terminal_blocks"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    control_panel_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_control_panels.id", ondelete="SET NULL")
    )
    terminal_strip: Mapped[str] = mapped_column(String(40), nullable=False)
    terminal_number: Mapped[str] = mapped_column(String(20), nullable=False)
    wire_number: Mapped[str | None] = mapped_column(String(40))
    cable_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_cables.id", ondelete="SET NULL")
    )
    conductor_core: Mapped[str | None] = mapped_column(String(40))
    device_tag: Mapped[str | None] = mapped_column(String(60))
    signal_description: Mapped[str | None] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)


class ProjectTermination(Base, CommonMixin):
    """A cable-end termination -- one conductor landed at a device or terminal."""

    __tablename__ = "project_terminations"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    cable_id: Mapped[int] = mapped_column(
        ForeignKey("project_cables.id", ondelete="RESTRICT"), nullable=False
    )
    cable_end: Mapped[CableEnd | None] = mapped_column(
        Enum(CableEnd, native_enum=False)
    )
    conductor_core: Mapped[str | None] = mapped_column(String(40))
    termination_type: Mapped[TerminationType | None] = mapped_column(
        Enum(TerminationType, native_enum=False)
    )
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_equipment.id", ondelete="SET NULL")
    )
    terminal_block_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_terminal_blocks.id", ondelete="SET NULL")
    )
    device_tag: Mapped[str | None] = mapped_column(String(60))
    drawing_reference: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)


class ProjectNetworkDevice(Base, CommonMixin):
    """A network device -- switch, gateway, router, etc."""

    __tablename__ = "project_network_devices"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "device_tag", name="uq_project_network_device_tag"
        ),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    device_tag: Mapped[str] = mapped_column(String(60), nullable=False)
    device_type: Mapped[NetworkDeviceType | None] = mapped_column(
        Enum(NetworkDeviceType, native_enum=False)
    )
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    subnet_mask: Mapped[str | None] = mapped_column(String(45))
    protocol: Mapped[NetworkProtocol | None] = mapped_column(
        Enum(NetworkProtocol, native_enum=False)
    )
    port_count: Mapped[int | None] = mapped_column(Integer)
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_locations.id", ondelete="SET NULL")
    )
    control_panel_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_control_panels.id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(Text)


class ProjectDrawing(Base, CommonMixin):
    """A drawing in the project drawing register."""

    __tablename__ = "project_drawings"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "drawing_number", name="uq_project_drawing_number"
        ),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    drawing_number: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    drawing_type: Mapped[DrawingType | None] = mapped_column(
        Enum(DrawingType, native_enum=False)
    )
    revision: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[DrawingStatus | None] = mapped_column(
        Enum(DrawingStatus, native_enum=False)
    )
    discipline: Mapped[str | None] = mapped_column(String(60))
    sheet_size: Mapped[str | None] = mapped_column(String(20))
    scale: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str | None] = mapped_column(Text)


class ProjectCalculation(Base, CommonMixin):
    """An engineering calculation in the project calculation register."""

    __tablename__ = "project_calculations"
    __table_args__ = (
        UniqueConstraint("project_id", "calc_number", name="uq_project_calc_number"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    calc_number: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    calc_type: Mapped[CalcType | None] = mapped_column(
        Enum(CalcType, native_enum=False)
    )
    revision: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[CalcStatus | None] = mapped_column(
        Enum(CalcStatus, native_enum=False)
    )
    result_summary: Mapped[str | None] = mapped_column(String(200))
    performed_by: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)


class ProjectQAQCCheck(Base, CommonMixin):
    """A QA/QC check item recorded against a project."""

    __tablename__ = "project_qaqc_checks"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    check_item: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[QAQCCategory | None] = mapped_column(
        Enum(QAQCCategory, native_enum=False)
    )
    severity: Mapped[QAQCSeverity | None] = mapped_column(
        Enum(QAQCSeverity, native_enum=False)
    )
    status: Mapped[QAQCStatus] = mapped_column(
        Enum(QAQCStatus, native_enum=False),
        nullable=False,
        default=QAQCStatus.OPEN,
    )
    related_reference: Mapped[str | None] = mapped_column(String(120))
    finding: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text)
    checked_by: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
