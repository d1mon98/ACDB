"""Schemas for catalog_column_defs and catalog_custom_rows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .common import ORMModel, make_optional


class ColumnDefCreate(ORMModel):
    col_name: str
    col_label: str
    col_type: str = "text"
    required: bool = False
    display_order: int = 0


class ColumnDefRead(ColumnDefCreate):
    id: int
    catalog_group_id: int
    created_at: datetime
    updated_at: datetime


ColumnDefUpdate = make_optional(ColumnDefCreate, "ColumnDefUpdate")


class CustomRowCreate(ORMModel):
    row_data: dict[str, Any]


class CustomRowRead(ORMModel):
    id: int
    catalog_group_id: int
    row_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime
