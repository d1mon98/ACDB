"""Class A -- General Catalog tables.

Catalog tables hold standardized, project-independent reference data: the
library of manufacturer equipment, standard cable types, instrument models and
so on.  They are seeded once and reused across every project.  A catalog row is
the *single source of truth* for the permanent attributes of the thing it
describes; project tables (Class B) reference these rows rather than copying
their fields.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .base import CommonMixin
from .enums import (
    ConductorMaterial,
    DeviceCategory,
    EquipmentCategory,
    InstrumentType,
    IOType,
)


class CatalogManufacturer(Base, CommonMixin):
    """Manufacturer / vendor library entry."""

    __tablename__ = "catalog_manufacturers"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    abbreviation: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(60))


class CatalogEquipment(Base, CommonMixin):
    """Standard power-distribution equipment model.

    Covers switchgear, panelboards, MCCs, transformers, VFDs, ATSs and
    disconnects -- the ``category`` column distinguishes them.
    """

    __tablename__ = "catalog_equipment"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="RESTRICT")
    )
    category: Mapped[EquipmentCategory] = mapped_column(
        Enum(EquipmentCategory, native_enum=False), nullable=False
    )
    model_series: Mapped[str] = mapped_column(String(120), nullable=False)
    rated_voltage: Mapped[str | None] = mapped_column(String(40))
    rated_current: Mapped[str | None] = mapped_column(String(40))
    rated_kva: Mapped[float | None] = mapped_column(Float)
    sccr_rating: Mapped[str | None] = mapped_column(String(40))  # short-circuit / AIC
    enclosure_type: Mapped[str | None] = mapped_column(String(40))  # NEMA type
    poles: Mapped[int | None] = mapped_column(Integer)
    phases: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)


class CatalogCable(Base, CommonMixin):
    """Standard cable / conductor type."""

    __tablename__ = "catalog_cables"

    cable_type_code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    conductor_material: Mapped[ConductorMaterial | None] = mapped_column(
        Enum(ConductorMaterial, native_enum=False)
    )
    insulation_type: Mapped[str | None] = mapped_column(String(40))  # THHN / XHHW / ...
    voltage_rating: Mapped[str | None] = mapped_column(String(40))
    conductor_count: Mapped[int | None] = mapped_column(Integer)
    conductor_size: Mapped[str | None] = mapped_column(String(40))  # AWG / kcmil
    ampacity: Mapped[int | None] = mapped_column(Integer)
    shielded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    armored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text)


class CatalogInstrument(Base, CommonMixin):
    """Standard field instrument model."""

    __tablename__ = "catalog_instruments"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="RESTRICT")
    )
    instrument_type: Mapped[InstrumentType] = mapped_column(
        Enum(InstrumentType, native_enum=False), nullable=False
    )
    measurement_principle: Mapped[str | None] = mapped_column(String(80))
    model_series: Mapped[str] = mapped_column(String(120), nullable=False)
    signal_type: Mapped[str | None] = mapped_column(String(40))  # 4-20mA / HART / RTD...
    process_connection: Mapped[str | None] = mapped_column(String(60))
    accuracy: Mapped[str | None] = mapped_column(String(60))
    power_requirement: Mapped[str | None] = mapped_column(String(60))
    area_classification: Mapped[str | None] = mapped_column(String(60))
    description: Mapped[str | None] = mapped_column(Text)


class CatalogIOModule(Base, CommonMixin):
    """Standard PLC / RIO I/O module."""

    __tablename__ = "catalog_io_modules"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="RESTRICT")
    )
    module_model: Mapped[str] = mapped_column(String(120), nullable=False)
    io_type: Mapped[IOType] = mapped_column(
        Enum(IOType, native_enum=False), nullable=False
    )
    point_count: Mapped[int | None] = mapped_column(Integer)
    signal_range: Mapped[str | None] = mapped_column(String(60))
    description: Mapped[str | None] = mapped_column(Text)


class CatalogDevice(Base, CommonMixin):
    """Standard control / protection device for control panels."""

    __tablename__ = "catalog_devices"

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_manufacturers.id", ondelete="RESTRICT")
    )
    device_category: Mapped[DeviceCategory] = mapped_column(
        Enum(DeviceCategory, native_enum=False), nullable=False
    )
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    ratings: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
