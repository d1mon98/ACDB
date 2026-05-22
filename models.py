"""
SQLAlchemy ORM models for the Electrical Project Database.

CLASS A — global catalog tables (shared across all projects)
CLASS B — project-specific tables (per-project, FK'd to projects)
"""

from __future__ import annotations

import enum
import os
from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

DATABASE_URL = os.environ.get("ACDB_URL", "sqlite:///acdb.db")

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EquipType(str, enum.Enum):
    MV_SWITCHGEAR = "MV_SWITCHGEAR"
    LV_SWITCHGEAR = "LV_SWITCHGEAR"
    TRANSFORMER = "TRANSFORMER"
    PANELBOARD = "PANELBOARD"
    MCC = "MCC"
    VFD = "VFD"
    SOFT_STARTER = "SOFT_STARTER"
    DISCONNECT = "DISCONNECT"
    UPS = "UPS"
    METER = "METER"
    OTHER = "OTHER"


class CableType(str, enum.Enum):
    POWER_MV = "POWER_MV"
    POWER_LV = "POWER_LV"
    CONTROL = "CONTROL"
    INSTRUMENTATION = "INSTRUMENTATION"
    FIBER = "FIBER"
    ETHERNET = "ETHERNET"


class ConductorMaterial(str, enum.Enum):
    CU = "CU"
    AL = "AL"


class Insulation(str, enum.Enum):
    XHHW_2 = "XHHW-2"
    THWN_2 = "THWN-2"
    EPR = "EPR"
    TRAY = "TRAY"
    OTHER = "OTHER"


class InstrumentType(str, enum.Enum):
    PRESSURE = "PRESSURE"
    FLOW = "FLOW"
    LEVEL = "LEVEL"
    TEMPERATURE = "TEMPERATURE"
    ANALYZER = "ANALYZER"
    POSITIONER = "POSITIONER"
    SOLENOID = "SOLENOID"
    OTHER = "OTHER"


class SignalType(str, enum.Enum):
    mA_4_20 = "4-20mA"
    DISCRETE = "DISCRETE"
    HART = "HART"
    PROFIBUS = "PROFIBUS"
    MODBUS = "MODBUS"
    ETHERNET = "ETHERNET"
    OTHER = "OTHER"


class ConduitType(str, enum.Enum):
    EMT = "EMT"
    IMC = "IMC"
    RGS = "RGS"
    PVC_40 = "PVC_40"
    PVC_80 = "PVC_80"
    LFMC = "LFMC"
    OTHER = "OTHER"


class VoltageSystem(str, enum.Enum):
    V208Y120 = "208Y/120"
    V480Y277 = "480Y/277"
    V4160 = "4160"
    V13800 = "13800"
    OTHER = "OTHER"


class AreaClassification(str, enum.Enum):
    ORDINARY = "ORDINARY"
    CLASS_I_DIV1 = "CLASS_I_DIV1"
    CLASS_I_DIV2 = "CLASS_I_DIV2"
    CLASS_II_DIV1 = "CLASS_II_DIV1"
    CLASS_II_DIV2 = "CLASS_II_DIV2"
    ZONE_0 = "ZONE_0"
    ZONE_1 = "ZONE_1"
    ZONE_2 = "ZONE_2"


class EquipStatus(str, enum.Enum):
    DESIGN = "DESIGN"
    ISSUED = "ISSUED"
    PURCHASED = "PURCHASED"
    INSTALLED = "INSTALLED"
    COMMISSIONED = "COMMISSIONED"


class CableStatus(str, enum.Enum):
    DESIGN = "DESIGN"
    ROUTED = "ROUTED"
    PULLED = "PULLED"
    TERMINATED = "TERMINATED"
    TESTED = "TESTED"


class Phase(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    AB = "A-B"
    BC = "B-C"
    AC = "A-C"
    THREE_PH = "3PH"


# ---------------------------------------------------------------------------
# CLASS A — GLOBAL CATALOG TABLES
# ---------------------------------------------------------------------------

class EquipCatalog(Base):
    __tablename__ = "equip_catalog"

    equip_catalog_id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer = Column(String(100))
    model = Column(String(100))
    description = Column(String(255))
    type = Column(Enum(EquipType), nullable=False)
    voltage_rating_v = Column(Integer)
    current_rating_a = Column(Float)
    ic_rating_ka = Column(Float)
    interrupting_type = Column(String(50))
    enclosure_nema = Column(String(20))
    weight_lbs = Column(Float)
    notes = Column(Text)

    equipment = relationship("Equipment", back_populates="catalog_entry")


class CableCatalog(Base):
    __tablename__ = "cable_catalog"

    cable_catalog_id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer = Column(String(100))
    trade_name = Column(String(100))
    type = Column(Enum(CableType), nullable=False)
    conductor_material = Column(Enum(ConductorMaterial), nullable=False)
    insulation = Column(Enum(Insulation), nullable=False)
    voltage_rating_v = Column(Integer)
    num_conductors = Column(Integer)
    awg_kcmil = Column(String(20))
    shield = Column(Boolean, default=False)
    armor = Column(Boolean, default=False)
    ampacity_conduit_a = Column(Float)
    ampacity_tray_a = Column(Float)
    od_inches = Column(Float)
    weight_lbft = Column(Float)
    notes = Column(Text)

    cables = relationship("Cable", back_populates="catalog_entry")


class InstrumentCatalog(Base):
    __tablename__ = "instrument_catalog"

    instrument_catalog_id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer = Column(String(100))
    model = Column(String(100))
    description = Column(String(255))
    type = Column(Enum(InstrumentType), nullable=False)
    signal_type = Column(Enum(SignalType))
    supply_vdc = Column(Float)
    enclosure_nema = Column(String(20))
    hazardous_area_rating = Column(String(50))
    notes = Column(Text)

    instruments = relationship("Instrument", back_populates="catalog_entry")


class ConduitCatalog(Base):
    __tablename__ = "conduit_catalog"

    conduit_catalog_id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(ConduitType), nullable=False)
    trade_size_in = Column(Float)
    od_inches = Column(Float)
    id_inches = Column(Float)
    notes = Column(Text)

    conduits = relationship("Conduit", back_populates="catalog_entry")


# ---------------------------------------------------------------------------
# CLASS B — PROJECT TABLES
# ---------------------------------------------------------------------------

class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_number = Column(String(50), unique=True, nullable=False)
    project_name = Column(String(255), nullable=False)
    client = Column(String(255))
    location = Column(String(255))
    engineer_of_record = Column(String(100))
    issue_date = Column(Date)
    nec_edition = Column(String(10))
    voltage_system = Column(Enum(VoltageSystem))
    notes = Column(Text)

    locations = relationship("Location", back_populates="project", cascade="all, delete-orphan")
    equipment = relationship("Equipment", back_populates="project", cascade="all, delete-orphan")
    instruments = relationship("Instrument", back_populates="project", cascade="all, delete-orphan")
    cables = relationship("Cable", back_populates="project", cascade="all, delete-orphan")
    conduits = relationship("Conduit", back_populates="project", cascade="all, delete-orphan")
    panel_schedules = relationship("PanelSchedule", back_populates="project", cascade="all, delete-orphan")


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    location_tag = Column(String(50), nullable=False)
    building = Column(String(100))
    room = Column(String(100))
    elevation_ft = Column(Float)
    area_classification = Column(Enum(AreaClassification), default=AreaClassification.ORDINARY)
    nfpa_classification = Column(String(50))
    description = Column(String(255))
    notes = Column(Text)

    project = relationship("Project", back_populates="locations")
    equipment = relationship("Equipment", back_populates="location")
    instruments = relationship("Instrument", back_populates="location")


class Equipment(Base):
    __tablename__ = "equipment"

    equip_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    equip_catalog_id = Column(Integer, ForeignKey("equip_catalog.equip_catalog_id"))
    tag = Column(String(50), nullable=False)
    name = Column(String(255))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    bus_voltage_v = Column(Integer)
    rated_current_a = Column(Float)
    ic_rating_ka = Column(Float)
    fed_from_tag = Column(String(50))
    breaker_trip_a = Column(Float)
    breaker_frame_a = Column(Float)
    drawing_ref = Column(String(100))
    sheet_number = Column(String(50))
    one_line_ref = Column(String(100))
    status = Column(Enum(EquipStatus), default=EquipStatus.DESIGN)
    notes = Column(Text)

    project = relationship("Project", back_populates="equipment")
    catalog_entry = relationship("EquipCatalog", back_populates="equipment")
    location = relationship("Location", back_populates="equipment")
    panel_schedules = relationship(
        "PanelSchedule",
        foreign_keys="PanelSchedule.panel_equip_id",
        back_populates="panel_equip",
    )

    # Cable endpoints
    cables_from_equip = relationship(
        "Cable", foreign_keys="Cable.from_equipment_id", back_populates="from_equipment"
    )
    cables_to_equip = relationship(
        "Cable", foreign_keys="Cable.to_equipment_id", back_populates="to_equipment"
    )


class Instrument(Base):
    __tablename__ = "instruments"

    instrument_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    instrument_catalog_id = Column(Integer, ForeignKey("instrument_catalog.instrument_catalog_id"))
    tag = Column(String(50), nullable=False)
    service_description = Column(String(255))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    loop_number = Column(String(50))
    p_and_id_ref = Column(String(100))
    panel_tag = Column(String(50))
    signal_type = Column(Enum(SignalType))
    supply_source_tag = Column(String(50))
    drawing_ref = Column(String(100))
    sheet_number = Column(String(50))
    status = Column(Enum(EquipStatus), default=EquipStatus.DESIGN)
    notes = Column(Text)

    project = relationship("Project", back_populates="instruments")
    catalog_entry = relationship("InstrumentCatalog", back_populates="instruments")
    location = relationship("Location", back_populates="instruments")

    cables_from_instr = relationship(
        "Cable", foreign_keys="Cable.from_instrument_id", back_populates="from_instrument"
    )
    cables_to_instr = relationship(
        "Cable", foreign_keys="Cable.to_instrument_id", back_populates="to_instrument"
    )


class Cable(Base):
    """
    FROM-TO cable schedule.

    Each endpoint (from / to) is represented by two nullable FKs:
      - *_equipment_id  → equipment table
      - *_instrument_id → instruments table

    Exactly one of the two must be non-NULL per endpoint.
    The CHECK constraints enforce this at the database level.
    """
    __tablename__ = "cables"
    __table_args__ = (
        CheckConstraint(
            "(from_equipment_id IS NOT NULL) != (from_instrument_id IS NOT NULL)",
            name="ck_cables_from_endpoint",
        ),
        CheckConstraint(
            "(to_equipment_id IS NOT NULL) != (to_instrument_id IS NOT NULL)",
            name="ck_cables_to_endpoint",
        ),
    )

    cable_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    cable_catalog_id = Column(Integer, ForeignKey("cable_catalog.cable_catalog_id"))
    cable_tag = Column(String(50), nullable=False)
    service_description = Column(String(255))

    from_equipment_id = Column(Integer, ForeignKey("equipment.equip_id"), nullable=True)
    from_instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=True)
    from_terminal = Column(String(50))

    to_equipment_id = Column(Integer, ForeignKey("equipment.equip_id"), nullable=True)
    to_instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=True)
    to_terminal = Column(String(50))

    from_location_id = Column(Integer, ForeignKey("locations.location_id"))
    to_location_id = Column(Integer, ForeignKey("locations.location_id"))

    conduit_tag = Column(String(50))
    routing_description = Column(Text)
    length_ft = Column(Float)
    length_ft_actual = Column(Float)
    num_conductors_used = Column(Integer)
    conductor_size_awg_kcmil = Column(String(20))
    voltage_drop_pct = Column(Float)
    drawing_ref = Column(String(100))
    sheet_number = Column(String(50))
    status = Column(Enum(CableStatus), default=CableStatus.DESIGN)
    notes = Column(Text)

    project = relationship("Project", back_populates="cables")
    catalog_entry = relationship("CableCatalog", back_populates="cables")

    from_equipment = relationship("Equipment", foreign_keys=[from_equipment_id], back_populates="cables_from_equip")
    from_instrument = relationship("Instrument", foreign_keys=[from_instrument_id], back_populates="cables_from_instr")
    to_equipment = relationship("Equipment", foreign_keys=[to_equipment_id], back_populates="cables_to_equip")
    to_instrument = relationship("Instrument", foreign_keys=[to_instrument_id], back_populates="cables_to_instr")

    @property
    def from_tag(self) -> str:
        if self.from_equipment:
            return self.from_equipment.tag
        if self.from_instrument:
            return self.from_instrument.tag
        return ""

    @property
    def to_tag(self) -> str:
        if self.to_equipment:
            return self.to_equipment.tag
        if self.to_instrument:
            return self.to_instrument.tag
        return ""

    def calc_voltage_drop(self, voltage_v: float, current_a: float, r_ohm_per_kft: float, three_phase: bool = True) -> float:
        """
        Voltage drop per NEC methodology.
          single-phase: vd_pct = (2 * L * I * R) / (1000 * V) * 100
          three-phase:  vd_pct = (1.732 * L * I * R) / (1000 * V) * 100
        L in feet, R in ohm/1000ft.
        """
        if not self.length_ft or not current_a or not r_ohm_per_kft:
            return 0.0
        multiplier = 1.732 if three_phase else 2.0
        vd = (multiplier * self.length_ft * current_a * r_ohm_per_kft) / (1000.0 * voltage_v) * 100.0
        self.voltage_drop_pct = round(vd, 2)
        return self.voltage_drop_pct


class Conduit(Base):
    __tablename__ = "conduits"

    conduit_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    conduit_catalog_id = Column(Integer, ForeignKey("conduit_catalog.conduit_catalog_id"))
    conduit_tag = Column(String(50), nullable=False)
    from_location_id = Column(Integer, ForeignKey("locations.location_id"))
    to_location_id = Column(Integer, ForeignKey("locations.location_id"))
    length_ft = Column(Float)
    fill_pct = Column(Float)
    routing_description = Column(Text)
    drawing_ref = Column(String(100))
    notes = Column(Text)

    project = relationship("Project", back_populates="conduits")
    catalog_entry = relationship("ConduitCatalog", back_populates="conduits")


class PanelSchedule(Base):
    __tablename__ = "panel_schedules"

    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    panel_equip_id = Column(Integer, ForeignKey("equipment.equip_id"), nullable=False)
    circuit_number = Column(String(10), nullable=False)
    phase = Column(Enum(Phase))
    breaker_trip_a = Column(Float)
    breaker_poles = Column(Integer)
    load_equip_id = Column(Integer, ForeignKey("equipment.equip_id"), nullable=True)
    load_instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=True)
    load_description = Column(String(255))
    load_kva = Column(Float)
    load_kw = Column(Float)
    load_pf = Column(Float)
    notes = Column(Text)

    project = relationship("Project", back_populates="panel_schedules")
    panel_equip = relationship("Equipment", foreign_keys=[panel_equip_id], back_populates="panel_schedules")
    load_equip = relationship("Equipment", foreign_keys=[load_equip_id])
    load_instrument = relationship("Instrument", foreign_keys=[load_instrument_id])


def init_db():
    """Create all tables."""
    Base.metadata.create_all(engine)
