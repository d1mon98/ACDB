"""Request / response schemas for the Class A catalog tables."""

from __future__ import annotations

from datetime import datetime

from ..models.enums import (
    ConductorMaterial,
    DeviceCategory,
    EquipmentCategory,
    InstrumentType,
    IOType,
)
from .common import ORMModel, make_optional

# --------------------------------------------------------------------------
# catalog_manufacturers
# --------------------------------------------------------------------------


class ManufacturerCreate(ORMModel):
    catalog_group_id: int | None = None
    name: str
    abbreviation: str | None = None
    country: str | None = None
    notes: str | None = None


class ManufacturerRead(ManufacturerCreate):
    id: int
    created_at: datetime
    updated_at: datetime


ManufacturerUpdate = make_optional(ManufacturerCreate, "ManufacturerUpdate")


# --------------------------------------------------------------------------
# catalog_equipment
# --------------------------------------------------------------------------


class EquipmentCreate(ORMModel):
    catalog_group_id: int | None = None
    manufacturer_id: int | None = None
    category: EquipmentCategory
    model_series: str
    rated_voltage: str | None = None
    rated_current: str | None = None
    rated_kva: float | None = None
    sccr_rating: str | None = None
    enclosure_type: str | None = None
    poles: int | None = None
    phases: int | None = None
    description: str | None = None
    notes: str | None = None


class EquipmentRead(EquipmentCreate):
    id: int
    created_at: datetime
    updated_at: datetime


EquipmentUpdate = make_optional(EquipmentCreate, "EquipmentUpdate")


# --------------------------------------------------------------------------
# catalog_cables
# --------------------------------------------------------------------------


class CableCreate(ORMModel):
    catalog_group_id: int | None = None
    cable_type_code: str
    conductor_material: ConductorMaterial | None = None
    insulation_type: str | None = None
    voltage_rating: str | None = None
    conductor_count: int | None = None
    conductor_size: str | None = None
    ampacity: int | None = None
    shielded: bool = False
    armored: bool = False
    description: str | None = None
    notes: str | None = None


class CableRead(CableCreate):
    id: int
    created_at: datetime
    updated_at: datetime


CableUpdate = make_optional(CableCreate, "CableUpdate")


# --------------------------------------------------------------------------
# catalog_instruments
# --------------------------------------------------------------------------


class InstrumentCreate(ORMModel):
    catalog_group_id: int | None = None
    manufacturer_id: int | None = None
    instrument_type: InstrumentType
    measurement_principle: str | None = None
    model_series: str
    signal_type: str | None = None
    process_connection: str | None = None
    accuracy: str | None = None
    power_requirement: str | None = None
    area_classification: str | None = None
    description: str | None = None
    notes: str | None = None


class InstrumentRead(InstrumentCreate):
    id: int
    created_at: datetime
    updated_at: datetime


InstrumentUpdate = make_optional(InstrumentCreate, "InstrumentUpdate")


# --------------------------------------------------------------------------
# catalog_io_modules
# --------------------------------------------------------------------------


class IOModuleCreate(ORMModel):
    catalog_group_id: int | None = None
    manufacturer_id: int | None = None
    module_model: str
    io_type: IOType
    point_count: int | None = None
    signal_range: str | None = None
    description: str | None = None
    notes: str | None = None


class IOModuleRead(IOModuleCreate):
    id: int
    created_at: datetime
    updated_at: datetime


IOModuleUpdate = make_optional(IOModuleCreate, "IOModuleUpdate")


# --------------------------------------------------------------------------
# catalog_devices
# --------------------------------------------------------------------------


class DeviceCreate(ORMModel):
    catalog_group_id: int | None = None
    manufacturer_id: int | None = None
    device_category: DeviceCategory
    model: str
    ratings: str | None = None
    description: str | None = None
    notes: str | None = None


class DeviceRead(DeviceCreate):
    id: int
    created_at: datetime
    updated_at: datetime


DeviceUpdate = make_optional(DeviceCreate, "DeviceUpdate")
