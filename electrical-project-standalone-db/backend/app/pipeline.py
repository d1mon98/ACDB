"""The guided Build-Project pipeline.

A static, ordered definition of phases and steps that walks a designer through
the project tables in dependency order, so every foreign-key dropdown is
already populated by the time its step is reached.  The frontend renders the
stepper purely from this definition -- it is never hard-coded in the UI.

Each step maps to one existing table.  ``prerequisites`` lists the step ids
whose data should exist first; readiness is computed from their row counts.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models.pipeline import ProjectPipelineProgress
from .registry import get_table


@dataclass(frozen=True)
class Phase:
    id: str
    title: str


@dataclass(frozen=True)
class Step:
    id: str
    number: int
    title: str
    phase_id: str
    table: str  # table slug
    prerequisites: tuple[str, ...]
    description: str


PHASES: list[Phase] = [
    Phase("phase-0", "Project Setup"),
    Phase("phase-1", "Spatial Framework"),
    Phase("phase-2", "Power Distribution Backbone"),
    Phase("phase-3", "Loads & Circuits"),
    Phase("phase-4", "Field Instrumentation"),
    Phase("phase-5", "Control Systems"),
    Phase("phase-6", "I/O Integration"),
    Phase("phase-7", "Cabling & Routing"),
    Phase("phase-8", "Verification"),
]

STEPS: list[Step] = [
    Step(
        "step-project", 0, "Create / Select Project", "phase-0", "projects", (),
        "Create or select the project record -- number, name, client, site and "
        "voltage classes. The pipeline then operates on that project.",
    ),
    Step(
        "step-locations", 1, "Locations / Areas", "phase-1", "project-locations", (),
        "Define buildings, rooms, process areas and area classifications. "
        "Nearly every later step references a location.",
    ),
    Step(
        "step-power", 2, "Power Distribution Equipment", "phase-2",
        "project-equipment", ("step-locations",),
        "Add service entrance, switchgear, transformers, MCCs and panelboards. "
        "Build top-down with the Fed-From reference to form the one-line.",
    ),
    Step(
        "step-circuits", 3, "Panel Circuits", "phase-3",
        "project-panel-circuits", ("step-power", "step-locations"),
        "Add the circuits and feeders inside each panelboard and MCC.",
    ),
    Step(
        "step-instruments", 4, "Instruments", "phase-4",
        "project-instruments", ("step-locations",),
        "Add field instrument tags, each assigned to a location, loop and the "
        "equipment or process it serves.",
    ),
    Step(
        "step-panels", 5, "Control Panels", "phase-5",
        "project-control-panels", ("step-locations",),
        "Add PLC, instrumentation and control panel instances.",
    ),
    Step(
        "step-components", 6, "Panel Components", "phase-5",
        "project-panel-components", ("step-panels",),
        "Add the devices placed inside each control panel.",
    ),
    Step(
        "step-io", 7, "I/O List", "phase-6", "project-io-list",
        ("step-instruments", "step-components"),
        "Tie instruments and panel components to PLC I/O points "
        "(rack-slot-channel).",
    ),
    Step(
        "step-cables", 8, "Cables", "phase-7", "project-cables",
        ("step-power", "step-instruments", "step-panels"),
        "Build the FROM-TO cable schedule between equipment, instruments and "
        "control panels.",
    ),
    Step(
        "step-conduits", 9, "Conduits / Trays", "phase-7", "project-conduits",
        ("step-locations",),
        "Add conduits, cable trays and duct-bank segments.",
    ),
    Step(
        "step-routes", 10, "Cable Routes", "phase-7", "project-cable-routes",
        ("step-cables", "step-conduits"),
        "Assign cables to conduits and trays.",
    ),
    Step(
        "step-terminals", 11, "Terminal Blocks", "phase-7",
        "project-terminal-blocks", ("step-cables", "step-components"),
        "Lay out terminal-strip points inside control panels.",
    ),
    Step(
        "step-terminations", 12, "Terminations", "phase-7",
        "project-terminations", ("step-cables", "step-terminals"),
        "Record cable-end terminations -- which conductor lands where.",
    ),
    Step(
        "step-network", 13, "Network Devices", "phase-7",
        "project-network-devices", ("step-locations", "step-panels"),
        "Add network devices -- switches, gateways, routers, etc.",
    ),
    Step(
        "step-calcs", 14, "Calculations", "phase-8", "project-calculations", (),
        "Record engineering calculations run against the populated database.",
    ),
    Step(
        "step-qaqc", 15, "QA/QC Checks", "phase-8", "project-qaqc-checks", (),
        "Run completeness and integrity QA/QC checks on the project.",
    ),
]

# Catalog tables checked for readiness when the pipeline is opened.
CATALOG_TABLES = [
    "catalog-manufacturers",
    "catalog-equipment",
    "catalog-cables",
    "catalog-instruments",
    "catalog-io-modules",
    "catalog-devices",
]


def definition() -> dict:
    """The static pipeline definition (no project data)."""
    return {
        "phases": [{"id": p.id, "title": p.title} for p in PHASES],
        "steps": [
            {
                "id": s.id,
                "number": s.number,
                "title": s.title,
                "phase_id": s.phase_id,
                "table": s.table,
                "table_label": get_table(s.table).label,
                "prerequisites": list(s.prerequisites),
                "description": s.description,
            }
            for s in STEPS
        ],
    }


def _row_count(db: Session, slug: str, project_id: int) -> int:
    """Rows of a step's table for the project (the project step always counts 1)."""
    spec = get_table(slug)
    if slug == "projects":
        return 1  # the pipeline already operates on one selected project
    stmt = select(func.count()).select_from(spec.model)
    if spec.project_scoped:
        stmt = stmt.where(spec.model.project_id == project_id)
    return db.scalar(stmt) or 0


def _reviewed_map(db: Session, project_id: int) -> dict[str, bool]:
    rows = db.scalars(
        select(ProjectPipelineProgress).where(
            ProjectPipelineProgress.project_id == project_id
        )
    ).all()
    return {r.step_id: r.reviewed for r in rows}


def _catalog_readiness(db: Session) -> list[dict]:
    result = []
    for slug in CATALOG_TABLES:
        spec = get_table(slug)
        count = db.scalar(select(func.count()).select_from(spec.model)) or 0
        result.append(
            {"table": slug, "label": spec.label, "count": count, "empty": count == 0}
        )
    return result


def compute_status(db: Session, project_id: int) -> dict:
    """Per-step status for a project: row counts, readiness, reviewed, progress."""
    counts = {s.id: _row_count(db, s.table, project_id) for s in STEPS}
    reviewed = _reviewed_map(db, project_id)

    steps_out: list[dict] = []
    for s in STEPS:
        met = sum(1 for p in s.prerequisites if counts.get(p, 0) > 0)
        if not s.prerequisites or met == len(s.prerequisites):
            readiness = "ready"  # green
        elif met > 0:
            readiness = "partial"  # yellow
        else:
            readiness = "blocked"  # gray
        row_count = counts[s.id]
        is_reviewed = reviewed.get(s.id, False)
        steps_out.append(
            {
                "id": s.id,
                "number": s.number,
                "title": s.title,
                "phase_id": s.phase_id,
                "table": s.table,
                "table_label": get_table(s.table).label,
                "prerequisites": list(s.prerequisites),
                "description": s.description,
                "row_count": row_count,
                "readiness": readiness,
                "reviewed": is_reviewed,
                "has_data": row_count > 0,
            }
        )

    done = sum(1 for s in steps_out if s["has_data"] or s["reviewed"])
    progress = round(100 * done / len(steps_out)) if steps_out else 0
    recommended = next(
        (s["id"] for s in steps_out if not s["has_data"] and not s["reviewed"]),
        None,
    )

    return {
        "project_id": project_id,
        "phases": [{"id": p.id, "title": p.title} for p in PHASES],
        "steps": steps_out,
        "progress_percent": progress,
        "recommended_step_id": recommended,
        "catalog_readiness": _catalog_readiness(db),
    }
