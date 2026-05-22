"""Schemas for the project-scoped composite endpoints.

These back two views that the frontend needs as a single round-trip:

* the project dashboard -- a count per Class B chapter, so the user can see at a
  glance how completely the database reflects the project;
* the full project export -- every Class B row for one project, with catalog
  data merged in, used to populate the whole UI for a selected project.
"""

from __future__ import annotations

from .common import ORMModel
from .projects import (
    ControlPanelRead,
    LocationRead,
    PanelCircuitRead,
    PanelComponentMerged,
    ProjectCableMerged,
    ProjectEquipmentMerged,
    ProjectInstrumentMerged,
    ProjectRead,
    IOPointMerged,
)


class ProjectDashboard(ORMModel):
    """Row counts per Class B chapter for one project."""

    project: ProjectRead
    locations: int
    equipment: int
    panel_circuits: int
    cables: int
    instruments: int
    io_points: int
    control_panels: int
    panel_components: int
    total: int  # sum of all Class B rows for the project


class ProjectAllData(ORMModel):
    """Every Class B row for one project, catalog data merged in."""

    project: ProjectRead
    locations: list[LocationRead]
    equipment: list[ProjectEquipmentMerged]
    panel_circuits: list[PanelCircuitRead]
    cables: list[ProjectCableMerged]
    instruments: list[ProjectInstrumentMerged]
    io_points: list[IOPointMerged]
    control_panels: list[ControlPanelRead]
    panel_components: list[PanelComponentMerged]
