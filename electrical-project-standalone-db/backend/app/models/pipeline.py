"""Model for the guided Build-Project pipeline.

The pipeline itself (phases, steps, prerequisites) is a static definition in
``app.pipeline``.  The only thing that needs persisting is the designer's
progress: a ``reviewed`` flag per (project, step), so a step can be marked done
even when it legitimately has zero rows.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .base import CommonMixin


class ProjectPipelineProgress(Base, CommonMixin):
    """One row per (project, pipeline step) tracking the ``reviewed`` flag."""

    __tablename__ = "project_pipeline_progress"
    __table_args__ = (
        UniqueConstraint("project_id", "step_id", name="uq_pipeline_progress_step"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    step_id: Mapped[str] = mapped_column(String(60), nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
