"""REST router for the Database Browser (dual-database).

The application owns TWO databases at runtime:

* a CATALOG database, exposed under ``/api/catalog-databases``;
* a PROJECT database, exposed under ``/api/project-databases``.

Both surfaces share the same schemas (a ``DatabaseInfo`` is a ``DatabaseInfo``
regardless of role) and the same CRUD-shape (list / create / connect /
disconnect / open / rename / delete).  The pre-split single-role endpoints
under ``/api/databases`` remain as a backward-compatible alias for the
PROJECT database, so existing UI / scripts continue to work while the
frontend is rolled forward.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db_manager import (
    DatabaseManager,
    catalog_manager,
    project_manager,
)


# ---- schemas -------------------------------------------------------------


class DatabaseInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    modified: str
    connected: bool


class RecentDatabase(BaseModel):
    path: str
    name: str
    exists: bool


class ConnectionStatus(BaseModel):
    role: str
    connected: bool
    current: str | None
    path: str | None


class DatabaseList(ConnectionStatus):
    items: list[DatabaseInfo]
    recent: list[RecentDatabase]


class CreateBody(BaseModel):
    name: str


class RenameBody(BaseModel):
    new_name: str


class OpenBody(BaseModel):
    path: str


class CombinedStatus(BaseModel):
    catalog: ConnectionStatus
    project: ConnectionStatus


# ---- helpers -------------------------------------------------------------


def _status(mgr: DatabaseManager) -> dict:
    return {
        "role": mgr.role,
        "connected": mgr.connected,
        "current": mgr.current,
        "path": mgr.current_path,
    }


def _build_router(mgr: DatabaseManager, prefix: str, tag: str) -> APIRouter:
    """Build a CRUD router for one of the two database managers."""
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=DatabaseList)
    def list_all():
        return {
            "items": mgr.list_databases(),
            "recent": mgr.recent(),
            **_status(mgr),
        }

    @router.get("/status", response_model=ConnectionStatus)
    def status():
        return _status(mgr)

    @router.post("", response_model=DatabaseInfo, status_code=201)
    def create(body: CreateBody):
        try:
            return mgr.create_database(body.name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except FileExistsError as e:
            raise HTTPException(409, str(e))

    @router.post("/disconnect", response_model=ConnectionStatus)
    def disconnect():
        mgr.disconnect()
        return _status(mgr)

    @router.post("/open", response_model=ConnectionStatus)
    def open_db(body: OpenBody):
        try:
            mgr.connect_path(body.path)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except FileNotFoundError as e:
            raise HTTPException(404, str(e))
        except OSError as e:
            raise HTTPException(400, f"Could not open that file: {e}")
        return _status(mgr)

    @router.post("/{name}/connect", response_model=ConnectionStatus)
    def connect(name: str):
        try:
            mgr.connect(name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except FileNotFoundError as e:
            raise HTTPException(404, str(e))
        return _status(mgr)

    @router.put("/{name}", response_model=DatabaseInfo)
    def rename(name: str, body: RenameBody):
        try:
            return mgr.rename_database(name, body.new_name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except FileNotFoundError as e:
            raise HTTPException(404, str(e))
        except FileExistsError as e:
            raise HTTPException(409, str(e))

    @router.delete("/{name}", status_code=204)
    def delete(name: str):
        try:
            mgr.delete_database(name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except FileNotFoundError as e:
            raise HTTPException(404, str(e))
        except PermissionError as e:
            raise HTTPException(409, str(e))

    return router


# ---- routers -------------------------------------------------------------


catalog_router = _build_router(
    catalog_manager,
    prefix="/api/catalog-databases",
    tag="Catalog Databases",
)
project_router = _build_router(
    project_manager,
    prefix="/api/project-databases",
    tag="Project Databases",
)
# Backward-compat alias: /api/databases mirrors the project database surface,
# matching the pre-split UI's expectations.
legacy_router = _build_router(
    project_manager,
    prefix="/api/databases",
    tag="Databases (legacy alias)",
)


# Combined status convenience endpoint -- the header shows both at once.
status_router = APIRouter(prefix="/api/db-status", tags=["Databases"])


@status_router.get("", response_model=CombinedStatus)
def combined_status():
    return {
        "catalog": _status(catalog_manager),
        "project": _status(project_manager),
    }
