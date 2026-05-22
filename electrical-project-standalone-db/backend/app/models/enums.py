"""Controlled vocabularies used across the schema.

Each enum subclasses ``str`` so the value stored in the database (and emitted in
JSON) is the readable token itself -- e.g. ``"SWITCHGEAR"`` -- rather than an
opaque integer.  The columns that use these are declared with
``native_enum=False`` (see the model modules), which renders as a portable
``VARCHAR`` + ``CHECK`` constraint on both SQLite and PostgreSQL.
"""

from __future__ import annotations

import enum


class EquipmentCategory(str, enum.Enum):
    """Category of a power-distribution equipment model."""

    SWITCHGEAR = "SWITCHGEAR"
    PANELBOARD = "PANELBOARD"
    MCC = "MCC"
    TRANSFORMER = "TRANSFORMER"
    VFD = "VFD"
    ATS = "ATS"
    DISCONNECT = "DISCONNECT"
    OTHER = "OTHER"


class ConductorMaterial(str, enum.Enum):
    """Conductor metal of a cable."""

    CU = "CU"
    AL = "AL"


class InstrumentType(str, enum.Enum):
    """Measured process variable / instrument family."""

    PRESSURE = "PRESSURE"
    FLOW = "FLOW"
    LEVEL = "LEVEL"
    TEMPERATURE = "TEMPERATURE"
    ANALYTICAL = "ANALYTICAL"
    POSITION = "POSITION"
    OTHER = "OTHER"


class IOType(str, enum.Enum):
    """Type of a PLC / RIO I/O point or module."""

    AI = "AI"  # analog input
    AO = "AO"  # analog output
    DI = "DI"  # discrete input
    DO = "DO"  # discrete output
    RTD = "RTD"  # resistance temperature detector
    TC = "TC"  # thermocouple
    COMM = "COMM"  # communications
    OTHER = "OTHER"


class DeviceCategory(str, enum.Enum):
    """Category of a control / protection device inside a control panel."""

    RELAY = "RELAY"
    PLC_CPU = "PLC_CPU"
    HMI = "HMI"
    POWER_SUPPLY = "POWER_SUPPLY"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    TERMINAL_BLOCK = "TERMINAL_BLOCK"
    SURGE_PROTECTOR = "SURGE_PROTECTOR"
    NETWORK_SWITCH = "NETWORK_SWITCH"
    OTHER = "OTHER"


class ProjectStatus(str, enum.Enum):
    """Lifecycle status of a project."""

    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class IssueStage(str, enum.Enum):
    """Design issue / deliverable stage of a project."""

    CONCEPT = "CONCEPT"
    PRELIMINARY = "PRELIMINARY"
    DESIGN_30 = "DESIGN_30"
    DESIGN_60 = "DESIGN_60"
    DESIGN_90 = "DESIGN_90"
    IFC = "IFC"  # issued for construction
    AS_BUILT = "AS_BUILT"
    OTHER = "OTHER"


class IndoorOutdoor(str, enum.Enum):
    """Whether a location is indoors or outdoors."""

    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"


class UL508AStatus(str, enum.Enum):
    """UL 508A listing status of a control panel."""

    LISTED = "LISTED"
    NOT_LISTED = "NOT_LISTED"
    PENDING = "PENDING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RouteType(str, enum.Enum):
    """Predominant routing method of a cable route."""

    TRAY = "TRAY"
    CONDUIT = "CONDUIT"
    DUCTBANK = "DUCTBANK"
    DIRECT_BURIED = "DIRECT_BURIED"
    FREE_AIR = "FREE_AIR"
    OTHER = "OTHER"


class ConduitType(str, enum.Enum):
    """Type of a raceway segment."""

    CONDUIT = "CONDUIT"
    CABLE_TRAY = "CABLE_TRAY"
    DUCTBANK = "DUCTBANK"
    WIREWAY = "WIREWAY"


class ConduitMaterial(str, enum.Enum):
    """Material of a conduit / raceway."""

    PVC = "PVC"
    RMC = "RMC"
    EMT = "EMT"
    IMC = "IMC"
    ALUMINUM = "ALUMINUM"
    GALV_STEEL = "GALV_STEEL"
    FIBERGLASS = "FIBERGLASS"
    OTHER = "OTHER"


class CableEnd(str, enum.Enum):
    """Which end of a cable a termination is at."""

    FROM = "FROM"
    TO = "TO"


class TerminationType(str, enum.Enum):
    """How a conductor is terminated."""

    LUG = "LUG"
    RING = "RING"
    FERRULE = "FERRULE"
    TERMINAL_BLOCK = "TERMINAL_BLOCK"
    SPLICE = "SPLICE"
    DIRECT = "DIRECT"
    OTHER = "OTHER"


class NetworkDeviceType(str, enum.Enum):
    """Type of a network device."""

    SWITCH = "SWITCH"
    ROUTER = "ROUTER"
    GATEWAY = "GATEWAY"
    FIREWALL = "FIREWALL"
    ACCESS_POINT = "ACCESS_POINT"
    MEDIA_CONVERTER = "MEDIA_CONVERTER"
    OTHER = "OTHER"


class NetworkProtocol(str, enum.Enum):
    """Primary industrial communication protocol of a network device."""

    ETHERNET_IP = "ETHERNET_IP"
    MODBUS_TCP = "MODBUS_TCP"
    PROFINET = "PROFINET"
    OPC_UA = "OPC_UA"
    DNP3 = "DNP3"
    BACNET = "BACNET"
    OTHER = "OTHER"


class DrawingType(str, enum.Enum):
    """Discipline / type of a drawing."""

    ONE_LINE = "ONE_LINE"
    SCHEMATIC = "SCHEMATIC"
    PANEL_LAYOUT = "PANEL_LAYOUT"
    LOOP_DIAGRAM = "LOOP_DIAGRAM"
    PID = "PID"
    LOCATION_PLAN = "LOCATION_PLAN"
    CABLE_ROUTING = "CABLE_ROUTING"
    DETAIL = "DETAIL"
    OTHER = "OTHER"


class DrawingStatus(str, enum.Enum):
    """Issue status of a drawing."""

    PRELIMINARY = "PRELIMINARY"
    IFR = "IFR"  # issued for review
    IFA = "IFA"  # issued for approval
    IFB = "IFB"  # issued for bid
    IFC = "IFC"  # issued for construction
    AS_BUILT = "AS_BUILT"
    OTHER = "OTHER"


class CalcType(str, enum.Enum):
    """Type of an engineering calculation."""

    LOAD = "LOAD"
    VOLTAGE_DROP = "VOLTAGE_DROP"
    SHORT_CIRCUIT = "SHORT_CIRCUIT"
    CONDUIT_FILL = "CONDUIT_FILL"
    GROUNDING = "GROUNDING"
    LIGHTING = "LIGHTING"
    CABLE_AMPACITY = "CABLE_AMPACITY"
    ARC_FLASH = "ARC_FLASH"
    OTHER = "OTHER"


class CalcStatus(str, enum.Enum):
    """Status of an engineering calculation."""

    PRELIMINARY = "PRELIMINARY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    CHECKED = "CHECKED"
    APPROVED = "APPROVED"
    OTHER = "OTHER"


class QAQCCategory(str, enum.Enum):
    """Subject area of a QA/QC check."""

    TAGGING = "TAGGING"
    POWER = "POWER"
    CABLES = "CABLES"
    INSTRUMENTS = "INSTRUMENTS"
    IO = "IO"
    TERMINATIONS = "TERMINATIONS"
    DRAWINGS = "DRAWINGS"
    GENERAL = "GENERAL"
    OTHER = "OTHER"


class QAQCStatus(str, enum.Enum):
    """Resolution state of a QA/QC check."""

    OPEN = "OPEN"
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    RESOLVED = "RESOLVED"


class QAQCSeverity(str, enum.Enum):
    """Severity of a QA/QC finding."""

    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class AlarmPriority(str, enum.Enum):
    """Alarm priority of an I/O point."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"
