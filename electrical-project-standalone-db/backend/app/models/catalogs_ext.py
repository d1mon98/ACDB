"""Extended catalog tables -- Group 1 through 10.

Each class maps to one leaf catalog table in the hierarchy.  All share the same
minimal structure via CatalogItemMixin: a group reference, a unique code, a
display name, a description, and an is_active flag.  The six original complex
catalog tables (catalog_manufacturers etc.) keep their own richer schemas and
only gain a catalog_group_id column (see catalogs.py).
"""

from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .base import CommonMixin


class CatalogItemMixin:
    """Columns shared by every simple catalog item table."""

    catalog_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_groups.id", ondelete="SET NULL"), index=True
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# =============================================================================
# Group 1 -- Electrical Power Systems
# =============================================================================

class PowerSystemCatalog(Base, CatalogItemMixin, CommonMixin):
    """US standard electrical power system configurations."""
    __tablename__ = "cat_power_systems"

    nominal_voltage: Mapped[str | None] = mapped_column(String(40))
    frequency_hz:    Mapped[float | None] = mapped_column(Float)
    phases:          Mapped[int | None] = mapped_column(Integer)
    wires:           Mapped[int | None] = mapped_column(Integer)
    system_config:   Mapped[str | None] = mapped_column(String(40))
    voltage_class:   Mapped[str | None] = mapped_column(String(40))


class VoltageClassCatalog(Base, CatalogItemMixin, CommonMixin):
    """Standard voltage class definitions (LV / MV / HV)."""
    __tablename__ = "cat_voltage_classes"

    voltage_value: Mapped[str | None] = mapped_column(String(40))   # e.g. "480V"
    voltage_range: Mapped[str | None] = mapped_column(String(80))   # e.g. "> 1 kV ≤ 35 kV"


class GroundingTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """System grounding configurations (solidly grounded, high-resistance, etc.)."""
    __tablename__ = "cat_grounding_types"


class PhaseWireConfigCatalog(Base, CatalogItemMixin, CommonMixin):
    """Phase/wire configurations (3Φ 4W, 1Φ 2W, etc.)."""
    __tablename__ = "cat_phase_wire_configs"

    phase_count: Mapped[int | None] = mapped_column(Integer)
    wire_count: Mapped[int | None] = mapped_column(Integer)


# =============================================================================
# Group 2 -- Electrical Equipment (general)
# =============================================================================

class EquipmentTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Top-level equipment type classifications."""
    __tablename__ = "cat_equipment_types"


class EquipmentModelCatalog(Base, CatalogItemMixin, CommonMixin):
    """Specific equipment model entries (alternative to the richer catalog_equipment)."""
    __tablename__ = "cat_equipment_models"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    equipment_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("cat_equipment_types.id", ondelete="SET NULL")
    )
    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    rated_current: Mapped[str | None] = mapped_column(String(40))


class EnclosureCatalog(Base, CatalogItemMixin, CommonMixin):
    """Enclosure type standards (NEMA, IP, etc.)."""
    __tablename__ = "cat_enclosures"

    standard: Mapped[str | None] = mapped_column(String(40))  # NEMA / IEC / UL
    ip_rating: Mapped[str | None] = mapped_column(String(20))


class MountingTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Mounting method standards (DIN rail, panel, floor-standing, etc.)."""
    __tablename__ = "cat_mounting_types"


# =============================================================================
# Group 3 -- Distribution Equipment
# =============================================================================

class SwitchgearCatalog(Base, CatalogItemMixin, CommonMixin):
    """Switchgear model catalog."""
    __tablename__ = "cat_switchgear"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    rated_current: Mapped[str | None] = mapped_column(String(40))
    sccr_rating: Mapped[str | None] = mapped_column(String(40))
    phases: Mapped[int | None] = mapped_column(Integer)


class SwitchboardCatalog(Base, CatalogItemMixin, CommonMixin):
    """Switchboard model catalog."""
    __tablename__ = "cat_switchboards"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    rated_current: Mapped[str | None] = mapped_column(String(40))


class MCCCatalog(Base, CatalogItemMixin, CommonMixin):
    """Motor control center model catalog."""
    __tablename__ = "cat_mccs"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    bus_rating: Mapped[str | None] = mapped_column(String(40))


class PanelboardCatalog(Base, CatalogItemMixin, CommonMixin):
    """Panelboard model catalog."""
    __tablename__ = "cat_panelboards"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    rated_current: Mapped[str | None] = mapped_column(String(40))
    poles: Mapped[int | None] = mapped_column(Integer)


class TransformerCatalog(Base, CatalogItemMixin, CommonMixin):
    """Transformer model catalog."""
    __tablename__ = "cat_transformers"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    kva_rating: Mapped[float | None] = mapped_column(Float)
    primary_voltage: Mapped[str | None] = mapped_column(String(40))
    secondary_voltage: Mapped[str | None] = mapped_column(String(40))
    winding_config: Mapped[str | None] = mapped_column(String(40))
    primary_current_a: Mapped[float | None] = mapped_column(Float)    # FLA, 3-phase kVA*1000/(V*√3)
    secondary_current_a: Mapped[float | None] = mapped_column(Float)


class ATSCatalog(Base, CatalogItemMixin, CommonMixin):
    """Automatic transfer switch model catalog."""
    __tablename__ = "cat_ats"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    rated_current: Mapped[str | None] = mapped_column(String(40))
    poles: Mapped[int | None] = mapped_column(Integer)


class GeneratorCatalog(Base, CatalogItemMixin, CommonMixin):
    """Generator set model catalog."""
    __tablename__ = "cat_generators"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    rated_kw: Mapped[float | None] = mapped_column(Float)
    rated_kva: Mapped[float | None] = mapped_column(Float)
    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    fuel_type: Mapped[str | None] = mapped_column(String(40))


class UPSCatalog(Base, CatalogItemMixin, CommonMixin):
    """Uninterruptible power supply model catalog."""
    __tablename__ = "cat_ups"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    rated_kva: Mapped[float | None] = mapped_column(Float)
    battery_runtime_min: Mapped[int | None] = mapped_column(Integer)


class BusDuctCatalog(Base, CatalogItemMixin, CommonMixin):
    """Bus duct / busway catalog."""
    __tablename__ = "cat_bus_ducts"

    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    rated_current: Mapped[int | None] = mapped_column(Integer)   # amps
    phases: Mapped[int | None] = mapped_column(Integer)
    bus_type: Mapped[str | None] = mapped_column(String(40))     # Feeder / Plug-In / Lighting


class MeteringEquipmentCatalog(Base, CatalogItemMixin, CommonMixin):
    """Revenue and check metering equipment catalog."""
    __tablename__ = "cat_meters"

    meter_class: Mapped[str | None] = mapped_column(String(40))       # Revenue / Check / PQ
    measurement_type: Mapped[str | None] = mapped_column(String(60))  # kWh / kW+kVAR / PQ
    accuracy_class: Mapped[str | None] = mapped_column(String(20))    # 0.2S / 0.5S / 1.0
    voltage_rating: Mapped[str | None] = mapped_column(String(40))


class CapacitorBankCatalog(Base, CatalogItemMixin, CommonMixin):
    """Power factor correction / capacitor bank catalog."""
    __tablename__ = "cat_capacitor_banks"

    voltage_rating: Mapped[str | None] = mapped_column(String(40))
    kvar_rating: Mapped[float | None] = mapped_column(Float)
    phases: Mapped[int | None] = mapped_column(Integer)
    connection_type: Mapped[str | None] = mapped_column(String(20))   # Wye / Delta


class PowerDistributionUnitCatalog(Base, CatalogItemMixin, CommonMixin):
    """Power distribution unit (PDU) catalog — data center / critical power."""
    __tablename__ = "cat_pdus"

    input_voltage: Mapped[str | None] = mapped_column(String(40))
    output_voltage: Mapped[str | None] = mapped_column(String(40))
    capacity_kva: Mapped[float | None] = mapped_column(Float)
    outlet_type: Mapped[str | None] = mapped_column(String(60))


# =============================================================================
# Group 4 -- Protection and Control Devices
# =============================================================================

class BreakerCatalog(Base, CatalogItemMixin, CommonMixin):
    """Circuit breaker model catalog."""
    __tablename__ = "cat_breakers"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    frame_rating: Mapped[str | None] = mapped_column(String(40))
    trip_rating: Mapped[str | None] = mapped_column(String(40))
    interrupt_rating: Mapped[str | None] = mapped_column(String(40))
    poles: Mapped[int | None] = mapped_column(Integer)
    voltage_rating: Mapped[str | None] = mapped_column(String(40))


class FuseCatalog(Base, CatalogItemMixin, CommonMixin):
    """Fuse model catalog."""
    __tablename__ = "cat_fuses"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    amp_rating: Mapped[str | None] = mapped_column(String(40))
    voltage_rating: Mapped[str | None] = mapped_column(String(40))
    class_type: Mapped[str | None] = mapped_column(String(20))  # Class J, CC, etc.
    interrupt_rating: Mapped[str | None] = mapped_column(String(40))


class RelayCatalog(Base, CatalogItemMixin, CommonMixin):
    """Protective relay model catalog."""
    __tablename__ = "cat_relays"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    relay_type: Mapped[str | None] = mapped_column(String(60))  # overcurrent / differential
    coil_voltage: Mapped[str | None] = mapped_column(String(40))
    contact_config: Mapped[str | None] = mapped_column(String(40))  # SPDT / DPDT


class OverloadCatalog(Base, CatalogItemMixin, CommonMixin):
    """Thermal / electronic overload relay model catalog."""
    __tablename__ = "cat_overloads"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    amp_range: Mapped[str | None] = mapped_column(String(40))


class DisconnectSwitchCatalog(Base, CatalogItemMixin, CommonMixin):
    """Disconnect switch / fusible switch model catalog."""
    __tablename__ = "cat_disconnect_switches"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    amp_rating: Mapped[str | None] = mapped_column(String(40))
    voltage_rating: Mapped[str | None] = mapped_column(String(40))
    fusible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    poles: Mapped[int | None] = mapped_column(Integer)


class SoftStarterCatalog(Base, CatalogItemMixin, CommonMixin):
    """Soft starter model catalog."""
    __tablename__ = "cat_soft_starters"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    hp_rating: Mapped[str | None] = mapped_column(String(40))
    amp_rating: Mapped[str | None] = mapped_column(String(40))
    voltage_rating: Mapped[str | None] = mapped_column(String(40))


class VFDCatalog(Base, CatalogItemMixin, CommonMixin):
    """Variable frequency drive model catalog."""
    __tablename__ = "cat_vfds"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    hp_rating: Mapped[str | None] = mapped_column(String(40))
    amp_rating: Mapped[str | None] = mapped_column(String(40))
    voltage_rating: Mapped[str | None] = mapped_column(String(40))


# =============================================================================
# Group 5 -- Cable and Raceway
# =============================================================================

class ConduitTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Conduit type catalog (EMT, IMC, RMC, PVC, etc.)."""
    __tablename__ = "cat_conduit_types"

    material: Mapped[str | None] = mapped_column(String(40))
    trade_size: Mapped[str | None] = mapped_column(String(40))


class CableTrayCatalog(Base, CatalogItemMixin, CommonMixin):
    """Cable tray type catalog."""
    __tablename__ = "cat_cable_trays"

    material: Mapped[str | None] = mapped_column(String(40))  # steel / aluminum / FRP
    width_in: Mapped[str | None] = mapped_column(String(20))
    depth_in: Mapped[str | None] = mapped_column(String(20))


class WireTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Wire type catalog (THHN, XHHW, USE-2, etc.)."""
    __tablename__ = "cat_wire_types"

    voltage_rating: Mapped[str | None] = mapped_column(String(40))
    temperature_rating: Mapped[str | None] = mapped_column(String(20))  # 60 / 75 / 90 °C


class CableInsulationCatalog(Base, CatalogItemMixin, CommonMixin):
    """Cable insulation material catalog."""
    __tablename__ = "cat_cable_insulations"

    material: Mapped[str | None] = mapped_column(String(60))
    voltage_rating: Mapped[str | None] = mapped_column(String(40))
    temperature_rating: Mapped[str | None] = mapped_column(String(20))


class ConductorMaterialCatalog(Base, CatalogItemMixin, CommonMixin):
    """Conductor material catalog (copper / aluminum / CCA)."""
    __tablename__ = "cat_conductor_materials"

    resistivity: Mapped[str | None] = mapped_column(String(60))


# =============================================================================
# Group 6 -- Instrumentation
# =============================================================================

class InstrumentModelCatalog(Base, CatalogItemMixin, CommonMixin):
    """Specific instrument models (complements catalog_instruments)."""
    __tablename__ = "cat_instrument_models"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    instrument_type: Mapped[str | None] = mapped_column(String(60))
    signal_type: Mapped[str | None] = mapped_column(String(40))
    accuracy: Mapped[str | None] = mapped_column(String(60))


class SignalTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Instrumentation signal type catalog (4-20mA, HART, Modbus, etc.)."""
    __tablename__ = "cat_signal_types"

    signal_range: Mapped[str | None] = mapped_column(String(60))
    protocol: Mapped[str | None] = mapped_column(String(60))


class MeasurementTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Measurement variable type catalog (Flow, Level, Pressure, Temp, etc.)."""
    __tablename__ = "cat_measurement_types"

    unit_of_measure: Mapped[str | None] = mapped_column(String(40))


class ProcessConnectionCatalog(Base, CatalogItemMixin, CommonMixin):
    """Process connection style catalog (NPT, flanged, tri-clamp, etc.)."""
    __tablename__ = "cat_process_connections"

    connection_size: Mapped[str | None] = mapped_column(String(40))
    connection_standard: Mapped[str | None] = mapped_column(String(40))  # ANSI / DIN


# =============================================================================
# Group 7 -- Controls and Automation
# =============================================================================

class PLCCatalog(Base, CatalogItemMixin, CommonMixin):
    """PLC / controller platform catalog."""
    __tablename__ = "cat_plcs"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    processor_model: Mapped[str | None] = mapped_column(String(120))
    memory_kb: Mapped[int | None] = mapped_column(Integer)
    communication_ports: Mapped[str | None] = mapped_column(String(120))


class PLCIOCatalog(Base, CatalogItemMixin, CommonMixin):
    """PLC I/O module catalog (complements catalog_io_modules)."""
    __tablename__ = "cat_plc_io"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    io_type: Mapped[str | None] = mapped_column(String(20))  # AI / AO / DI / DO
    point_count: Mapped[int | None] = mapped_column(Integer)
    signal_range: Mapped[str | None] = mapped_column(String(60))


class SCADACatalog(Base, CatalogItemMixin, CommonMixin):
    """SCADA / HMI platform catalog."""
    __tablename__ = "cat_scada"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    platform_type: Mapped[str | None] = mapped_column(String(60))  # SCADA / HMI / DCS


class NetworkDeviceCatalog(Base, CatalogItemMixin, CommonMixin):
    """Network device model catalog (switches, routers, gateways)."""
    __tablename__ = "cat_network_devices"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="SET NULL")
    )
    device_type: Mapped[str | None] = mapped_column(String(60))
    port_count: Mapped[int | None] = mapped_column(Integer)


class CommunicationProtocolCatalog(Base, CatalogItemMixin, CommonMixin):
    """Communication protocol catalog (Modbus, EtherNet/IP, PROFIBUS, etc.)."""
    __tablename__ = "cat_comm_protocols"

    layer: Mapped[str | None] = mapped_column(String(40))  # Physical / Network / Application
    medium: Mapped[str | None] = mapped_column(String(40))  # serial / ethernet / wireless


# =============================================================================
# Group 8 -- Locations and Classification
# =============================================================================

class AreaTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Area type catalog (process, electrical, control, utility, etc.)."""
    __tablename__ = "cat_area_types"


class RoomTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Room type catalog (control room, switchgear room, battery room, etc.)."""
    __tablename__ = "cat_room_types"


class HazardousAreaCatalog(Base, CatalogItemMixin, CommonMixin):
    """Hazardous area classification catalog (NEC / IEC)."""
    __tablename__ = "cat_hazardous_areas"

    classification_standard: Mapped[str | None] = mapped_column(String(40))  # NEC / ATEX / IEC
    class_division: Mapped[str | None] = mapped_column(String(40))   # Class I Div 1
    group: Mapped[str | None] = mapped_column(String(20))


class EnvironmentalRatingCatalog(Base, CatalogItemMixin, CommonMixin):
    """Environmental protection rating catalog (NEMA types, IP ratings)."""
    __tablename__ = "cat_environmental_ratings"

    standard: Mapped[str | None] = mapped_column(String(40))
    ip_equivalent: Mapped[str | None] = mapped_column(String(20))


# =============================================================================
# Group 9 -- Drawings and Documents
# =============================================================================

class DrawingTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Drawing type catalog (one-line, loop, layout, schematic, etc.)."""
    __tablename__ = "cat_drawing_types"

    discipline: Mapped[str | None] = mapped_column(String(40))


class RevisionStatusCatalog(Base, CatalogItemMixin, CommonMixin):
    """Drawing revision status catalog (IFC, IFR, ISSUED, etc.)."""
    __tablename__ = "cat_revision_statuses"

    is_issued: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class DocumentTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Document type catalog (specification, datasheet, report, etc.)."""
    __tablename__ = "cat_document_types"

    discipline: Mapped[str | None] = mapped_column(String(40))


class SubmittalStatusCatalog(Base, CatalogItemMixin, CommonMixin):
    """Submittal status catalog (pending, approved, rejected, revise-resubmit)."""
    __tablename__ = "cat_submittal_statuses"


# =============================================================================
# Group 10 -- Construction and Installation
# =============================================================================

class InstallationMethodCatalog(Base, CatalogItemMixin, CommonMixin):
    """Installation method catalog (direct-buried, in conduit, cable tray, etc.)."""
    __tablename__ = "cat_installation_methods"

    nec_article: Mapped[str | None] = mapped_column(String(40))


class MountingDetailCatalog(Base, CatalogItemMixin, CommonMixin):
    """Mounting detail catalog (wall-mount, floor-mount, ceiling-mount, etc.)."""
    __tablename__ = "cat_mounting_details"


class ConduitRoutingCatalog(Base, CatalogItemMixin, CommonMixin):
    """Conduit routing method catalog (exposed, concealed, underground, etc.)."""
    __tablename__ = "cat_conduit_routing"


class TerminationTypeCatalog(Base, CatalogItemMixin, CommonMixin):
    """Termination type catalog (lug, terminal block, wire nut, compression, etc.)."""
    __tablename__ = "cat_termination_types"

    compatible_wire_range: Mapped[str | None] = mapped_column(String(60))


# ---------------------------------------------------------------------------
# Convenience list for iterating over all new catalog model classes.
# ---------------------------------------------------------------------------

ALL_EXT_CATALOGS: list[type] = [
    PowerSystemCatalog,
    VoltageClassCatalog,
    GroundingTypeCatalog,
    PhaseWireConfigCatalog,
    EquipmentTypeCatalog,
    EquipmentModelCatalog,
    EnclosureCatalog,
    MountingTypeCatalog,
    SwitchgearCatalog,
    SwitchboardCatalog,
    MCCCatalog,
    PanelboardCatalog,
    TransformerCatalog,
    ATSCatalog,
    GeneratorCatalog,
    UPSCatalog,
    BusDuctCatalog,
    MeteringEquipmentCatalog,
    CapacitorBankCatalog,
    PowerDistributionUnitCatalog,
    BreakerCatalog,
    FuseCatalog,
    RelayCatalog,
    OverloadCatalog,
    DisconnectSwitchCatalog,
    SoftStarterCatalog,
    VFDCatalog,
    ConduitTypeCatalog,
    CableTrayCatalog,
    WireTypeCatalog,
    CableInsulationCatalog,
    ConductorMaterialCatalog,
    InstrumentModelCatalog,
    SignalTypeCatalog,
    MeasurementTypeCatalog,
    ProcessConnectionCatalog,
    PLCCatalog,
    PLCIOCatalog,
    SCADACatalog,
    NetworkDeviceCatalog,
    CommunicationProtocolCatalog,
    AreaTypeCatalog,
    RoomTypeCatalog,
    HazardousAreaCatalog,
    EnvironmentalRatingCatalog,
    DrawingTypeCatalog,
    RevisionStatusCatalog,
    DocumentTypeCatalog,
    SubmittalStatusCatalog,
    InstallationMethodCatalog,
    MountingDetailCatalog,
    ConduitRoutingCatalog,
    TerminationTypeCatalog,
]
