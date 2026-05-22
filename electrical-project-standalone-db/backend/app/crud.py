"""Generic CRUD helpers.

Every table shares the same five operations, so they are written once here and
parametrised by model.  The only table-aware behaviour is:

* ``list_items`` applies a ``project_id`` filter when the model actually has
  that column (all Class B tables do; Class A catalogs do not), and supports a
  free-text ``search`` across the model's string columns plus column ``sort``;
* callers may request eager-loading of the ``catalog`` relationship for the
  merged-view endpoints.

Integrity errors are rolled back and re-raised so the caller / global handler
can turn them into a clean HTTP response.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import String, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, Session, selectinload


def list_items(
    db: Session,
    model: type,
    *,
    skip: int = 0,
    limit: int = 100,
    project_id: int | None = None,
    eager: list[InstrumentedAttribute] | None = None,
    search: str | None = None,
    sort: str | None = None,
    order: str = "asc",
) -> tuple[list[Any], int]:
    """Return ``(rows, total)`` for a paginated, filtered, sorted list.

    ``search`` matches (case-insensitively) against every string column of the
    model.  ``sort`` must be a real column name or it is ignored (which also
    makes it safe against injection); ``order`` is ``asc`` or ``desc``.
    """
    base = select(model)

    if project_id is not None and hasattr(model, "project_id"):
        base = base.where(model.project_id == project_id)

    if search:
        term = f"%{search}%"
        # Text, Enum and other VARCHAR-backed types all subclass String.
        text_columns = [
            col for col in model.__table__.columns if isinstance(col.type, String)
        ]
        if text_columns:
            base = base.where(or_(*[col.ilike(term) for col in text_columns]))

    # total = matching rows ignoring pagination
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    # sorting -- only a genuine column name is honoured
    if sort and sort in model.__table__.columns:
        order_column = model.__table__.columns[sort]
    else:
        order_column = model.__table__.columns["id"]
    order_column = order_column.desc() if order == "desc" else order_column.asc()

    stmt = base.order_by(order_column)
    for relationship in eager or []:
        stmt = stmt.options(selectinload(relationship))
    rows = list(db.scalars(stmt.offset(skip).limit(limit)).all())
    return rows, total


def get_item(
    db: Session,
    model: type,
    item_id: int,
    *,
    eager: list[InstrumentedAttribute] | None = None,
) -> Any | None:
    """Return a single row by primary key, or ``None`` if it does not exist."""
    stmt = select(model).where(model.id == item_id)
    for relationship in eager or []:
        stmt = stmt.options(selectinload(relationship))
    return db.scalars(stmt).first()


def create_item(db: Session, model: type, data: dict[str, Any]) -> Any:
    """Insert a new row and return it."""
    obj = model(**data)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(obj)
    return obj


def update_item(db: Session, obj: Any, data: dict[str, Any]) -> Any:
    """Apply ``data`` (already filtered to provided fields) to an existing row."""
    for field, value in data.items():
        setattr(obj, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(obj)
    return obj


def delete_item(db: Session, obj: Any) -> None:
    """Delete a row.  Raises ``IntegrityError`` if it is still referenced."""
    db.delete(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
