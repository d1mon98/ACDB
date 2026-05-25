"""REST router for user-defined table schemas and row data.

Mounted under /api/catalog-groups/{id}:
  GET/POST         /columns
  GET/PUT/DELETE   /columns/{col_id}
  GET/POST         /rows
  GET/PUT/DELETE   /rows/{row_id}
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_catalog_db as get_db
from ..models.catalog_groups import CatalogGroup
from ..models.custom_tables import CatalogColumnDef, CatalogCustomRow
from ..schemas.common import ListResponse
from ..schemas.custom_tables import (
    ColumnDefCreate,
    ColumnDefRead,
    ColumnDefUpdate,
    CustomRowCreate,
    CustomRowRead,
)

router = APIRouter(prefix="/api/catalog-groups", tags=["Custom Tables"])


def _require_group(group_id: int, db: Session) -> CatalogGroup:
    g = db.get(CatalogGroup, group_id)
    if g is None:
        raise HTTPException(404, "Catalog group not found.")
    return g


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

@router.get("/{group_id}/columns", response_model=list[ColumnDefRead])
def list_columns(group_id: int, db: Session = Depends(get_db)):
    _require_group(group_id, db)
    rows = db.scalars(
        select(CatalogColumnDef)
        .where(CatalogColumnDef.catalog_group_id == group_id)
        .order_by(CatalogColumnDef.display_order, CatalogColumnDef.id)
    ).all()
    return list(rows)


@router.post("/{group_id}/columns", response_model=ColumnDefRead, status_code=201)
def create_column(
    group_id: int, body: ColumnDefCreate, db: Session = Depends(get_db)
):
    _require_group(group_id, db)
    col = CatalogColumnDef(catalog_group_id=group_id, **body.model_dump())
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.put("/{group_id}/columns/{col_id}", response_model=ColumnDefRead)
def update_column(
    group_id: int,
    col_id: int,
    body: ColumnDefUpdate,
    db: Session = Depends(get_db),
):
    col = db.get(CatalogColumnDef, col_id)
    if col is None or col.catalog_group_id != group_id:
        raise HTTPException(404, "Column not found.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(col, k, v)
    db.commit()
    db.refresh(col)
    return col


@router.delete("/{group_id}/columns/{col_id}", status_code=204)
def delete_column(group_id: int, col_id: int, db: Session = Depends(get_db)):
    col = db.get(CatalogColumnDef, col_id)
    if col is None or col.catalog_group_id != group_id:
        raise HTTPException(404, "Column not found.")
    db.delete(col)
    db.commit()


# ---------------------------------------------------------------------------
# Data rows (JSON blobs)
# ---------------------------------------------------------------------------

def _row_to_read(row: CatalogCustomRow) -> CustomRowRead:
    try:
        data = json.loads(row.row_data)
    except (ValueError, TypeError):
        data = {}
    return CustomRowRead(
        id=row.id,
        catalog_group_id=row.catalog_group_id,
        row_data=data,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/{group_id}/rows", response_model=list[CustomRowRead])
def list_rows(group_id: int, db: Session = Depends(get_db)):
    _require_group(group_id, db)
    rows = db.scalars(
        select(CatalogCustomRow)
        .where(CatalogCustomRow.catalog_group_id == group_id)
        .order_by(CatalogCustomRow.id)
    ).all()
    return [_row_to_read(r) for r in rows]


@router.post("/{group_id}/rows", response_model=CustomRowRead, status_code=201)
def create_row(
    group_id: int, body: CustomRowCreate, db: Session = Depends(get_db)
):
    _require_group(group_id, db)
    row = CatalogCustomRow(
        catalog_group_id=group_id,
        row_data=json.dumps(body.row_data),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_read(row)


@router.put("/{group_id}/rows/{row_id}", response_model=CustomRowRead)
def update_row(
    group_id: int,
    row_id: int,
    body: CustomRowCreate,
    db: Session = Depends(get_db),
):
    row = db.get(CatalogCustomRow, row_id)
    if row is None or row.catalog_group_id != group_id:
        raise HTTPException(404, "Row not found.")
    row.row_data = json.dumps(body.row_data)
    db.commit()
    db.refresh(row)
    return _row_to_read(row)


@router.delete("/{group_id}/rows/{row_id}", status_code=204)
def delete_row(group_id: int, row_id: int, db: Session = Depends(get_db)):
    row = db.get(CatalogCustomRow, row_id)
    if row is None or row.catalog_group_id != group_id:
        raise HTTPException(404, "Row not found.")
    db.delete(row)
    db.commit()
