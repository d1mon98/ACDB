"""REST router for catalog_groups: CRUD plus a /tree endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_catalog_db as get_db
from ..models.catalog_groups import CatalogGroup
from ..schemas.catalog_groups import (
    CatalogGroupCreate,
    CatalogGroupRead,
    CatalogGroupTree,
    CatalogGroupUpdate,
)
from ..schemas.common import ListResponse

router = APIRouter(prefix="/api/catalog-groups", tags=["Catalog Groups"])


def _to_tree(
    groups: list[CatalogGroup],
    parent_id: int | None = None,
) -> list[CatalogGroupTree]:
    """Recursively build a nested tree from a flat list."""
    nodes = [g for g in groups if g.parent_group_id == parent_id]
    nodes.sort(key=lambda g: (g.display_order, g.group_name))
    result = []
    for g in nodes:
        node = CatalogGroupTree(
            id=g.id,
            group_name=g.group_name,
            group_code=g.group_code,
            description=g.description,
            display_order=g.display_order,
            is_active=g.is_active,
            linked_table=g.linked_table,
            children=_to_tree(groups, parent_id=g.id),
        )
        result.append(node)
    return result


@router.get("/tree", response_model=list[CatalogGroupTree])
def get_tree(db: Session = Depends(get_db)):
    """Return the full catalog group hierarchy as a nested tree."""
    groups = db.scalars(select(CatalogGroup)).all()
    return _to_tree(list(groups), parent_id=None)


@router.get("", response_model=ListResponse[CatalogGroupRead])
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(CatalogGroup.__class__).select_from(CatalogGroup)
    ) or 0
    # simpler: just count all
    all_groups = db.scalars(select(CatalogGroup)).all()
    total = len(all_groups)
    page = list(all_groups)[skip: skip + limit]
    return ListResponse(items=page, total=total, skip=skip, limit=limit)


@router.get("/{group_id}", response_model=CatalogGroupRead)
def get_group(group_id: int, db: Session = Depends(get_db)):
    g = db.get(CatalogGroup, group_id)
    if g is None:
        raise HTTPException(404, "Catalog group not found.")
    return g


@router.post("", response_model=CatalogGroupRead, status_code=201)
def create_group(body: CatalogGroupCreate, db: Session = Depends(get_db)):
    g = CatalogGroup(**body.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.put("/{group_id}", response_model=CatalogGroupRead)
def update_group(
    group_id: int, body: CatalogGroupUpdate, db: Session = Depends(get_db)
):
    g = db.get(CatalogGroup, group_id)
    if g is None:
        raise HTTPException(404, "Catalog group not found.")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(g, key, val)
    db.commit()
    db.refresh(g)
    return g


@router.delete("/{group_id}", status_code=204)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = db.get(CatalogGroup, group_id)
    if g is None:
        raise HTTPException(404, "Catalog group not found.")
    db.delete(g)
    db.commit()
