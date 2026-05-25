"""Hierarchical catalog group model.

Provides unlimited nesting via a self-referential parent_group_id foreign key.
Groups organise all catalog tables into a 10-category tree.  The optional
``linked_table`` field names the existing complex catalog table (e.g.
``catalog_manufacturers``) whose rows are presented as the items for that leaf
group; groups without ``linked_table`` own rows in the generic catalog tables.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .base import CommonMixin


class CatalogGroup(Base, CommonMixin):
    """One node in the catalog group hierarchy."""

    __tablename__ = "catalog_groups"

    parent_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_groups.id", ondelete="RESTRICT"), index=True
    )
    group_name: Mapped[str] = mapped_column(String(200), nullable=False)
    group_code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # When set, names the existing complex catalog table whose items live in that
    # table rather than in the generic catalog_ext_* tables.
    linked_table: Mapped[str | None] = mapped_column(String(100))
