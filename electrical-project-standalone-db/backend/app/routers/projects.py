"""Router for the ``projects`` registry plus the project-scoped composite views.

``projects`` is hand-written rather than generated because it needs three things
the generic factory does not provide:

* a delete that is RESTRICT by default but can cascade on request;
* a dashboard endpoint (row counts per Class B chapter);
* a full-export endpoint (every Class B row for one project, catalog-merged).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from .. import crud
from ..database import get_db
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
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows, total = crud.list_items(db, Project, skip=skip, limit=limit)
    return {"items": rows, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, Project, payload.model_dump())


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
