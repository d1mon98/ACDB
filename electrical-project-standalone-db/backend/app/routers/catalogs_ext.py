"""REST routers for the ~49 extended catalog tables (Groups 1-10).

All tables share the same simple schema (code / name / description / group_id)
so a single make_crud_router call per table is sufficient.
"""

from ..models.catalogs_ext import (
    AreaTypeCatalog,
    ATSCatalog,
    BreakerCatalog,
    BusDuctCatalog,
    CapacitorBankCatalog,
    MeteringEquipmentCatalog,
    PowerDistributionUnitCatalog,
    CableInsulationCatalog,
    CableTrayCatalog,
    CommunicationProtocolCatalog,
    ConductorMaterialCatalog,
    ConduitRoutingCatalog,
    ConduitTypeCatalog,
    DisconnectSwitchCatalog,
    DocumentTypeCatalog,
    DrawingTypeCatalog,
    EnclosureCatalog,
    EnvironmentalRatingCatalog,
    EquipmentModelCatalog,
    EquipmentTypeCatalog,
    FuseCatalog,
    GeneratorCatalog,
    GroundingTypeCatalog,
    HazardousAreaCatalog,
    InstallationMethodCatalog,
    InstrumentModelCatalog,
    MCCCatalog,
    MeasurementTypeCatalog,
    MountingDetailCatalog,
    MountingTypeCatalog,
    NetworkDeviceCatalog,
    OverloadCatalog,
    PanelboardCatalog,
    PhaseWireConfigCatalog,
    PLCCatalog,
    PLCIOCatalog,
    PowerSystemCatalog,
    ProcessConnectionCatalog,
    RelayCatalog,
    RevisionStatusCatalog,
    RoomTypeCatalog,
    SCADACatalog,
    SignalTypeCatalog,
    SoftStarterCatalog,
    SubmittalStatusCatalog,
    SwitchboardCatalog,
    SwitchgearCatalog,
    TerminationTypeCatalog,
    TransformerCatalog,
    UPSCatalog,
    VFDCatalog,
    VoltageClassCatalog,
    WireTypeCatalog,
)
from ..schemas.catalog_groups import (
    ATSCreate, ATSRead, ATSUpdate,
    BusDuctCreate, BusDuctRead, BusDuctUpdate,
    CapacitorBankCreate, CapacitorBankRead, CapacitorBankUpdate,
    CatalogItemCreate,
    CatalogItemRead,
    CatalogItemUpdate,
    DisconnectSwitchCreate, DisconnectSwitchRead, DisconnectSwitchUpdate,
    GeneratorCreate, GeneratorRead, GeneratorUpdate,
    MCCCreate, MCCRead, MCCUpdate,
    MeteringEquipmentCreate, MeteringEquipmentRead, MeteringEquipmentUpdate,
    PanelboardCreate, PanelboardRead, PanelboardUpdate,
    PDUCreate, PDURead, PDUUpdate,
    PowerSystemCreate, PowerSystemRead, PowerSystemUpdate,
    SwitchboardCreate, SwitchboardRead, SwitchboardUpdate,
    SwitchgearCreate, SwitchgearRead, SwitchgearUpdate,
    TransformerCreate, TransformerRead, TransformerUpdate,
    UPSCreate, UPSRead, UPSUpdate,
    WireTypeCreate, WireTypeRead, WireTypeUpdate,
)
from .factory import make_crud_router

_ENTRIES = [
    # (model,                    url-prefix,                    label)
    (VoltageClassCatalog,        "/api/cat-voltage-classes",    "Voltage class"),
    (GroundingTypeCatalog,       "/api/cat-grounding-types",    "Grounding type"),
    (PhaseWireConfigCatalog,     "/api/cat-phase-wire-configs", "Phase/wire config"),
    (EquipmentTypeCatalog,       "/api/cat-equipment-types",    "Equipment type"),
    (EquipmentModelCatalog,      "/api/cat-equipment-models",   "Equipment model"),
    (EnclosureCatalog,           "/api/cat-enclosures",         "Enclosure type"),
    (MountingTypeCatalog,        "/api/cat-mounting-types",     "Mounting type"),
    # Distribution equipment uses extended schemas -- registered separately below
    (BreakerCatalog,                "/api/cat-breakers",           "Breaker model"),
    (FuseCatalog,                "/api/cat-fuses",              "Fuse model"),
    (RelayCatalog,               "/api/cat-relays",             "Relay model"),
    (OverloadCatalog,            "/api/cat-overloads",          "Overload relay"),
    # DisconnectSwitchCatalog uses extended schema -- registered separately below
    (SoftStarterCatalog,         "/api/cat-soft-starters",      "Soft starter"),
    (VFDCatalog,                 "/api/cat-vfds",               "VFD model"),
    (ConduitTypeCatalog,         "/api/cat-conduit-types",      "Conduit type"),
    (CableTrayCatalog,           "/api/cat-cable-trays",        "Cable tray"),
    # WireTypeCatalog uses extended schema -- registered separately below
    (CableInsulationCatalog,     "/api/cat-cable-insulations",  "Cable insulation"),
    (ConductorMaterialCatalog,   "/api/cat-conductor-materials","Conductor material"),
    (InstrumentModelCatalog,     "/api/cat-instrument-models",  "Instrument model"),
    (SignalTypeCatalog,          "/api/cat-signal-types",       "Signal type"),
    (MeasurementTypeCatalog,     "/api/cat-measurement-types",  "Measurement type"),
    (ProcessConnectionCatalog,   "/api/cat-process-connections","Process connection"),
    (PLCCatalog,                 "/api/cat-plcs",               "PLC platform"),
    (PLCIOCatalog,               "/api/cat-plc-io",             "PLC I/O module"),
    (SCADACatalog,               "/api/cat-scada",              "SCADA/HMI platform"),
    (NetworkDeviceCatalog,       "/api/cat-network-devices",    "Network device"),
    (CommunicationProtocolCatalog, "/api/cat-comm-protocols",   "Comm protocol"),
    (AreaTypeCatalog,            "/api/cat-area-types",         "Area type"),
    (RoomTypeCatalog,            "/api/cat-room-types",         "Room type"),
    (HazardousAreaCatalog,       "/api/cat-hazardous-areas",    "Hazardous area"),
    (EnvironmentalRatingCatalog, "/api/cat-environmental-ratings","Environmental rating"),
    (DrawingTypeCatalog,         "/api/cat-drawing-types",      "Drawing type"),
    (RevisionStatusCatalog,      "/api/cat-revision-statuses",  "Revision status"),
    (DocumentTypeCatalog,        "/api/cat-document-types",     "Document type"),
    (SubmittalStatusCatalog,     "/api/cat-submittal-statuses", "Submittal status"),
    (InstallationMethodCatalog,  "/api/cat-installation-methods","Installation method"),
    (MountingDetailCatalog,      "/api/cat-mounting-details",   "Mounting detail"),
    (ConduitRoutingCatalog,      "/api/cat-conduit-routing",    "Conduit routing"),
    (TerminationTypeCatalog,     "/api/cat-termination-types",  "Termination type"),
]

def _ext(model, prefix, label, create, read, update):
    return make_crud_router(model=model, prefix=prefix, label=label,
                            create_schema=create, read_schema=read, update_schema=update)

_dist_routers = [
    _ext(SwitchgearCatalog,          "/api/cat-switchgear",         "Switchgear",       SwitchgearCreate,         SwitchgearRead,         SwitchgearUpdate),
    _ext(SwitchboardCatalog,         "/api/cat-switchboards",       "Switchboard",      SwitchboardCreate,        SwitchboardRead,        SwitchboardUpdate),
    _ext(MCCCatalog,                 "/api/cat-mccs",               "MCC",              MCCCreate,                MCCRead,                MCCUpdate),
    _ext(PanelboardCatalog,          "/api/cat-panelboards",        "Panelboard",       PanelboardCreate,         PanelboardRead,         PanelboardUpdate),
    _ext(TransformerCatalog,         "/api/cat-transformers",       "Transformer",      TransformerCreate,        TransformerRead,        TransformerUpdate),
    _ext(ATSCatalog,                 "/api/cat-ats",                "ATS",              ATSCreate,                ATSRead,                ATSUpdate),
    _ext(GeneratorCatalog,           "/api/cat-generators",         "Generator",        GeneratorCreate,          GeneratorRead,          GeneratorUpdate),
    _ext(UPSCatalog,                 "/api/cat-ups",                "UPS",              UPSCreate,                UPSRead,                UPSUpdate),
    _ext(DisconnectSwitchCatalog,    "/api/cat-disconnect-switches","Disconnect switch",DisconnectSwitchCreate,   DisconnectSwitchRead,   DisconnectSwitchUpdate),
    _ext(BusDuctCatalog,             "/api/cat-bus-ducts",          "Bus duct",         BusDuctCreate,            BusDuctRead,            BusDuctUpdate),
    _ext(MeteringEquipmentCatalog,   "/api/cat-meters",             "Meter",            MeteringEquipmentCreate,  MeteringEquipmentRead,  MeteringEquipmentUpdate),
    _ext(CapacitorBankCatalog,       "/api/cat-capacitor-banks",    "Capacitor bank",   CapacitorBankCreate,      CapacitorBankRead,      CapacitorBankUpdate),
    _ext(PowerDistributionUnitCatalog,"/api/cat-pdus",              "PDU",              PDUCreate,                PDURead,                PDUUpdate),
]

_power_systems_router = make_crud_router(
    model=PowerSystemCatalog,
    prefix="/api/cat-power-systems",
    label="Power system",
    create_schema=PowerSystemCreate,
    read_schema=PowerSystemRead,
    update_schema=PowerSystemUpdate,
)

_wire_types_router = make_crud_router(
    model=WireTypeCatalog,
    prefix="/api/cat-wire-types",
    label="Wire type",
    create_schema=WireTypeCreate,
    read_schema=WireTypeRead,
    update_schema=WireTypeUpdate,
)

routers = _dist_routers + [_power_systems_router, _wire_types_router] + [
    make_crud_router(
        model=model,
        prefix=prefix,
        label=label,
        create_schema=CatalogItemCreate,
        read_schema=CatalogItemRead,
        update_schema=CatalogItemUpdate,
    )
    for model, prefix, label in _ENTRIES
]

# Expose a mapping from table name → API prefix for the frontend tree view.
_DIST_PREFIX_MAP = {
    SwitchgearCatalog.__tablename__:           "/api/cat-switchgear",
    SwitchboardCatalog.__tablename__:          "/api/cat-switchboards",
    MCCCatalog.__tablename__:                  "/api/cat-mccs",
    PanelboardCatalog.__tablename__:           "/api/cat-panelboards",
    TransformerCatalog.__tablename__:          "/api/cat-transformers",
    ATSCatalog.__tablename__:                  "/api/cat-ats",
    GeneratorCatalog.__tablename__:            "/api/cat-generators",
    UPSCatalog.__tablename__:                  "/api/cat-ups",
    DisconnectSwitchCatalog.__tablename__:     "/api/cat-disconnect-switches",
    BusDuctCatalog.__tablename__:              "/api/cat-bus-ducts",
    MeteringEquipmentCatalog.__tablename__:    "/api/cat-meters",
    CapacitorBankCatalog.__tablename__:        "/api/cat-capacitor-banks",
    PowerDistributionUnitCatalog.__tablename__:"/api/cat-pdus",
}

TABLE_PREFIX_MAP: dict[str, str] = {
    PowerSystemCatalog.__tablename__: "/api/cat-power-systems",
    WireTypeCatalog.__tablename__: "/api/cat-wire-types",
    **_DIST_PREFIX_MAP,
    **{model.__tablename__: prefix for model, prefix, _ in _ENTRIES},
}
