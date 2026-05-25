"""REST router for the guided Build-Project pipeline.

Exposes:

* the static pipeline definition and the per-project status (row counts,
  readiness, reviewed flags, catalog readiness, recommended next step);
* upsert of the per-step ``reviewed`` flag;
* the importable-fields metadata for a table (used by the Excel mapping screen);
* the three-stage Excel / CSV import -- columns / preview / commit -- with
  foreign keys resolved by natural key;
* downloadable .xlsx templates per table.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import importing, pipeline
from ..database import get_project_db as get_db
from ..models.pipeline import ProjectPipelineProgress
from ..registry import (
    TABLES,
    fk_target_table_name,
    get_table,
    spec_for_table_name,
)

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])


# ---- definition / status ------------------------------------------------


@router.get("/definition")
def get_definition():
    """The static pipeline definition (phases + steps), independent of any project."""
    return pipeline.definition()


@router.get("/status")
def get_status(project_id: int, db: Session = Depends(get_db)):
    """Per-step status for one project."""
    return pipeline.compute_status(db, project_id)


# ---- reviewed flag ------------------------------------------------------


class ProgressBody(BaseModel):
    project_id: int
    step_id: str
    reviewed: bool


@router.put("/progress")
def set_reviewed(body: ProgressBody, db: Session = Depends(get_db)):
    """Upsert the reviewed flag for one (project, step)."""
    row = db.scalar(
        select(ProjectPipelineProgress).where(
            ProjectPipelineProgress.project_id == body.project_id,
            ProjectPipelineProgress.step_id == body.step_id,
        )
    )
    if row is None:
        db.add(
            ProjectPipelineProgress(
                project_id=body.project_id,
                step_id=body.step_id,
                reviewed=body.reviewed,
            )
        )
    else:
        row.reviewed = body.reviewed
    db.commit()
    return {"project_id": body.project_id, "step_id": body.step_id, "reviewed": body.reviewed}


# ---- importable fields (for the mapping screen) -------------------------


def _field_label(spec, field: str) -> str:
    base = field.replace("_", " ").strip().capitalize()
    target = fk_target_table_name(spec.model, field)
    if target:
        target_spec = spec_for_table_name(target)
        if target_spec:
            return f"{base} (by {target_spec.natural_key})"
    return base


@router.get("/import/fields/{table}")
def get_importable_fields(table: str):
    """Metadata for the table's importable fields -- powers the mapping UI."""
    if table not in TABLES:
        raise HTTPException(404, f"Unknown table: {table}")
    spec = get_table(table)
    fields = []
    for name in importing.importable_fields(spec):
        info = spec.create_schema.model_fields[name]
        target_table_name = fk_target_table_name(spec.model, name)
        target_spec = (
            spec_for_table_name(target_table_name) if target_table_name else None
        )
        fields.append(
            {
                "name": name,
                "label": _field_label(spec, name),
                "required": info.is_required(),
                "is_fk": target_spec is not None,
                "fk_target": target_spec.slug if target_spec else None,
                "fk_key": target_spec.natural_key if target_spec else None,
            }
        )
    return {"table": spec.slug, "label": spec.label, "fields": fields}


# ---- import: columns / preview / commit ---------------------------------


def _require_spec(table: str):
    if table not in TABLES:
        raise HTTPException(404, f"Unknown table: {table}")
    return get_table(table)


def _parse_or_400(filename: str, content: bytes):
    try:
        return importing.parse_spreadsheet(filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"Could not read file: {e}")


def _parse_mapping(raw: str) -> dict[str, str]:
    try:
        mapping = json.loads(raw or "{}")
    except json.JSONDecodeError:
        raise HTTPException(400, "Mapping must be valid JSON.")
    if not isinstance(mapping, dict):
        raise HTTPException(400, "Mapping must be a JSON object {column: field}.")
    return {str(k): str(v) for k, v in mapping.items() if v}


@router.post("/import/columns")
async def import_columns(file: UploadFile = File(...)):
    """Stage 1 -- return the spreadsheet's column headers and row count."""
    content = await file.read()
    headers, rows = _parse_or_400(file.filename or "", content)
    return {"columns": headers, "row_count": len(rows)}


@router.post("/import/preview")
async def import_preview(
    file: UploadFile = File(...),
    table: str = Form(...),
    project_id: int | None = Form(None),
    mapping: str = Form(...),
    db: Session = Depends(get_db),
):
    """Stage 2 -- validate every row, return per-row results (no inserts)."""
    spec = _require_spec(table)
    if spec.project_scoped and project_id is None:
        raise HTTPException(400, "project_id is required for this table.")
    content = await file.read()
    _, rows = _parse_or_400(file.filename or "", content)
    parsed_mapping = _parse_mapping(mapping)
    return importing.preview_import(db, spec, project_id or 0, rows, parsed_mapping)


@router.post("/import/commit")
async def import_commit(
    file: UploadFile = File(...),
    table: str = Form(...),
    project_id: int | None = Form(None),
    mapping: str = Form(...),
    db: Session = Depends(get_db),
):
    """Stage 3 -- insert the valid rows."""
    spec = _require_spec(table)
    if spec.project_scoped and project_id is None:
        raise HTTPException(400, "project_id is required for this table.")
    content = await file.read()
    _, rows = _parse_or_400(file.filename or "", content)
    parsed_mapping = _parse_mapping(mapping)
    return importing.commit_import(db, spec, project_id or 0, rows, parsed_mapping)


# ---- template download --------------------------------------------------


@router.get("/import/template/{table}")
def import_template(table: str):
    """Download an .xlsx template for the table (header row + one example row)."""
    spec = _require_spec(table)
    content = importing.build_template(spec)
    return Response(
        content=content,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{spec.slug}-template.xlsx"'
        },
    )
