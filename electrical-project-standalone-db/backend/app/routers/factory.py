"""CRUD router factory.

Every table exposes an identical REST surface, generated once here:

* list (with pagination, ``project_id`` filter, free-text ``search`` and column
  ``sort``), get, create, update, delete;
* ``/export-csv`` and ``/import-csv`` for bulk round-tripping;
* the five catalog-linked Class B tables also get ``/merged`` routes that return
  the project row with its catalog record joined in.

This module deliberately does NOT use ``from __future__ import annotations``:
the request-body type is supplied as a *closure variable* (``create_schema`` /
``update_schema``) and must resolve to the real class at function-definition
time so FastAPI can read it from the signature.
"""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_catalog_db
from ..schemas.common import ListResponse


class ImportCSVBody(BaseModel):
    """Body for the CSV import endpoint -- the raw CSV text."""

    content: str


def _format_error(exc: Exception) -> str:
    """Turn a validation / integrity error into a short readable string."""
    if isinstance(exc, ValidationError):
        parts = []
        for err in exc.errors()[:3]:
            loc = ".".join(str(x) for x in err.get("loc", ()))
            parts.append(f"{loc}: {err.get('msg')}")
        return "; ".join(parts)
    return str(getattr(exc, "orig", exc))


def make_crud_router(
    *,
    model: type,
    prefix: str,
    label: str,
    create_schema: type,
    read_schema: type,
    update_schema: type,
    merged_schema: type | None = None,
    db_dep=None,
    catalog_model: type | None = None,
    catalog_id_field: str | None = None,
    catalog_read_schema: type | None = None,
):
    """Build a fully wired CRUD ``APIRouter`` for one table.

    Parameters
    ----------
    model          ORM model class.
    prefix         URL prefix, e.g. ``/api/catalog-manufacturers``.
    label          Human-readable singular name, used in tags and 404 messages.
    create_schema  Schema for POST bodies (and CSV-import row validation).
    read_schema    Schema for responses.
    update_schema  Partial schema for PUT bodies.
    merged_schema  If given, also expose ``/merged`` routes using this schema
                   (only the catalog-linked Class B tables pass this).
    db_dep         FastAPI dependency that yields the session this router uses.
                   Defaults to the catalog DB; pass ``get_project_db`` for
                   project-table routers so they hit the project database.
    """
    if db_dep is None:
        db_dep = get_catalog_db
    router = APIRouter(prefix=prefix, tags=[label])
    slug = prefix.rsplit("/", 1)[-1]
    columns = [col.name for col in model.__table__.columns]

    # -- list -----------------------------------------------------------------
    @router.get("", response_model=ListResponse[read_schema])
    def list_items(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        project_id: int | None = Query(
            None, description="Filter to one project (Class B tables only)."
        ),
        search: str | None = Query(None, description="Free-text search."),
        sort: str | None = Query(None, description="Column name to sort by."),
        order: str = Query("asc", pattern="^(asc|desc)$"),
        db: Session = Depends(db_dep),
    ):
        rows, total = crud.list_items(
            db,
            model,
            skip=skip,
            limit=limit,
            project_id=project_id,
            search=search,
            sort=sort,
            order=order,
        )
        return {"items": rows, "total": total, "skip": skip, "limit": limit}

    # -- create ---------------------------------------------------------------
    @router.post("", response_model=read_schema, status_code=201)
    def create_item(payload: create_schema, db: Session = Depends(db_dep)):
        return crud.create_item(db, model, payload.model_dump())

    # -- export CSV -----------------------------------------------------------
    @router.get("/export-csv")
    def export_csv(
        project_id: int | None = Query(None),
        search: str | None = Query(None),
        db: Session = Depends(db_dep),
    ):
        """Download every row of this table (filtered) as a CSV file."""
        rows, _ = crud.list_items(
            db, model, skip=0, limit=100000, project_id=project_id, search=search
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(["" if getattr(row, c) is None else getattr(row, c) for c in columns])
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{slug}.csv"'},
        )

    # -- import CSV -----------------------------------------------------------
    @router.post("/import-csv")
    def import_csv(
        body: ImportCSVBody,
        project_id: int | None = Query(
            None, description="Project to import the rows into (Class B tables)."
        ),
        db: Session = Depends(db_dep),
    ):
        """Create rows from CSV text.  Returns counts and per-row errors.

        Each row is validated through the same schema as a normal create, so
        the merge rule and field types are enforced.  ``id`` and the timestamp
        columns are ignored if present.
        """
        allowed = set(create_schema.model_fields.keys())
        reader = csv.DictReader(io.StringIO(body.content))
        created = 0
        errors: list[dict] = []

        for line_number, raw in enumerate(reader, start=2):  # row 1 is the header
            data = {
                key: (value if value not in ("", None) else None)
                for key, value in raw.items()
                if key in allowed
            }
            if "project_id" in allowed and project_id is not None:
                data["project_id"] = project_id
            try:
                payload = create_schema(**data)
                crud.create_item(db, model, payload.model_dump())
                created += 1
            except Exception as exc:  # noqa: BLE001 -- reported per row
                db.rollback()
                errors.append({"row": line_number, "error": _format_error(exc)})

        return {"created": created, "errors": errors[:100]}

    # -- merged views (catalog-linked Class B tables only) --------------------
    # Declared before "/{item_id}" so the literal segments are not swallowed by
    # the integer path parameter.  The catalog now lives in a separate DB, so
    # we fetch project rows from the project session and look up the matching
    # catalog rows from the catalog session manually.
    if merged_schema is not None:
        from sqlalchemy import select as _select

        from ..db_manager import catalog_manager as _catalog_manager

        def _fetch_catalog_map(ids: set[int]) -> dict[int, dict]:
            """Bulk-load catalog rows for the given IDs, return {id: dict}."""
            if not ids or catalog_model is None or catalog_read_schema is None:
                return {}
            if not _catalog_manager.connected:
                return {}
            cdb = next(_catalog_manager.get_session())
            try:
                cat_rows = cdb.execute(
                    _select(catalog_model).where(catalog_model.id.in_(ids))
                ).scalars().all()
                return {
                    c.id: catalog_read_schema.model_validate(
                        c, from_attributes=True
                    ).model_dump()
                    for c in cat_rows
                }
            finally:
                cdb.close()

        def _merge(row, cat_map: dict[int, dict]) -> dict:
            base = read_schema.model_validate(row, from_attributes=True).model_dump()
            base["is_custom"] = getattr(row, "is_custom", False)
            cat_id = (
                getattr(row, catalog_id_field, None) if catalog_id_field else None
            )
            base["catalog"] = cat_map.get(cat_id) if cat_id else None
            return base

        @router.get("/merged", response_model=ListResponse[merged_schema])
        def list_merged(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000),
            project_id: int | None = Query(None),
            search: str | None = Query(None),
            sort: str | None = Query(None),
            order: str = Query("asc", pattern="^(asc|desc)$"),
            db: Session = Depends(db_dep),
        ):
            """Project rows with their catalog records joined in (cross-DB)."""
            rows, total = crud.list_items(
                db, model, skip=skip, limit=limit, project_id=project_id,
                search=search, sort=sort, order=order,
            )
            ids: set[int] = set()
            if catalog_id_field:
                ids = {
                    getattr(r, catalog_id_field) for r in rows
                    if getattr(r, catalog_id_field, None) is not None
                }
            cat_map = _fetch_catalog_map(ids)
            items = [_merge(r, cat_map) for r in rows]
            return {"items": items, "total": total, "skip": skip, "limit": limit}

        @router.get("/merged/{item_id}", response_model=merged_schema)
        def get_merged(item_id: int, db: Session = Depends(db_dep)):
            obj = crud.get_item(db, model, item_id)
            if obj is None:
                raise HTTPException(404, f"{label} {item_id} not found.")
            ids: set[int] = set()
            if catalog_id_field:
                cid = getattr(obj, catalog_id_field, None)
                if cid is not None:
                    ids = {cid}
            cat_map = _fetch_catalog_map(ids)
            return _merge(obj, cat_map)

    # -- get ------------------------------------------------------------------
    @router.get("/{item_id}", response_model=read_schema)
    def get_item(item_id: int, db: Session = Depends(db_dep)):
        obj = crud.get_item(db, model, item_id)
        if obj is None:
            raise HTTPException(404, f"{label} {item_id} not found.")
        return obj

    # -- update ---------------------------------------------------------------
    @router.put("/{item_id}", response_model=read_schema)
    def update_item(
        item_id: int, payload: update_schema, db: Session = Depends(db_dep)
    ):
        obj = crud.get_item(db, model, item_id)
        if obj is None:
            raise HTTPException(404, f"{label} {item_id} not found.")
        return crud.update_item(db, obj, payload.model_dump(exclude_unset=True))

    # -- delete ---------------------------------------------------------------
    @router.delete("/{item_id}", status_code=204)
    def delete_item(item_id: int, db: Session = Depends(db_dep)):
        obj = crud.get_item(db, model, item_id)
        if obj is None:
            raise HTTPException(404, f"{label} {item_id} not found.")
        crud.delete_item(db, obj)

    return router
