"""Dynamic schema for user-created catalog groups.

catalog_column_defs  -- the column names/types the user defines for a group
catalog_custom_rows  -- actual data rows stored as a JSON blob per column set
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .base import CommonMixin


class CatalogColumnDef(Base, CommonMixin):
    """One user-defined column for a custom catalog group."""

    __tablename__ = "catalog_column_defs"

    catalog_group_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_groups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    col_name: Mapped[str] = mapped_column(String(100), nullable=False)
    col_label: Mapped[str] = mapped_column(String(200), nullable=False)
    # Allowed: text | textarea | number | bool
    col_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CatalogCustomRow(Base, CommonMixin):
    """One data row in a custom catalog group (values stored as JSON)."""

    __tablename__ = "catalog_custom_rows"

    catalog_group_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_groups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    row_data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
