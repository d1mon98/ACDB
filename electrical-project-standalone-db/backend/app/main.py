"""FastAPI application entry point.

Run with::

    uvicorn app.main:app --reload

The app exposes:

* ``/api/...``  -- the REST API (CRUD for all 15 tables, merged views, the
  project dashboard and full-export endpoints);
* ``/docs``     -- interactive OpenAPI documentation;
* ``/``         -- the built frontend, *if* ``frontend/dist`` exists (otherwise
  run the Vite dev server separately -- see the README).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

from .config import APP_NAME, BACKEND_DIR
from .db_manager import catalog_manager, project_manager
from .routers import (
    catalog_groups,
    catalogs,
    catalogs_ext,
    custom_tables,
    databases,
    erd,
    filesystem,
    project_tables,
    projects,
    usage,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Reconnect to the last-used catalog and project databases on startup."""
    catalog_manager.startup()
    project_manager.startup()
    yield


app = FastAPI(
    title=APP_NAME,
    description=(
        "Standalone database for an industrial electrical power-distribution "
        "and I&C project. Class A catalogs hold reusable reference data; "
        "Class B project tables merge a catalog record with project-specific "
        "data via a foreign key."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# The Vite dev server runs on a different origin during development, so the
# browser needs CORS permission to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Turn raw database constraint errors into clear, human-readable messages."""
    raw = str(exc.orig) if exc.orig is not None else str(exc)
    low = raw.lower()

    if "foreign key" in low:
        detail = (
            "This change conflicts with a foreign-key relationship: a "
            "referenced record does not exist, or this record is still "
            "referenced by other rows. Remove or repoint those references first."
        )
    elif "unique" in low:
        detail = f"A record with the same unique value already exists. ({raw})"
    elif "check constraint" in low and "catalog_or_custom" in low:
        detail = (
            "A project row must either reference a catalog record or supply "
            "its custom permanent details -- it cannot have neither."
        )
    elif "not null" in low:
        detail = f"A required field is missing. ({raw})"
    else:
        detail = f"The operation violates a database constraint: {raw}"

    return JSONResponse(status_code=409, content={"detail": detail})


@app.get("/api/health", tags=["Meta"])
def health() -> dict[str, str]:
    """Simple liveness probe; also echoes the application name."""
    return {"status": "ok", "app": APP_NAME}


# --- routers --------------------------------------------------------------
app.include_router(databases.catalog_router)
app.include_router(databases.project_router)
app.include_router(databases.legacy_router)
app.include_router(databases.status_router)
app.include_router(filesystem.router)
app.include_router(erd.router)
app.include_router(catalog_groups.router)
app.include_router(custom_tables.router)
app.include_router(usage.router)
app.include_router(projects.router)
for catalog_router in catalogs.routers:
    app.include_router(catalog_router)
for ext_router in catalogs_ext.routers:
    app.include_router(ext_router)
for project_table_router in project_tables.routers:
    app.include_router(project_table_router)


# --- optional: serve the built frontend -----------------------------------
# Mounted last so it only catches paths the API did not.  During development
# this directory does not exist and the Vite dev server is used instead.
_frontend_dist = BACKEND_DIR.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
