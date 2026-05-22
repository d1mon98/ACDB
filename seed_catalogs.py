"""
Seed script — populates all CLASS A catalog tables with generic starter entries.
Run once after `db init` or `alembic upgrade head`.

Usage:
    python seed_catalogs.py
"""

from models import (
    CableCatalog,
    CableType,
    ConductorMaterial,
    ConduitCatalog,
    ConduitType,
    EquipCatalog,
    EquipType,
    InstrumentCatalog,
    InstrumentType,
    Insulation,
    Session,
    SignalType,
    init_db,
)


def seed_equip_catalog(session):
    entries = [
        EquipCatalog(
            manufacturer="Eaton",
            model="PVME-D",
            description="MV Vacuum Circuit Breaker Switchgear, 5kV",
            type=EquipType.MV_SWITCHGEAR,
            voltage_rating_v=4160,
            current_rating_a=1200,
            ic_rating_ka=40,
            interrupting_type="Vacuum",
            enclosure_nema="NEMA 1",
            weight_lbs=3200,
            notes="NEC 230.95, ANSI C37.20.2",
        ),
        EquipCatalog(
            manufacturer="Siemens",
            model="SENTRON WL",
            description="LV Metal-Enclosed Switchgear, 480V",
            type=EquipType.LV_SWITCHGEAR,
            voltage_rating_v=480,
            current_rating_a=4000,
            ic_rating_ka=85,
            interrupting_type="ACB",
            enclosure_nema="NEMA 1",
            weight_lbs=1800,
            notes="NEC 408.3",
        ),
        EquipCatalog(
            manufacturer="ABB",
            model="TrafoStar",
            description="Dry-Type Transformer, 480V-208Y/120V, 75kVA",
            type=EquipType.TRANSFORMER,
            voltage_rating_v=480,
            current_rating_a=90,
            ic_rating_ka=None,
            interrupting_type=None,
            enclosure_nema="NEMA 3R",
            weight_lbs=640,
            notes="NEC 450.3, 75kVA 480D-208Y/120V",
        ),
        EquipCatalog(
            manufacturer="Square D",
            model="NQ",
            description="120/240V 1-Phase Lighting Panelboard, 225A MLO",
            type=EquipType.PANELBOARD,
            voltage_rating_v=240,
            current_rating_a=225,
            ic_rating_ka=22,
            interrupting_type="MCB",
            enclosure_nema="NEMA 1",
            weight_lbs=85,
            notes="NEC 408.36, 42 spaces",
        ),
        EquipCatalog(
            manufacturer="Allen-Bradley",
            model="2100",
            description="MCC, 480V 3-Phase, NEMA 1, Combo Starters",
            type=EquipType.MCC,
            voltage_rating_v=480,
            current_rating_a=800,
            ic_rating_ka=42,
            interrupting_type="MCB",
            enclosure_nema="NEMA 1",
            weight_lbs=1200,
            notes="NEC 430.92; NEMA ICS 2",
        ),
        EquipCatalog(
            manufacturer="Danfoss",
            model="FC302",
            description="Variable Frequency Drive, 480V 3-Phase, 30HP",
            type=EquipType.VFD,
            voltage_rating_v=480,
            current_rating_a=62,
            ic_rating_ka=None,
            interrupting_type=None,
            enclosure_nema="NEMA 12",
            weight_lbs=110,
            notes="NEC 430.122; includes integral bypass",
        ),
        EquipCatalog(
            manufacturer="Eaton",
            model="DS7",
            description="Soft Starter, 480V 3-Phase, 75HP",
            type=EquipType.SOFT_STARTER,
            voltage_rating_v=480,
            current_rating_a=143,
            ic_rating_ka=None,
            interrupting_type=None,
            enclosure_nema="NEMA 12",
            weight_lbs=55,
            notes="NEC 430.52",
        ),
        EquipCatalog(
            manufacturer="Siemens",
            model="3KL5",
            description="Heavy-Duty Safety Disconnect, 480V 3-Phase, 100A",
            type=EquipType.DISCONNECT,
            voltage_rating_v=480,
            current_rating_a=100,
            ic_rating_ka=None,
            interrupting_type="Fused",
            enclosure_nema="NEMA 3R",
            weight_lbs=22,
            notes="NEC 430.109(A)(1)",
        ),
        EquipCatalog(
            manufacturer="Eaton",
            model="9170+",
            description="Online Double-Conversion UPS, 208V, 10kVA",
            type=EquipType.UPS,
            voltage_rating_v=208,
            current_rating_a=48,
            ic_rating_ka=None,
            interrupting_type=None,
            enclosure_nema="NEMA 1",
            weight_lbs=270,
            notes="NEC 645.11",
        ),
        EquipCatalog(
            manufacturer="Schneider Electric",
            model="PowerLogic ION9000",
            description="Revenue-Grade Power Meter, 480V",
            type=EquipType.METER,
            voltage_rating_v=480,
            current_rating_a=None,
            ic_rating_ka=None,
            interrupting_type=None,
            enclosure_nema="NEMA 4",
            weight_lbs=8,
            notes="ANSI C12.20 Class 0.2; NEC 250.119",
        ),
    ]
    session.add_all(entries)


def seed_cable_catalog(session):
    entries = [
        CableCatalog(
            manufacturer="Southwire",
            trade_name="SIMpull THHN",
            type=CableType.POWER_LV,
            conductor_material=ConductorMaterial.CU,
            insulation=Insulation.THWN_2,
            voltage_rating_v=600,
            num_conductors=3,
            awg_kcmil="12",
            shield=False,
            armor=False,
            ampacity_conduit_a=20,
            ampacity_tray_a=None,
            od_inches=0.134,
            weight_lbft=0.031,
            notes="NEC Table 310.16; 75°C column",
        ),
        CableCatalog(
            manufacturer="Southwire",
            trade_name="SIMpull THHN",
            type=CableType.POWER_LV,
            conductor_material=ConductorMaterial.CU,
            insulation=Insulation.THWN_2,
            voltage_rating_v=600,
            num_conductors=3,
            awg_kcmil="6",
            shield=False,
            armor=False,
            ampacity_conduit_a=65,
            ampacity_tray_a=None,
            od_inches=0.252,
            weight_lbft=0.101,
            notes="NEC Table 310.16; 75°C column",
        ),
        CableCatalog(
            manufacturer="Southwire",
            trade_name="SIMpull THHN",
            type=CableType.POWER_LV,
            conductor_material=ConductorMaterial.CU,
            insulation=Insulation.THWN_2,
            voltage_rating_v=600,
            num_conductors=3,
            awg_kcmil="3/0",
            shield=False,
            armor=False,
            ampacity_conduit_a=200,
            ampacity_tray_a=None,
            od_inches=0.574,
            weight_lbft=0.483,
            notes="NEC Table 310.16; 75°C column",
        ),
        CableCatalog(
            manufacturer="General Cable",
            trade_name="GenFlex EPR",
            type=CableType.POWER_MV,
            conductor_material=ConductorMaterial.CU,
            insulation=Insulation.EPR,
            voltage_rating_v=5000,
            num_conductors=3,
            awg_kcmil="2/0",
            shield=True,
            armor=False,
            ampacity_conduit_a=170,
            ampacity_tray_a=195,
            od_inches=1.21,
            weight_lbft=0.95,
            notes="NEC 310.60; 5kV shielded",
        ),
        CableCatalog(
            manufacturer="Belden",
            trade_name="8723",
            type=CableType.CONTROL,
            conductor_material=ConductorMaterial.CU,
            insulation=Insulation.TRAY,
            voltage_rating_v=600,
            num_conductors=10,
            awg_kcmil="18",
            shield=True,
            armor=False,
            ampacity_conduit_a=10,
            ampacity_tray_a=None,
            od_inches=0.52,
            weight_lbft=0.11,
            notes="NEC 725.49; overall foil shield",
        ),
        CableCatalog(
            manufacturer="Belden",
            trade_name="9501",
            type=CableType.INSTRUMENTATION,
            conductor_material=ConductorMaterial.CU,
            insulation=Insulation.TRAY,
            voltage_rating_v=300,
            num_conductors=2,
            awg_kcmil="22",
            shield=True,
            armor=False,
            ampacity_conduit_a=3,
            ampacity_tray_a=None,
            od_inches=0.22,
            weight_lbft=0.032,
            notes="NEC 727; twisted pair, foil+drain",
        ),
        CableCatalog(
            manufacturer="Corning",
            trade_name="ALTOS",
            type=CableType.FIBER,
            conductor_material=ConductorMaterial.CU,
            insulation=Insulation.OTHER,
            voltage_rating_v=0,
            num_conductors=12,
            awg_kcmil="SM-9/125",
            shield=False,
            armor=True,
            ampacity_conduit_a=None,
            ampacity_tray_a=None,
            od_inches=0.39,
            weight_lbft=0.058,
            notes="12F SM armored OSP",
        ),
        CableCatalog(
            manufacturer="Belden",
            trade_name="Cat6A",
            type=CableType.ETHERNET,
            conductor_material=ConductorMaterial.CU,
            insulation=Insulation.OTHER,
            voltage_rating_v=300,
            num_conductors=8,
            awg_kcmil="23",
            shield=False,
            armor=False,
            ampacity_conduit_a=None,
            ampacity_tray_a=None,
            od_inches=0.275,
            weight_lbft=0.038,
            notes="Cat6A UTP; TIA-568-C.2",
        ),
    ]
    session.add_all(entries)


def seed_instrument_catalog(session):
    entries = [
        InstrumentCatalog(
            manufacturer="Emerson",
            model="3051C",
            description="Coplanar Pressure Transmitter",
            type=InstrumentType.PRESSURE,
            signal_type=SignalType.mA_4_20,
            supply_vdc=24,
            enclosure_nema="NEMA 4X",
            hazardous_area_rating="Class I Div 2 Groups A-D",
            notes="HART rev 7; NEC 501.10(B)",
        ),
        InstrumentCatalog(
            manufacturer="Yokogawa",
            model="ADMAG AXR",
            description="Magnetic Flowmeter",
            type=InstrumentType.FLOW,
            signal_type=SignalType.mA_4_20,
            supply_vdc=24,
            enclosure_nema="NEMA 4X",
            hazardous_area_rating="ATEX Zone 1",
            notes="HART; pulse output available",
        ),
        InstrumentCatalog(
            manufacturer="Endress+Hauser",
            model="FMP51",
            description="Guided Radar Level Transmitter",
            type=InstrumentType.LEVEL,
            signal_type=SignalType.mA_4_20,
            supply_vdc=24,
            enclosure_nema="NEMA 4X",
            hazardous_area_rating="Class I Div 1 Groups C/D",
            notes="HART; NEC 501.10(A)",
        ),
        InstrumentCatalog(
            manufacturer="Emerson",
            model="644",
            description="Temperature Transmitter, RTD/TC Input",
            type=InstrumentType.TEMPERATURE,
            signal_type=SignalType.HART,
            supply_vdc=24,
            enclosure_nema="NEMA 4X",
            hazardous_area_rating="Class I Div 2 Groups A-D",
            notes="DIN head mount; NEC 501.10(B)",
        ),
        InstrumentCatalog(
            manufacturer="ABB",
            model="AV912",
            description="pH/ORP Analyzer",
            type=InstrumentType.ANALYZER,
            signal_type=SignalType.mA_4_20,
            supply_vdc=24,
            enclosure_nema="NEMA 4X",
            hazardous_area_rating="Ordinary",
            notes="4-wire; local display",
        ),
        InstrumentCatalog(
            manufacturer="Fisher",
            model="DVC6200",
            description="Digital Valve Controller / Positioner",
            type=InstrumentType.POSITIONER,
            signal_type=SignalType.HART,
            supply_vdc=24,
            enclosure_nema="NEMA 4X",
            hazardous_area_rating="Class I Div 1 Groups C/D",
            notes="NEC 501.115; loop-powered",
        ),
        InstrumentCatalog(
            manufacturer="ASCO",
            model="8210",
            description="Solenoid Valve, 24VDC Coil",
            type=InstrumentType.SOLENOID,
            signal_type=SignalType.DISCRETE,
            supply_vdc=24,
            enclosure_nema="NEMA 4",
            hazardous_area_rating="Class I Div 2 Groups A-D",
            notes="NEC 501.115(B)(2)",
        ),
    ]
    session.add_all(entries)


def seed_conduit_catalog(session):
    sizes = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
    # Approximate OD/ID values (inches) for EMT and RGS
    emt_dims = {
        0.5: (0.706, 0.622),
        0.75: (0.922, 0.824),
        1.0: (1.163, 1.049),
        1.5: (1.740, 1.610),
        2.0: (2.197, 2.067),
        3.0: (3.500, 3.356),
        4.0: (4.500, 4.334),
    }
    rgs_dims = {
        0.5: (0.840, 0.622),
        0.75: (1.050, 0.824),
        1.0: (1.315, 1.049),
        1.5: (1.900, 1.610),
        2.0: (2.375, 2.067),
        3.0: (3.500, 3.068),
        4.0: (4.500, 4.026),
    }
    entries = []
    for sz in [0.75, 1.0, 1.5, 2.0, 3.0]:
        od, id_ = emt_dims[sz]
        entries.append(
            ConduitCatalog(
                type=ConduitType.EMT,
                trade_size_in=sz,
                od_inches=od,
                id_inches=id_,
                notes="NEC Chapter 3, Article 358",
            )
        )
    for sz in [0.75, 1.0, 1.5, 2.0, 3.0]:
        od, id_ = rgs_dims[sz]
        entries.append(
            ConduitCatalog(
                type=ConduitType.RGS,
                trade_size_in=sz,
                od_inches=od,
                id_inches=id_,
                notes="NEC Chapter 3, Article 344",
            )
        )
    session.add_all(entries)


def run():
    init_db()
    with Session() as session:
        # Skip if already seeded
        if session.query(EquipCatalog).count() > 0:
            print("Catalog tables already seeded — skipping.")
            return
        seed_equip_catalog(session)
        seed_cable_catalog(session)
        seed_instrument_catalog(session)
        seed_conduit_catalog(session)
        session.commit()
        print("CLASS A catalog tables seeded successfully.")


if __name__ == "__main__":
    run()
