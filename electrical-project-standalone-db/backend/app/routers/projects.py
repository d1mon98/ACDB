"""Router for the ``projects`` registry plus the project-scoped composite views.

``projects`` is hand-written rather than generated because it needs three things
the generic factory does not provide:

* a delete that is RESTRICT by default but can cascade on request;
* a dashboard endpoint (row counts per Class B chapter);
* a full-export endpoint (every Class B row for one project, catalog-merged).
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from .. import crud
from .. import db_manager as _dm
from ..database import get_project_db as get_db
from ..db_manager import project_manager
from ..models.projects import (
    Project,
    ProjectCable,
    ProjectControlPanel,
    ProjectEquipment,
    ProjectInstrument,
    ProjectIOPoint,
    ProjectLocation,
    ProjectPanelCircuit,
    ProjectPanelComponent,
)
from ..schemas.common import ListResponse
from ..schemas.dashboard import ProjectAllData, ProjectDashboard
from ..schemas.projects import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["Project"])

# Class B tables in a FK-safe deletion order: a child table always appears
# before any table it references via a RESTRICT foreign key.
_CASCADE_ORDER = [
    ProjectIOPoint,
    ProjectPanelCircuit,
    ProjectPanelComponent,
    ProjectInstrument,
    ProjectCable,
    ProjectControlPanel,
    ProjectEquipment,
    ProjectLocation,
]


def _count(db: Session, model: type, project_id: int) -> int:
    """Number of rows of ``model`` belonging to a project."""
    return (
        db.scalar(
            select(func.count())
            .select_from(model)
            .where(model.project_id == project_id)
        )
        or 0
    )


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = crud.get_item(db, Project, project_id)
    if project is None:
        raise HTTPException(404, f"Project {project_id} not found.")
    return project


# --------------------------------------------------------------------------
# CRUD
# --------------------------------------------------------------------------


@router.get("", response_model=ListResponse[ProjectRead])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    rows, total = crud.list_items(db, Project, skip=skip, limit=limit)
    return {"items": rows, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = crud.create_item(db, Project, payload.model_dump())
    # Auto-create a standalone DB file for this project.
    try:
        project_manager.create_database(project.project_number)
    except FileExistsError:
        pass  # DB already exists — fine
    except (ValueError, OSError):
        pass  # Bad name or FS error — non-fatal, user can create manually
    return project


def _migrate_project_data(source_path: str, target_path: str, project_id: int) -> None:
    """Copy one project's rows from source_path into target_path via raw SQLite."""
    _dm._ensure_table_sets()
    src = sqlite3.connect(source_path)
    tgt = sqlite3.connect(target_path)
    src.row_factory = sqlite3.Row
    try:
        tgt_tables = {r[0] for r in tgt.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}

        # Copy the project row itself.
        row = src.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if row and "projects" in tgt_tables:
            cols = ", ".join(row.keys())
            ph = ", ".join("?" * len(row.keys()))
            tgt.execute(
                f"INSERT OR IGNORE INTO projects ({cols}) VALUES ({ph})", list(row)
            )

        # Copy every project_* table that exists in both DBs.
        for table in sorted(_dm._PROJECT_TABLES or set()):
            if table == "projects" or table not in tgt_tables:
                continue
            try:
                rows = src.execute(
                    f"SELECT * FROM {table} WHERE project_id=?", (project_id,)
                ).fetchall()
                if rows:
                    cols = ", ".join(rows[0].keys())
                    ph = ", ".join("?" * len(rows[0].keys()))
                    tgt.executemany(
                        f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({ph})",
                        [list(r) for r in rows],
                    )
            except sqlite3.OperationalError:
                pass  # column doesn't exist in source — skip

        tgt.commit()
    finally:
        src.close()
        tgt.close()


@router.post("/{project_id}/activate")
def activate_project(project_id: int, db: Session = Depends(get_db)):
    """Connect the project-specific DB for this project, disconnecting any other.

    If the per-project DB file does not yet exist it is created and any data
    for this project that lives in the currently-connected DB is migrated into
    it automatically.
    """
    project = _get_project_or_404(db, project_id)
    db_name = project.project_number

    target_path = project_manager.databases_dir / _dm.safe_db_filename(db_name)

    if not target_path.exists():
        # Create schema in the new file.
        try:
            project_manager.create_database(db_name)
        except (ValueError, OSError) as e:
            raise HTTPException(400, f"Cannot create project database: {e}")

        # Migrate any data that already exists in the currently-connected DB.
        if project_manager.current_path:
            try:
                _migrate_project_data(
                    project_manager.current_path, str(target_path), project_id
                )
            except Exception:
                pass  # migration is best-effort; new DB stays empty if it fails

    try:
        project_manager.connect(db_name)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, f"Project database not found: {e}")

    return {
        "role": project_manager.role,
        "connected": project_manager.connected,
        "current": project_manager.current,
        "path": project_manager.current_path,
    }


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return _get_project_or_404(db, project_id)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)
):
    project = _get_project_or_404(db, project_id)
    return crud.update_item(db, project, payload.model_dump(exclude_unset=True))


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    cascade: bool = Query(
        False,
        description="If true, also delete every Class B row belonging to the "
        "project.  If false (default) the delete is refused when the project "
        "still has dependent records.",
    ),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(db, project_id)

    counts = {model.__tablename__: _count(db, model, project_id) for model in _CASCADE_ORDER}
    dependent_total = sum(counts.values())

    if dependent_total and not cascade:
        detail = ", ".join(f"{name}: {n}" for name, n in counts.items() if n)
        raise HTTPException(
            409,
            f"Project {project_id} still has {dependent_total} dependent "
            f"record(s) ({detail}). Re-send with ?cascade=true to delete them "
            f"too, or remove them first.",
        )

    # Delete children first (FK-safe order), then the project itself.
    for model in _CASCADE_ORDER:
        db.execute(delete(model).where(model.project_id == project_id))
    db.delete(project)
    db.commit()


# --------------------------------------------------------------------------
# Project-scoped composite views
# --------------------------------------------------------------------------


@router.get("/{project_id}/dashboard", response_model=ProjectDashboard)
def project_dashboard(project_id: int, db: Session = Depends(get_db)):
    """Row counts per Class B chapter -- how completely the DB reflects the project."""
    project = _get_project_or_404(db, project_id)
    counts = {
        "locations": _count(db, ProjectLocation, project_id),
        "equipment": _count(db, ProjectEquipment, project_id),
        "panel_circuits": _count(db, ProjectPanelCircuit, project_id),
        "cables": _count(db, ProjectCable, project_id),
        "instruments": _count(db, ProjectInstrument, project_id),
        "io_points": _count(db, ProjectIOPoint, project_id),
        "control_panels": _count(db, ProjectControlPanel, project_id),
        "panel_components": _count(db, ProjectPanelComponent, project_id),
    }
    return {"project": project, "total": sum(counts.values()), **counts}


@router.get("/{project_id}/all", response_model=ProjectAllData)
def project_all_data(project_id: int, db: Session = Depends(get_db)):
    """Every Class B row for one project, with catalog records merged in."""
    project = _get_project_or_404(db, project_id)

    def rows(model, *, eager_catalog: bool = False):
        stmt = select(model).where(model.project_id == project_id).order_by(model.id)
        if eager_catalog:
            stmt = stmt.options(selectinload(model.catalog))
        return list(db.scalars(stmt).all())

    return {
        "project": project,
        "locations": rows(ProjectLocation),
        "equipment": rows(ProjectEquipment, eager_catalog=True),
        "panel_circuits": rows(ProjectPanelCircuit),
        "cables": rows(ProjectCable, eager_catalog=True),
        "instruments": rows(ProjectInstrument, eager_catalog=True),
        "io_points": rows(ProjectIOPoint, eager_catalog=True),
        "control_panels": rows(ProjectControlPanel),
        "panel_components": rows(ProjectPanelComponent, eager_catalog=True),
    }
