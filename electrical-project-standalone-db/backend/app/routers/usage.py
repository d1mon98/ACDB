"""Generic row-usage endpoint.

GET /api/usage-check/{table_name}/{row_id}

Returns every table that has a foreign key pointing at *table_name* and the
count of rows in that table that reference the given *row_id*.  The frontend
uses this to warn the user before they attempt to delete a catalog row.

SQLite enforces foreign keys (PRAGMA foreign_keys=ON is set per connection in
database.py), so rows with references cannot be deleted -- this endpoint just
lets the UI say *why* in advance, before the attempt.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.orm import Session

from ..database import get_catalog_db as get_db
from ..db_manager import manager

router = APIRouter(prefix="/api/usage-check", tags=["Meta"])


class TableRef(BaseModel):
    table: str
    column: str
    count: int


class UsageResult(BaseModel):
    table: str
    id: int
    references: list[TableRef]
    total: int


@router.get("/{table_name}/{row_id}", response_model=UsageResult)
def check_usage(table_name: str, row_id: int, db: Session = Depends(get_db)):
    """Count references to a specific row from every FK-pointing table."""
    eng = manager.engine
    if eng is None:
        return UsageResult(table=table_name, id=row_id, references=[], total=0)

    inspector = sa_inspect(eng)
    refs: list[TableRef] = []

    for ref_table in inspector.get_table_names():
        for fk in inspector.get_foreign_keys(ref_table):
            if fk.get("referred_table") != table_name:
                continue
            col = fk["constrained_columns"][0]
            try:
                count = db.execute(
                    text(f'SELECT COUNT(*) FROM "{ref_table}" WHERE "{col}" = :id'),
                    {"id": row_id},
                ).scalar() or 0
                if count > 0:
                    refs.append(TableRef(table=ref_table, column=col, count=int(count)))
            except Exception:
                pass

    return UsageResult(
        table=table_name,
        id=row_id,
        references=refs,
        total=sum(r.count for r in refs),
    )
