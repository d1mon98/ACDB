"""ERD (Entity Relationship Diagram) router.

Provides three groups of endpoints:

* ``GET /api/erd/schema``           — introspect every table, its columns, and
                                      its FK edges directly from SQLite PRAGMAs.
* ``GET|PUT /api/erd/layout``       — persist drag-and-drop node positions inside
                                      the connected database (erd_node_positions).
* ``GET|POST|PUT|DELETE /api/erd/relationships``
                                    — user-defined / annotated relationships stored
                                      in erd_relationships; these complement the
                                      FK-derived edges shown on the canvas.

Both metadata tables are created lazily (CREATE TABLE IF NOT EXISTS) so they
work with existing databases that pre-date this feature.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_catalog_db as get_db

router = APIRouter(prefix="/api/erd", tags=["ERD"])

# ---------------------------------------------------------------------------
# Lazy table creation
# ---------------------------------------------------------------------------

_TABLES_CREATED = False


def _ensure_erd_tables(db: Session) -> None:
    global _TABLES_CREATED
    if _TABLES_CREATED:
        return
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS erd_node_positions (
            table_name TEXT PRIMARY KEY,
            x          REAL NOT NULL DEFAULT 0,
            y          REAL NOT NULL DEFAULT 0,
            collapsed  INTEGER NOT NULL DEFAULT 0
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS erd_relationships (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_table   TEXT NOT NULL,
            child_table    TEXT NOT NULL,
            foreign_key    TEXT,
            rel_type       TEXT NOT NULL DEFAULT 'ONE_TO_MANY',
            cascade_update TEXT NOT NULL DEFAULT 'NO ACTION',
            cascade_delete TEXT NOT NULL DEFAULT 'NO ACTION',
            label          TEXT,
            notes          TEXT
        )
    """))
    db.commit()
    _TABLES_CREATED = True


# ---------------------------------------------------------------------------
# Schema introspection
# ---------------------------------------------------------------------------

_SKIP_TABLES = {"alembic_version", "erd_node_positions", "erd_relationships"}


@router.get("/schema")
def get_schema(db: Session = Depends(get_db)):
    """Return every user table with its columns and FK relationships."""
    _ensure_erd_tables(db)

    rows = db.execute(text(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )).fetchall()

    tables = [r[0] for r in rows if r[0] not in _SKIP_TABLES]

    result: dict[str, dict] = {}
    for table in tables:
        cols = db.execute(text(f"PRAGMA table_info(\"{table}\")")).fetchall()
        fks  = db.execute(text(f"PRAGMA foreign_key_list(\"{table}\")")).fetchall()

        result[table] = {
            "columns": [
                {
                    "cid":     c[0],
                    "name":    c[1],
                    "type":    c[2],
                    "notnull": bool(c[3]),
                    "default": c[4],
                    "pk":      bool(c[5]),
                }
                for c in cols
            ],
            "foreign_keys": [
                {
                    "id":        fk[0],
                    "seq":       fk[1],
                    "ref_table": fk[2],
                    "from_col":  fk[3],
                    "to_col":    fk[4],
                    "on_update": fk[5],
                    "on_delete": fk[6],
                }
                for fk in fks
            ],
        }

    return result


# ---------------------------------------------------------------------------
# Node layout persistence
# ---------------------------------------------------------------------------

class NodePosition(BaseModel):
    x: float
    y: float
    collapsed: bool = False


class LayoutPayload(BaseModel):
    positions: dict[str, NodePosition]


@router.get("/layout")
def get_layout(db: Session = Depends(get_db)):
    """Return persisted node positions."""
    _ensure_erd_tables(db)
    rows = db.execute(
        text("SELECT table_name, x, y, collapsed FROM erd_node_positions")
    ).fetchall()
    return {
        r[0]: {"x": r[1], "y": r[2], "collapsed": bool(r[3])}
        for r in rows
    }


@router.put("/layout")
def save_layout(payload: LayoutPayload, db: Session = Depends(get_db)):
    """Upsert node positions after a drag-and-drop or auto-layout."""
    _ensure_erd_tables(db)
    for table_name, pos in payload.positions.items():
        db.execute(text("""
            INSERT INTO erd_node_positions (table_name, x, y, collapsed)
            VALUES (:t, :x, :y, :c)
            ON CONFLICT(table_name) DO UPDATE SET
                x = excluded.x,
                y = excluded.y,
                collapsed = excluded.collapsed
        """), {"t": table_name, "x": pos.x, "y": pos.y, "c": int(pos.collapsed)})
    db.commit()
    return {"saved": len(payload.positions)}


# ---------------------------------------------------------------------------
# User-defined / annotated relationships
# ---------------------------------------------------------------------------

REL_TYPES   = {"ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_MANY"}
CASCADE_OPS = {"NO ACTION", "RESTRICT", "SET NULL", "SET DEFAULT", "CASCADE"}


class RelationshipCreate(BaseModel):
    parent_table:   str
    child_table:    str
    foreign_key:    str | None = None
    rel_type:       str = "ONE_TO_MANY"
    cascade_update: str = "NO ACTION"
    cascade_delete: str = "NO ACTION"
    label:          str | None = None
    notes:          str | None = None


class RelationshipUpdate(BaseModel):
    parent_table:   str | None = None
    child_table:    str | None = None
    foreign_key:    str | None = None
    rel_type:       str | None = None
    cascade_update: str | None = None
    cascade_delete: str | None = None
    label:          str | None = None
    notes:          str | None = None


def _validate_rel(rel_type: str | None, cascade_update: str | None, cascade_delete: str | None):
    if rel_type and rel_type not in REL_TYPES:
        raise HTTPException(400, f"rel_type must be one of {REL_TYPES}")
    if cascade_update and cascade_update not in CASCADE_OPS:
        raise HTTPException(400, f"cascade_update must be one of {CASCADE_OPS}")
    if cascade_delete and cascade_delete not in CASCADE_OPS:
        raise HTTPException(400, f"cascade_delete must be one of {CASCADE_OPS}")


def _row_to_dict(r) -> dict:
    return {
        "id":            r[0],
        "parent_table":  r[1],
        "child_table":   r[2],
        "foreign_key":   r[3],
        "rel_type":      r[4],
        "cascade_update": r[5],
        "cascade_delete": r[6],
        "label":         r[7],
        "notes":         r[8],
    }


@router.get("/relationships")
def list_relationships(db: Session = Depends(get_db)):
    _ensure_erd_tables(db)
    rows = db.execute(text(
        "SELECT id, parent_table, child_table, foreign_key, rel_type, "
        "cascade_update, cascade_delete, label, notes "
        "FROM erd_relationships ORDER BY id"
    )).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.post("/relationships", status_code=201)
def create_relationship(payload: RelationshipCreate, db: Session = Depends(get_db)):
    _ensure_erd_tables(db)
    _validate_rel(payload.rel_type, payload.cascade_update, payload.cascade_delete)
    cur = db.execute(text("""
        INSERT INTO erd_relationships
            (parent_table, child_table, foreign_key, rel_type,
             cascade_update, cascade_delete, label, notes)
        VALUES
            (:pt, :ct, :fk, :rt, :cu, :cd, :lb, :nt)
    """), {
        "pt": payload.parent_table,
        "ct": payload.child_table,
        "fk": payload.foreign_key,
        "rt": payload.rel_type,
        "cu": payload.cascade_update,
        "cd": payload.cascade_delete,
        "lb": payload.label,
        "nt": payload.notes,
    })
    db.commit()
    row = db.execute(text(
        "SELECT id, parent_table, child_table, foreign_key, rel_type, "
        "cascade_update, cascade_delete, label, notes "
        "FROM erd_relationships WHERE id = :id"
    ), {"id": cur.lastrowid}).fetchone()
    return _row_to_dict(row)


@router.put("/relationships/{rel_id}")
def update_relationship(rel_id: int, payload: RelationshipUpdate, db: Session = Depends(get_db)):
    _ensure_erd_tables(db)
    existing = db.execute(text(
        "SELECT id FROM erd_relationships WHERE id = :id"
    ), {"id": rel_id}).fetchone()
    if not existing:
        raise HTTPException(404, f"Relationship {rel_id} not found.")

    _validate_rel(payload.rel_type, payload.cascade_update, payload.cascade_delete)

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update.")

    col_map = {
        "parent_table": "parent_table",
        "child_table": "child_table",
        "foreign_key": "foreign_key",
        "rel_type": "rel_type",
        "cascade_update": "cascade_update",
        "cascade_delete": "cascade_delete",
        "label": "label",
        "notes": "notes",
    }
    set_parts = ", ".join(f"{col_map[k]} = :{k}" for k in updates)
    updates["rel_id"] = rel_id
    db.execute(text(f"UPDATE erd_relationships SET {set_parts} WHERE id = :rel_id"), updates)
    db.commit()

    row = db.execute(text(
        "SELECT id, parent_table, child_table, foreign_key, rel_type, "
        "cascade_update, cascade_delete, label, notes "
        "FROM erd_relationships WHERE id = :id"
    ), {"id": rel_id}).fetchone()
    return _row_to_dict(row)


@router.delete("/relationships/{rel_id}", status_code=204)
def delete_relationship(rel_id: int, db: Session = Depends(get_db)):
    _ensure_erd_tables(db)
    existing = db.execute(text(
        "SELECT id FROM erd_relationships WHERE id = :id"
    ), {"id": rel_id}).fetchone()
    if not existing:
        raise HTTPException(404, f"Relationship {rel_id} not found.")
    db.execute(text("DELETE FROM erd_relationships WHERE id = :id"), {"id": rel_id})
    db.commit()
