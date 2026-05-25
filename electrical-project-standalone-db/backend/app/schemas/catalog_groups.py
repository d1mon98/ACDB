"""Schemas for catalog_groups and the generic extended catalog item tables."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .common import ORMModel, make_optional


# ---------------------------------------------------------------------------
# catalog_groups
# ---------------------------------------------------------------------------

class CatalogGroupCreate(ORMModel):
    parent_group_id: int | None = None
    group_name: str
    group_code: str
    description: str | None = None
    display_order: int = 0
    is_active: bool = True
    linked_table: str | None = None
    notes: str | None = None


class CatalogGroupRead(CatalogGroupCreate):
    id: int
    created_at: datetime
    updated_at: datetime


CatalogGroupUpdate = make_optional(CatalogGroupCreate, "CatalogGroupUpdate")


class CatalogGroupTree(ORMModel):
    """Nested tree representation used by the /tree endpoint."""
    id: int
    group_name: str
    group_code: str
    description: str | None = None
    display_order: int
    is_active: bool
    linked_table: str | None = None
    children: list[Any] = []    # list[CatalogGroupTree] -- forward ref resolved at runtime


CatalogGroupTree.model_rebuild()


# ---------------------------------------------------------------------------
# Generic extended catalog item (used by all cat_* simple tables)
# ---------------------------------------------------------------------------

class CatalogItemCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    description: str | None = None
    is_active: bool = True
    notes: str | None = None


class CatalogItemRead(CatalogItemCreate):
    id: int
    created_at: datetime
    updated_at: datetime


CatalogItemUpdate = make_optional(CatalogItemCreate, "CatalogItemUpdate")


# ---------------------------------------------------------------------------
# Power Systems catalog (cat_power_systems) -- extended columns
# ---------------------------------------------------------------------------

class PowerSystemCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    nominal_voltage: str | None = None
    phases: int | None = None
    frequency_hz: float | None = None
    wires: int | None = None
    system_config: str | None = None
    voltage_class: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None


class PowerSystemRead(PowerSystemCreate):
    id: int
    created_at: datetime
    updated_at: datetime


PowerSystemUpdate = make_optional(PowerSystemCreate, "PowerSystemUpdate")


# ---------------------------------------------------------------------------
# Wire Types catalog (cat_wire_types) -- extended columns
# ---------------------------------------------------------------------------

class WireTypeCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    voltage_rating: str | None = None
    temperature_rating: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None


class WireTypeRead(WireTypeCreate):
    id: int
    created_at: datetime
    updated_at: datetime


WireTypeUpdate = make_optional(WireTypeCreate, "WireTypeUpdate")


# ---------------------------------------------------------------------------
# Distribution Equipment extended schemas
# ---------------------------------------------------------------------------

def _dist_read(name: str, create_cls):
    read_cls = type(f"{name}Read", (create_cls,), {"__annotations__": {"id": int, "created_at": datetime, "updated_at": datetime}})
    read_cls.__bases__ = (create_cls,)
    return read_cls


class SwitchgearCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    rated_voltage: str | None = None
    rated_current: str | None = None
    sccr_rating: str | None = None
    phases: int | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class SwitchgearRead(SwitchgearCreate):
    id: int; created_at: datetime; updated_at: datetime

SwitchgearUpdate = make_optional(SwitchgearCreate, "SwitchgearUpdate")


class SwitchboardCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    rated_voltage: str | None = None
    rated_current: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class SwitchboardRead(SwitchboardCreate):
    id: int; created_at: datetime; updated_at: datetime

SwitchboardUpdate = make_optional(SwitchboardCreate, "SwitchboardUpdate")


class MCCCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    rated_voltage: str | None = None
    bus_rating: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class MCCRead(MCCCreate):
    id: int; created_at: datetime; updated_at: datetime

MCCUpdate = make_optional(MCCCreate, "MCCUpdate")


class PanelboardCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    rated_voltage: str | None = None
    rated_current: str | None = None
    poles: int | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class PanelboardRead(PanelboardCreate):
    id: int; created_at: datetime; updated_at: datetime

PanelboardUpdate = make_optional(PanelboardCreate, "PanelboardUpdate")


class TransformerCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    kva_rating: float | None = None
    primary_voltage: str | None = None
    primary_current_a: float | None = None
    secondary_voltage: str | None = None
    secondary_current_a: float | None = None
    winding_config: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class TransformerRead(TransformerCreate):
    id: int; created_at: datetime; updated_at: datetime

TransformerUpdate = make_optional(TransformerCreate, "TransformerUpdate")


class ATSCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    rated_voltage: str | None = None
    rated_current: str | None = None
    poles: int | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class ATSRead(ATSCreate):
    id: int; created_at: datetime; updated_at: datetime

ATSUpdate = make_optional(ATSCreate, "ATSUpdate")


class GeneratorCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    rated_kw: float | None = None
    rated_kva: float | None = None
    rated_voltage: str | None = None
    fuel_type: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class GeneratorRead(GeneratorCreate):
    id: int; created_at: datetime; updated_at: datetime

GeneratorUpdate = make_optional(GeneratorCreate, "GeneratorUpdate")


class UPSCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    rated_kva: float | None = None
    battery_runtime_min: int | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class UPSRead(UPSCreate):
    id: int; created_at: datetime; updated_at: datetime

UPSUpdate = make_optional(UPSCreate, "UPSUpdate")


class DisconnectSwitchCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    amp_rating: str | None = None
    voltage_rating: str | None = None
    fusible: bool = False
    poles: int | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class DisconnectSwitchRead(DisconnectSwitchCreate):
    id: int; created_at: datetime; updated_at: datetime

DisconnectSwitchUpdate = make_optional(DisconnectSwitchCreate, "DisconnectSwitchUpdate")


class BusDuctCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    rated_voltage: str | None = None
    rated_current: int | None = None
    phases: int | None = None
    bus_type: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class BusDuctRead(BusDuctCreate):
    id: int; created_at: datetime; updated_at: datetime

BusDuctUpdate = make_optional(BusDuctCreate, "BusDuctUpdate")


class MeteringEquipmentCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    meter_class: str | None = None
    measurement_type: str | None = None
    accuracy_class: str | None = None
    voltage_rating: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class MeteringEquipmentRead(MeteringEquipmentCreate):
    id: int; created_at: datetime; updated_at: datetime

MeteringEquipmentUpdate = make_optional(MeteringEquipmentCreate, "MeteringEquipmentUpdate")


class CapacitorBankCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    voltage_rating: str | None = None
    kvar_rating: float | None = None
    phases: int | None = None
    connection_type: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class CapacitorBankRead(CapacitorBankCreate):
    id: int; created_at: datetime; updated_at: datetime

CapacitorBankUpdate = make_optional(CapacitorBankCreate, "CapacitorBankUpdate")


class PDUCreate(ORMModel):
    catalog_group_id: int | None = None
    code: str
    name: str
    input_voltage: str | None = None
    output_voltage: str | None = None
    capacity_kva: float | None = None
    outlet_type: str | None = None
    description: str | None = None
    is_active: bool = True
    notes: str | None = None

class PDURead(PDUCreate):
    id: int; created_at: datetime; updated_at: datetime

PDUUpdate = make_optional(PDUCreate, "PDUUpdate")
