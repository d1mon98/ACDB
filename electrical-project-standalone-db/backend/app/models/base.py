"""Shared column mixin.

Every table in the schema -- Class A catalogs and Class B project tables alike
-- carries the same four bookkeeping columns.  Defining them once keeps the
model modules focused on what is genuinely table-specific.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column


class CommonMixin:
    """``id`` / ``notes`` / ``created_at`` / ``updated_at`` for every table."""

    # Surrogate primary key.  Integer keys keep cross-table foreign keys cheap
    # and are portable to PostgreSQL (where they become a serial/identity).
    id: Mapped[int] = mapped_column(primary_key=True)

    # Free-text remarks.  Present on every table by project convention.
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    # Row bookkeeping.  ``server_default``/``onupdate`` use the database clock so
    # values are correct even for rows inserted outside the API (e.g. the seed
    # script or a future bulk import).
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
