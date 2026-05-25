"""Seed the database with generic placeholder data.

Loads a small, realistic-but-fictional set of records into every Class A catalog
table, then creates ONE example project -- a water/wastewater treatment
facility -- with rows across every Class B project table, including a few merged
from the catalog and a few custom one-offs.

Usage (from the backend/ directory, with migrations already applied)::

    python seed.py                       # seed databases/project.db if empty
    python seed.py --reset               # wipe ALL data first, then seed
    python seed.py --database other.db   # seed a different database file

All data here is generic placeholder data: no real client, project or vendor
names.
"""

from __future__ import annotations

import argparse

from sqlalchemy import delete, func, select
from sqlalchemy.orm import sessionmaker

from app.config import DATABASES_DIR, DEFAULT_DATABASE
from app.database import make_engine
from app.models.catalog_groups import CatalogGroup
from app.models.catalogs import (
    CatalogCable,
    CatalogDevice,
    CatalogEquipment,
    CatalogInstrument,
    CatalogIOModule,
    CatalogManufacturer,
)
from app.models.enums import (
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
from app.models.projects import (
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

# Every table, ordered so deleting top-to-bottom never violates a foreign key.
_DELETE_ORDER = [
    ProjectTermination,
    ProjectTerminalBlock,
    ProjectIOPoint,
    ProjectConduit,
    ProjectCableRoute,
    ProjectFeeder,
    ProjectNetworkDevice,
    ProjectDrawing,
    ProjectCalculation,
    ProjectQAQCCheck,
    ProjectPanelCircuit,
    ProjectPanelComponent,
    ProjectInstrument,
    ProjectCable,
    ProjectControlPanel,
    ProjectEquipment,
    ProjectLocation,
    Project,
    CatalogEquipment,
    CatalogInstrument,
    CatalogIOModule,
    CatalogDevice,
    CatalogCable,
    CatalogManufacturer,
    CatalogGroup,
]


def wipe(db) -> None:
    """Delete every row from every table, in foreign-key-safe order."""
    for model in _DELETE_ORDER:
        db.execute(delete(model))
    db.commit()
    print("  - existing data wiped")


def seed_catalog_groups(db) -> dict[str, object]:
    """Insert the 10 top-level catalog groups (and representative sub-groups).

    Returns a code → ORM-object map for use by seed_catalogs().
    """
    # Top-level groups
    groups_data = [
        ("GRP-01", "Electrical Power Systems",      1,  None,
         "Voltage classes, grounding types, and phase/wire configurations."),
        ("GRP-02", "Electrical Equipment",          2,  None,
         "General equipment types, enclosures, and mounting standards."),
        ("GRP-03", "Distribution Equipment",        3,  None,
         "Switchgear, switchboards, MCCs, panelboards, and transformers."),
        ("GRP-04", "Protection and Control Devices",4,  None,
         "Breakers, fuses, relays, overloads, disconnect switches, VFDs."),
        ("GRP-05", "Cable and Raceway",             5,  None,
         "Cable types, conduit, cable tray, insulation, conductor materials."),
        ("GRP-06", "Instrumentation",               6,  None,
         "Instrument models, signal types, measurement types, process connections."),
        ("GRP-07", "Controls and Automation",       7,  None,
         "PLC platforms, I/O modules, SCADA, network devices, protocols."),
        ("GRP-08", "Locations and Classification",  8,  None,
         "Area types, room types, hazardous area and environmental ratings."),
        ("GRP-09", "Drawings and Documents",        9,  None,
         "Drawing types, revision statuses, document types, submittals."),
        ("GRP-10", "Construction and Installation", 10, None,
         "Installation methods, mounting details, conduit routing, terminations."),
    ]
    top = {}
    for code, name, order, parent, desc in groups_data:
        g = CatalogGroup(
            group_code=code, group_name=name, display_order=order,
            parent_group_id=parent, description=desc,
        )
        db.add(g)
        top[code] = g
    db.flush()

    # Sub-groups linking the 6 legacy complex tables
    legacy_subs = [
        ("GRP-02-MFR",  "GRP-02", "Manufacturers",            1, "catalog_manufacturers"),
        ("GRP-02-EQ",   "GRP-02", "Equipment Models",         2, "catalog_equipment"),
        ("GRP-05-CAB",  "GRP-05", "Cable Types",              1, "catalog_cables"),
        ("GRP-06-INST", "GRP-06", "Instrument Models",        1, "catalog_instruments"),
        ("GRP-07-IO",   "GRP-07", "PLC / RIO I/O Modules",    2, "catalog_io_modules"),
        ("GRP-07-DEV",  "GRP-07", "Control Panel Devices",    3, "catalog_devices"),
    ]
    subs = {}
    for code, parent_code, name, order, linked in legacy_subs:
        g = CatalogGroup(
            group_code=code, group_name=name, display_order=order,
            parent_group_id=top[parent_code].id, linked_table=linked,
        )
        db.add(g)
        subs[code] = g
    db.flush()

    all_groups = {**top, **subs}
    print(f"  - catalog groups seeded: {len(all_groups)} groups")
    return all_groups


def seed_catalogs(db, groups: dict | None = None) -> dict[str, object]:
    """Insert the Class A catalog records.  Returns a code -> ORM-object map.

    If ``groups`` is provided (from :func:`seed_catalog_groups`), each entry is
    linked to its corresponding catalog group.
    """
    mfr_group_id    = groups["GRP-02-MFR"].id  if groups else None
    eq_group_id     = groups["GRP-02-EQ"].id   if groups else None
    cab_group_id    = groups["GRP-05-CAB"].id  if groups else None
    inst_group_id   = groups["GRP-06-INST"].id if groups else None
    io_group_id     = groups["GRP-07-IO"].id   if groups else None
    dev_group_id    = groups["GRP-07-DEV"].id  if groups else None

    manufacturers = {
        "ACME": CatalogManufacturer(
            catalog_group_id=mfr_group_id,
            name="Acme Electrical Mfg.", abbreviation="ACME", country="USA",
        ),
        "SPC": CatalogManufacturer(
            catalog_group_id=mfr_group_id,
            name="Standard Power Co.", abbreviation="SPC", country="USA",
        ),
        "GII": CatalogManufacturer(
            catalog_group_id=mfr_group_id,
            name="Generic Instruments Inc.", abbreviation="GII", country="USA",
        ),
        "APX": CatalogManufacturer(
            catalog_group_id=mfr_group_id,
            name="Apex Controls Ltd.", abbreviation="APX", country="Canada",
        ),
        "UCC": CatalogManufacturer(
            catalog_group_id=mfr_group_id,
            name="Universal Cable Co.", abbreviation="UCC", country="USA",
        ),
    }
    db.add_all(manufacturers.values())
    db.flush()

    equipment = {
        "SWGR": CatalogEquipment(
            catalog_group_id=eq_group_id,
            manufacturer_id=manufacturers["ACME"].id,
            category=EquipmentCategory.SWITCHGEAR,
            model_series="ACE-SWGR-2000",
            rated_voltage="480V",
            rated_current="2000A",
            sccr_rating="65kA",
            enclosure_type="NEMA 1",
            phases=3,
            description="Generic 480V low-voltage switchgear, 2000A bus.",
        ),
        "XFMR": CatalogEquipment(
            catalog_group_id=eq_group_id,
            manufacturer_id=manufacturers["ACME"].id,
            category=EquipmentCategory.TRANSFORMER,
            model_series="ACE-TX-75",
            rated_voltage="480-208Y/120V",
            rated_kva=75.0,
            enclosure_type="NEMA 3R",
            phases=3,
            description="Generic 75 kVA dry-type distribution transformer.",
        ),
        "PNL": CatalogEquipment(
            catalog_group_id=eq_group_id,
            manufacturer_id=manufacturers["SPC"].id,
            category=EquipmentCategory.PANELBOARD,
            model_series="SPC-PNL-225",
            rated_voltage="208Y/120V",
            rated_current="225A",
            sccr_rating="22kA",
            enclosure_type="NEMA 1",
            poles=42,
            phases=3,
            description="Generic 225A lighting & appliance panelboard.",
        ),
        "MCC": CatalogEquipment(
            catalog_group_id=eq_group_id,
            manufacturer_id=manufacturers["SPC"].id,
            category=EquipmentCategory.MCC,
            model_series="SPC-MCC-600",
            rated_voltage="480V",
            rated_current="600A",
            sccr_rating="65kA",
            enclosure_type="NEMA 12",
            phases=3,
            description="Generic 480V motor control center, 600A bus.",
        ),
        "VFD": CatalogEquipment(
            catalog_group_id=eq_group_id,
            manufacturer_id=manufacturers["APX"].id,
            category=EquipmentCategory.VFD,
            model_series="APX-VFD-50",
            rated_voltage="480V",
            rated_current="65A",
            enclosure_type="NEMA 1",
            phases=3,
            description="Generic 50 HP variable frequency drive.",
        ),
    }
    db.add_all(equipment.values())

    cables = {
        "PWR250": CatalogCable(
            catalog_group_id=cab_group_id,
            cable_type_code="PWR-600V-3C-250-CU",
            conductor_material=ConductorMaterial.CU,
            insulation_type="XHHW-2",
            voltage_rating="600V",
            conductor_count=3,
            conductor_size="250 kcmil",
            ampacity=290,
            description="Generic 600V power cable, 3-conductor 250 kcmil copper.",
        ),
        "PWR4": CatalogCable(
            catalog_group_id=cab_group_id,
            cable_type_code="PWR-600V-3C-4AWG-CU",
            conductor_material=ConductorMaterial.CU,
            insulation_type="THHN",
            voltage_rating="600V",
            conductor_count=3,
            conductor_size="#4 AWG",
            ampacity=85,
            description="Generic 600V power cable, 3-conductor #4 AWG copper.",
        ),
        "CTL14": CatalogCable(
            catalog_group_id=cab_group_id,
            cable_type_code="CTL-600V-7C-14AWG-CU",
            conductor_material=ConductorMaterial.CU,
            insulation_type="THHN",
            voltage_rating="600V",
            conductor_count=7,
            conductor_size="#14 AWG",
            ampacity=20,
            description="Generic 600V control cable, 7-conductor #14 AWG copper.",
        ),
        "INST16": CatalogCable(
            catalog_group_id=cab_group_id,
            cable_type_code="INST-300V-1PR-16AWG-SH",
            conductor_material=ConductorMaterial.CU,
            insulation_type="PVC",
            voltage_rating="300V",
            conductor_count=2,
            conductor_size="#16 AWG",
            ampacity=10,
            shielded=True,
            description="Generic 300V instrument cable, 1 shielded pair #16 AWG.",
        ),
    }
    db.add_all(cables.values())

    instruments = {
        "PT": CatalogInstrument(
            catalog_group_id=inst_group_id,
            manufacturer_id=manufacturers["GII"].id,
            instrument_type=InstrumentType.PRESSURE,
            measurement_principle="Capacitance",
            model_series="GII-PT-100",
            signal_type="4-20mA HART",
            process_connection="1/2 in NPT",
            accuracy="+/-0.075%",
            power_requirement="24 VDC",
            area_classification="Class I Div 2",
            description="Generic gauge pressure transmitter.",
        ),
        "FT": CatalogInstrument(
            catalog_group_id=inst_group_id,
            manufacturer_id=manufacturers["GII"].id,
            instrument_type=InstrumentType.FLOW,
            measurement_principle="Magnetic",
            model_series="GII-FM-200",
            signal_type="4-20mA HART",
            process_connection="6 in flanged",
            accuracy="+/-0.5%",
            power_requirement="24 VDC",
            area_classification="Unclassified",
            description="Generic magnetic flow meter.",
        ),
        "LT": CatalogInstrument(
            catalog_group_id=inst_group_id,
            manufacturer_id=manufacturers["GII"].id,
            instrument_type=InstrumentType.LEVEL,
            measurement_principle="Guided-wave radar",
            model_series="GII-LT-300",
            signal_type="4-20mA HART",
            process_connection="3 in flanged",
            accuracy="+/-2 mm",
            power_requirement="24 VDC",
            area_classification="Class I Div 1",
            description="Generic radar level transmitter.",
        ),
        "TT": CatalogInstrument(
            catalog_group_id=inst_group_id,
            manufacturer_id=manufacturers["APX"].id,
            instrument_type=InstrumentType.TEMPERATURE,
            measurement_principle="RTD Pt100",
            model_series="APX-TT-400",
            signal_type="4-20mA",
            process_connection="1/2 in NPT thermowell",
            accuracy="+/-0.1%",
            power_requirement="24 VDC",
            area_classification="Class I Div 2",
            description="Generic RTD temperature transmitter.",
        ),
    }
    db.add_all(instruments.values())

    io_modules = {
        "AI8": CatalogIOModule(
            catalog_group_id=io_group_id,
            manufacturer_id=manufacturers["APX"].id,
            module_model="APX-AI-8",
            io_type=IOType.AI,
            point_count=8,
            signal_range="4-20mA",
            description="Generic 8-channel analog input module.",
        ),
        "AO4": CatalogIOModule(
            catalog_group_id=io_group_id,
            manufacturer_id=manufacturers["APX"].id,
            module_model="APX-AO-4",
            io_type=IOType.AO,
            point_count=4,
            signal_range="4-20mA",
            description="Generic 4-channel analog output module.",
        ),
        "DI16": CatalogIOModule(
            catalog_group_id=io_group_id,
            manufacturer_id=manufacturers["APX"].id,
            module_model="APX-DI-16",
            io_type=IOType.DI,
            point_count=16,
            signal_range="24 VDC",
            description="Generic 16-channel discrete input module.",
        ),
        "DO16": CatalogIOModule(
            catalog_group_id=io_group_id,
            manufacturer_id=manufacturers["APX"].id,
            module_model="APX-DO-16",
            io_type=IOType.DO,
            point_count=16,
            signal_range="24 VDC",
            description="Generic 16-channel discrete output module.",
        ),
    }
    db.add_all(io_modules.values())

    devices = {
        "CPU": CatalogDevice(
            catalog_group_id=dev_group_id,
            manufacturer_id=manufacturers["APX"].id,
            device_category=DeviceCategory.PLC_CPU,
            model="APX-CPU-1500",
            ratings="32-bit processor, 2 MB",
            description="Generic PLC processor module.",
        ),
        "HMI": CatalogDevice(
            catalog_group_id=dev_group_id,
            manufacturer_id=manufacturers["APX"].id,
            device_category=DeviceCategory.HMI,
            model="APX-HMI-10",
            ratings="10 in touchscreen, 24 VDC",
            description="Generic 10-inch operator interface.",
        ),
        "PS": CatalogDevice(
            catalog_group_id=dev_group_id,
            manufacturer_id=manufacturers["ACME"].id,
            device_category=DeviceCategory.POWER_SUPPLY,
            model="ACE-PS-24-10",
            ratings="24 VDC, 10 A",
            description="Generic DIN-rail switching power supply.",
        ),
        "MCB": CatalogDevice(
            catalog_group_id=dev_group_id,
            manufacturer_id=manufacturers["SPC"].id,
            device_category=DeviceCategory.CIRCUIT_BREAKER,
            model="SPC-MCB-20A",
            ratings="20 A, 1-pole, 240 VAC",
            description="Generic miniature circuit breaker.",
        ),
        "RLY": CatalogDevice(
            catalog_group_id=dev_group_id,
            manufacturer_id=manufacturers["GII"].id,
            device_category=DeviceCategory.RELAY,
            model="GII-RLY-4PDT",
            ratings="4PDT, 24 VDC coil",
            description="Generic plug-in control relay.",
        ),
    }
    db.add_all(devices.values())

    db.flush()
    print(
        "  - catalogs seeded: "
        f"{len(manufacturers)} manufacturers, {len(equipment)} equipment, "
        f"{len(cables)} cables, {len(instruments)} instruments, "
        f"{len(io_modules)} I/O modules, {len(devices)} devices"
    )
    return {
        "equipment": equipment,
        "cables": cables,
        "instruments": instruments,
        "io_modules": io_modules,
        "devices": devices,
    }


def seed_example_project(db, catalog: dict) -> None:
    """Create one example water/wastewater project across every Class B table."""
    eq = catalog["equipment"]
    cab = catalog["cables"]
    instr = catalog["instruments"]
    io = catalog["io_modules"]
    dev = catalog["devices"]

    project = Project(
        project_number="EX-001",
        name="Example Treatment Facility",
        client="Sample Municipal Client",
        facility="Main Treatment Plant",
        location="Anytown, USA",
        voltage_system="480V 3-phase / 208Y/120V",
        issue_stage=IssueStage.DESIGN_60,
        status=ProjectStatus.ACTIVE,
        description=(
            "Example water/wastewater project demonstrating the expanded "
            "schema. All data is generic placeholder data."
        ),
    )
    db.add(project)
    db.flush()
    pid = project.id

    # --- locations --------------------------------------------------------
    loc_elec = ProjectLocation(
        project_id=pid, location_code="AREA-100", description="Electrical Room",
        building="Administration Building", room="Electrical Room", area="Electrical",
        indoor_outdoor=IndoorOutdoor.INDOOR, area_classification="Unclassified",
    )
    loc_process = ProjectLocation(
        project_id=pid, location_code="AREA-200", description="Process Area",
        building="Process Building", area="Aeration Basin", process_system="Aeration",
        indoor_outdoor=IndoorOutdoor.INDOOR, area_classification="Class I Div 2",
    )
    db.add_all([loc_elec, loc_process])
    db.flush()
    loc_pump = ProjectLocation(
        project_id=pid, location_code="AREA-210", description="Influent Pump Station",
        area="Pump Station", process_system="Influent Pumping",
        indoor_outdoor=IndoorOutdoor.OUTDOOR, area_classification="Unclassified",
        parent_location_id=loc_process.id,
    )
    loc_control = ProjectLocation(
        project_id=pid, location_code="AREA-300", description="Control Room",
        building="Administration Building", room="Control Room",
        indoor_outdoor=IndoorOutdoor.INDOOR, area_classification="Unclassified",
    )
    db.add_all([loc_pump, loc_control])
    db.flush()

    # --- equipment (merged + custom one-offs) -----------------------------
    mts = ProjectEquipment(
        project_id=pid, catalog_equipment_id=eq["SWGR"].id, equipment_tag="MTS-1",
        equipment_type="Switchgear", location_id=loc_elec.id, voltage="480V", phase="3",
        drawing_reference="E-001", description="Main switchgear.",
    )
    db.add(mts)
    db.flush()
    xfmr = ProjectEquipment(
        project_id=pid, catalog_equipment_id=eq["XFMR"].id, equipment_tag="XFMR-1",
        equipment_type="Transformer", location_id=loc_elec.id,
        voltage="480-208Y/120V", phase="3", fed_from_id=mts.id, drawing_reference="E-001",
    )
    mcc = ProjectEquipment(
        project_id=pid, catalog_equipment_id=eq["MCC"].id, equipment_tag="MCC-1",
        equipment_type="MCC", location_id=loc_process.id, voltage="480V", phase="3",
        fed_from_id=mts.id, drawing_reference="E-001",
    )
    db.add_all([xfmr, mcc])
    db.flush()
    pnl = ProjectEquipment(
        project_id=pid, catalog_equipment_id=eq["PNL"].id, equipment_tag="PNL-1",
        equipment_type="Panelboard", location_id=loc_elec.id, voltage="208Y/120V",
        phase="3", fed_from_id=xfmr.id, drawing_reference="E-001",
    )
    db.add(pnl)
    db.flush()
    p101 = ProjectEquipment(
        project_id=pid, catalog_equipment_id=None, equipment_tag="P-101",
        equipment_type="Motor", location_id=loc_pump.id, voltage="480V", phase="3",
        hp_kw="25 HP", fla=34.0, fed_from_id=mcc.id, drawing_reference="E-002",
        local_manufacturer="Generic Motor Co.", local_category=EquipmentCategory.OTHER,
        local_model="Influent Pump Motor 25HP", local_rated_voltage="480V",
        local_rated_current="34A", description="Influent pump motor (custom one-off).",
    )
    db.add(p101)
    db.flush()

    # --- control panels ---------------------------------------------------
    plc_panel = ProjectControlPanel(
        project_id=pid, panel_tag="PLC-1", panel_type="PLC Panel", voltage="120 VAC",
        enclosure_type="NEMA 12", sccr="5kA", manufacturer="Apex Controls Ltd.",
        ul508a_status=UL508AStatus.LISTED, location_id=loc_control.id,
        description="Main PLC control panel.",
    )
    cp101 = ProjectControlPanel(
        project_id=pid, panel_tag="CP-101", panel_type="Pump Control Panel",
        voltage="480 VAC", enclosure_type="NEMA 4X", sccr="10kA",
        manufacturer="Apex Controls Ltd.", ul508a_status=UL508AStatus.LISTED,
        location_id=loc_pump.id, description="Influent pump control panel.",
    )
    db.add_all([plc_panel, cp101])
    db.flush()

    # --- cable routes -----------------------------------------------------
    rt01 = ProjectCableRoute(
        project_id=pid, route_tag="RT-01", route_type=RouteType.TRAY,
        from_location_id=loc_elec.id, to_location_id=loc_process.id,
        total_length=80.0, description="Main cable tray run.",
    )
    rt02 = ProjectCableRoute(
        project_id=pid, route_tag="RT-02", route_type=RouteType.DUCTBANK,
        from_location_id=loc_process.id, to_location_id=loc_pump.id,
        total_length=120.0, description="Duct bank to pump station.",
    )
    db.add_all([rt01, rt02])
    db.flush()

    # --- cables (merged + custom) -----------------------------------------
    c_mcc = ProjectCable(
        project_id=pid, catalog_cable_id=cab["PWR250"].id, cable_tag="C-MCC1-01",
        from_equipment_id=mts.id, to_equipment_id=mcc.id, from_location_id=loc_elec.id,
        to_location_id=loc_process.id, length=80.0, route_id=rt01.id,
        voltage_class="600V", drawing_reference="E-001",
    )
    c_pnl = ProjectCable(
        project_id=pid, catalog_cable_id=cab["PWR4"].id, cable_tag="C-PNL1-01",
        from_equipment_id=xfmr.id, to_equipment_id=pnl.id, length=25.0,
        voltage_class="600V", drawing_reference="E-001",
    )
    c_p101 = ProjectCable(
        project_id=pid, catalog_cable_id=None, cable_tag="C-P101-01",
        from_equipment_id=mcc.id, to_equipment_id=p101.id, from_location_id=loc_process.id,
        to_location_id=loc_pump.id, length=120.0, route_id=rt02.id, voltage_class="600V",
        drawing_reference="E-002", local_cable_type_code="VFD-600V-3C-8AWG-CU",
        local_conductor_material=ConductorMaterial.CU, local_conductor_size="#8 AWG",
        local_conductor_count=3, local_insulation_type="XHHW-2",
        local_voltage_rating="600V", description="Influent pump motor feeder (custom).",
    )
    c_fit = ProjectCable(
        project_id=pid, catalog_cable_id=cab["INST16"].id, cable_tag="C-FIT101-01",
        from_location_id=loc_process.id, to_location_id=loc_control.id, length=95.0,
        route_id=rt01.id, voltage_class="300V", description="FIT-101 instrument cable.",
    )
    c_lit = ProjectCable(
        project_id=pid, catalog_cable_id=cab["INST16"].id, cable_tag="C-LIT201-01",
        from_location_id=loc_process.id, to_location_id=loc_control.id, length=90.0,
        route_id=rt01.id, voltage_class="300V", description="LIT-201 instrument cable.",
    )
    db.add_all([c_mcc, c_pnl, c_p101, c_fit, c_lit])
    db.flush()

    # --- panel circuits (within PNL-1) ------------------------------------
    db.add_all([
        ProjectPanelCircuit(
            project_id=pid, panel_id=pnl.id, circuit_number="1",
            load_description="Lighting - Electrical Room", connected_load=1200.0,
            phases="A", breaker_size="20A",
        ),
        ProjectPanelCircuit(
            project_id=pid, panel_id=pnl.id, circuit_number="3",
            load_description="Receptacles", connected_load=1500.0, phases="B",
            breaker_size="20A",
        ),
        ProjectPanelCircuit(
            project_id=pid, panel_id=pnl.id, circuit_number="5",
            load_description="PLC Panel Feed", connected_load=2400.0, phases="C",
            breaker_size="20A",
        ),
    ])

    # --- instruments (merged + custom) ------------------------------------
    fit101 = ProjectInstrument(
        project_id=pid, catalog_instrument_id=instr["FT"].id, instrument_tag="FIT-101",
        location_id=loc_process.id, measured_variable="Flow", pid_reference="P-101",
        loop_number="101", calibrated_range="0-2000 GPM", power_source="24 VDC",
        process_connection="6 in flanged", associated_equipment_id=p101.id,
        cable_id=c_fit.id, plc_panel_id=plc_panel.id,
    )
    lit201 = ProjectInstrument(
        project_id=pid, catalog_instrument_id=instr["LT"].id, instrument_tag="LIT-201",
        location_id=loc_process.id, measured_variable="Level", pid_reference="P-201",
        loop_number="201", calibrated_range="0-20 ft", power_source="24 VDC",
        cable_id=c_lit.id, plc_panel_id=plc_panel.id,
    )
    pit301 = ProjectInstrument(
        project_id=pid, catalog_instrument_id=None, instrument_tag="PIT-301",
        location_id=loc_pump.id, measured_variable="Pressure", loop_number="301",
        calibrated_range="0-100 psig", local_manufacturer="Field Supplied",
        local_instrument_type=InstrumentType.PRESSURE, local_model="Custom-PT-Gauge",
        local_signal_type="4-20mA", description="Custom pressure transmitter (one-off).",
    )
    db.add_all([fit101, lit201, pit301])
    db.flush()

    # --- I/O list (merged + custom) ---------------------------------------
    db.add_all([
        ProjectIOPoint(
            project_id=pid, catalog_io_module_id=io["AI8"].id, io_tag="FIT-101",
            project_instrument_id=fit101.id, io_type=IOType.AI, plc_panel_id=plc_panel.id,
            rack="1", slot="2", channel="0", plc_address="R1-S2-CH0",
            signal_range="4-20mA", alarm_priority=AlarmPriority.HIGH,
            scada_tag="FIT_101_FLOW", cable_id=c_fit.id,
            description="Influent flow input.",
        ),
        ProjectIOPoint(
            project_id=pid, catalog_io_module_id=io["AI8"].id, io_tag="LIT-201",
            project_instrument_id=lit201.id, io_type=IOType.AI, plc_panel_id=plc_panel.id,
            rack="1", slot="2", channel="1", plc_address="R1-S2-CH1",
            signal_range="4-20mA", alarm_priority=AlarmPriority.HIGH,
            scada_tag="LIT_201_LEVEL", cable_id=c_lit.id,
            description="Aeration basin level input.",
        ),
        ProjectIOPoint(
            project_id=pid, catalog_io_module_id=None, io_tag="P-101-RUN",
            io_type=IOType.DI, plc_panel_id=plc_panel.id, rack="1", slot="4",
            channel="0", plc_address="R1-S4-CH0", signal_range="24 VDC",
            alarm_priority=AlarmPriority.MEDIUM, scada_tag="P_101_RUN",
            local_io_module_model="Custom-DI-Card",
            description="Influent pump run status (custom module).",
        ),
    ])

    # --- panel components -------------------------------------------------
    db.add_all([
        ProjectPanelComponent(
            project_id=pid, control_panel_id=plc_panel.id, catalog_device_id=dev["CPU"].id,
            component_tag="CPU", component_type="PLC Processor", part_number="APX-CPU-1500",
            voltage="24 VDC", mounting_reference="DIN rail 1", quantity=1,
        ),
        ProjectPanelComponent(
            project_id=pid, control_panel_id=plc_panel.id, catalog_device_id=dev["HMI"].id,
            component_tag="HMI", component_type="Operator Interface",
            part_number="APX-HMI-10", voltage="24 VDC", mounting_reference="Door",
            quantity=1,
        ),
        ProjectPanelComponent(
            project_id=pid, control_panel_id=cp101.id, catalog_device_id=dev["PS"].id,
            component_tag="PS-1", component_type="Power Supply", part_number="ACE-PS-24-10",
            voltage="24 VDC", mounting_reference="DIN rail 1", quantity=1,
        ),
        ProjectPanelComponent(
            project_id=pid, control_panel_id=cp101.id, catalog_device_id=None,
            component_tag="CR-1", component_type="Relay", quantity=2,
            mounting_reference="DIN rail 2", local_manufacturer="Field Supplied",
            local_device_category=DeviceCategory.RELAY, local_model="Custom-Relay-X",
            local_ratings="DPDT, 120 VAC coil", description="Custom relay (one-off).",
        ),
    ])

    # --- terminal blocks --------------------------------------------------
    tb_list = [
        ProjectTerminalBlock(
            project_id=pid, control_panel_id=cp101.id, terminal_strip="TB1",
            terminal_number="1", wire_number="W-101", cable_id=c_p101.id,
            conductor_core="U", device_tag="P-101", signal_description="Motor lead T1",
        ),
        ProjectTerminalBlock(
            project_id=pid, control_panel_id=cp101.id, terminal_strip="TB1",
            terminal_number="2", wire_number="W-102", cable_id=c_p101.id,
            conductor_core="V", device_tag="P-101", signal_description="Motor lead T2",
        ),
        ProjectTerminalBlock(
            project_id=pid, control_panel_id=cp101.id, terminal_strip="TB1",
            terminal_number="3", wire_number="W-103", cable_id=c_p101.id,
            conductor_core="W", device_tag="P-101", signal_description="Motor lead T3",
        ),
        ProjectTerminalBlock(
            project_id=pid, control_panel_id=plc_panel.id, terminal_strip="TB2",
            terminal_number="1", wire_number="W-201", cable_id=c_fit.id,
            conductor_core="+", device_tag="FIT-101", signal_description="4-20mA +",
        ),
    ]
    db.add_all(tb_list)
    db.flush()

    # --- terminations -----------------------------------------------------
    db.add_all([
        ProjectTermination(
            project_id=pid, cable_id=c_p101.id, cable_end=CableEnd.FROM,
            conductor_core="U/V/W", termination_type=TerminationType.LUG,
            equipment_id=mcc.id, device_tag="MCC-1", drawing_reference="E-002",
            description="Pump feeder source termination.",
        ),
        ProjectTermination(
            project_id=pid, cable_id=c_p101.id, cable_end=CableEnd.TO,
            conductor_core="U/V/W", termination_type=TerminationType.LUG,
            equipment_id=p101.id, device_tag="P-101", drawing_reference="E-002",
            description="Pump feeder load termination.",
        ),
        ProjectTermination(
            project_id=pid, cable_id=c_fit.id, cable_end=CableEnd.TO,
            conductor_core="+", termination_type=TerminationType.TERMINAL_BLOCK,
            terminal_block_id=tb_list[3].id, device_tag="FIT-101",
            description="Instrument cable termination at PLC-1.",
        ),
    ])

    # --- network devices --------------------------------------------------
    db.add(ProjectNetworkDevice(
        project_id=pid, device_tag="SW-01", device_type=NetworkDeviceType.SWITCH,
        manufacturer="Apex Controls Ltd.", model="APX-SW-8", ip_address="192.168.1.10",
        subnet_mask="255.255.255.0", protocol=NetworkProtocol.ETHERNET_IP, port_count=8,
        location_id=loc_control.id, control_panel_id=plc_panel.id,
        description="Plant control network switch.",
    ))

    # --- feeders (Power Distribution) -------------------------------------
    db.add_all([
        ProjectFeeder(
            project_id=pid, feeder_tag="FDR-MCC1", source_equipment_id=mts.id,
            load_equipment_id=mcc.id, voltage="480V", phases="3", ampacity="400A",
            ocpd_type="Breaker", ocpd_rating="400A", feeder_cable_id=c_mcc.id,
            drawing_reference="E-001",
        ),
        ProjectFeeder(
            project_id=pid, feeder_tag="FDR-PNL1", source_equipment_id=xfmr.id,
            load_equipment_id=pnl.id, voltage="208Y/120V", phases="3", ampacity="225A",
            ocpd_type="Breaker", ocpd_rating="225A", feeder_cable_id=c_pnl.id,
            drawing_reference="E-001",
        ),
        ProjectFeeder(
            project_id=pid, feeder_tag="FDR-P101", source_equipment_id=mcc.id,
            load_equipment_id=p101.id, voltage="480V", phases="3", ampacity="40A",
            ocpd_type="MCP", ocpd_rating="50A", feeder_cable_id=c_p101.id,
            drawing_reference="E-002",
        ),
    ])

    # --- conduits / trays -------------------------------------------------
    db.add_all([
        ProjectConduit(
            project_id=pid, conduit_tag="CT-1", conduit_type=ConduitType.CABLE_TRAY,
            trade_size="12 in", material=ConduitMaterial.GALV_STEEL, route_id=rt01.id,
            from_location_id=loc_elec.id, to_location_id=loc_process.id, length=80.0,
            fill_percent=30.0,
        ),
        ProjectConduit(
            project_id=pid, conduit_tag="DB-1", conduit_type=ConduitType.DUCTBANK,
            trade_size="4 in", material=ConduitMaterial.PVC, route_id=rt02.id,
            from_location_id=loc_process.id, to_location_id=loc_pump.id, length=120.0,
            fill_percent=35.0,
        ),
        ProjectConduit(
            project_id=pid, conduit_tag="C-1", conduit_type=ConduitType.CONDUIT,
            trade_size="3/4 in", material=ConduitMaterial.EMT,
            from_location_id=loc_process.id, to_location_id=loc_control.id, length=40.0,
            fill_percent=22.0,
        ),
    ])

    # --- drawings ---------------------------------------------------------
    db.add_all([
        ProjectDrawing(
            project_id=pid, drawing_number="E-001", title="Electrical One-Line Diagram",
            drawing_type=DrawingType.ONE_LINE, revision="B", status=DrawingStatus.IFR,
            discipline="Electrical", sheet_size="ANSI D",
        ),
        ProjectDrawing(
            project_id=pid, drawing_number="E-101", title="MCC-1 Panel Layout",
            drawing_type=DrawingType.PANEL_LAYOUT, revision="A",
            status=DrawingStatus.PRELIMINARY, discipline="Electrical", sheet_size="ANSI D",
        ),
        ProjectDrawing(
            project_id=pid, drawing_number="I-001", title="FIT-101 Loop Diagram",
            drawing_type=DrawingType.LOOP_DIAGRAM, revision="A", status=DrawingStatus.IFR,
            discipline="I&C", sheet_size="ANSI B",
        ),
    ])

    # --- calculations -----------------------------------------------------
    db.add_all([
        ProjectCalculation(
            project_id=pid, calc_number="CALC-001", title="Facility Load Summary",
            calc_type=CalcType.LOAD, revision="B", status=CalcStatus.COMPLETE,
            result_summary="Total connected load 480 kVA", performed_by="Engineer",
        ),
        ProjectCalculation(
            project_id=pid, calc_number="CALC-002",
            title="Influent Pump Feeder Voltage Drop", calc_type=CalcType.VOLTAGE_DROP,
            revision="A", status=CalcStatus.CHECKED,
            result_summary="2.1% voltage drop at full load", performed_by="Engineer",
        ),
    ])

    # --- QA/QC checks -----------------------------------------------------
    db.add_all([
        ProjectQAQCCheck(
            project_id=pid, check_item="All equipment tags are unique",
            category=QAQCCategory.TAGGING, severity=QAQCSeverity.MAJOR,
            status=QAQCStatus.PASS, checked_by="Reviewer",
        ),
        ProjectQAQCCheck(
            project_id=pid,
            check_item="Influent pump feeder sized per NEC 430.22 (125% FLA)",
            category=QAQCCategory.CABLES, severity=QAQCSeverity.CRITICAL,
            status=QAQCStatus.OPEN, related_reference="C-P101-01",
            finding="Confirm #8 AWG ampacity against 125% of 34 A FLA.",
        ),
        ProjectQAQCCheck(
            project_id=pid, check_item="All instruments assigned to an I/O point",
            category=QAQCCategory.IO, severity=QAQCSeverity.MAJOR,
            status=QAQCStatus.OPEN, finding="PIT-301 has no I/O point yet.",
        ),
    ])

    db.flush()
    print(f"  - example project seeded: '{project.name}' ({project.project_number})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed an Electrical Project Standalone DB database file."
    )
    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE,
        help=f"Database file in the databases/ directory (default: {DEFAULT_DATABASE}).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe ALL existing data before seeding.",
    )
    args = parser.parse_args()

    db_path = DATABASES_DIR / args.database
    if not db_path.exists():
        print(f"Database '{args.database}' not found at {db_path}.")
        print("Create the schema first, e.g.:  alembic upgrade head")
        return

    engine = make_engine(f"sqlite:///{db_path}")
    session_factory = sessionmaker(bind=engine, autoflush=False, future=True)
    db = session_factory()
    try:
        existing = db.scalar(select(func.count()).select_from(Project)) or 0
        if existing and not args.reset:
            print(
                f"Database '{args.database}' already contains data "
                f"({existing} project(s)). Use --reset to wipe and reseed."
            )
            return

        print(f"Seeding '{args.database}'...")
        if args.reset:
            wipe(db)

        groups  = seed_catalog_groups(db)
        catalog = seed_catalogs(db, groups)
        seed_example_project(db, catalog)
        db.commit()
        print("Done.")
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()
