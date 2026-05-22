"""REST router for the Database Browser.

Manages the database files -- list, create, rename, delete -- the connect /
disconnect of the active database, and opening a database from anywhere on the
filesystem.  These endpoints work while no database is connected.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import db_manager
from ..db_manager import manager

router = APIRouter(prefix="/api/databases", tags=["Databases"])


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


def _status() -> dict:
    return {
        "connected": manager.connected,
        "current": manager.current,
        "path": manager.current_path,
    }


# ---- routes --------------------------------------------------------------


@router.get("", response_model=DatabaseList)
def list_databases():
    """List managed database files, recent databases, and connection status."""
    return {
        "items": db_manager.list_databases(),
        "recent": db_manager.recent_databases(),
        **_status(),
    }


@router.get("/status", response_model=ConnectionStatus)
def connection_status():
    """Which database, if any, is currently connected."""
    return _status()


@router.post("", response_model=DatabaseInfo, status_code=201)
def create_database(body: CreateBody):
    """Create a new database file (in the managed folder) with the schema applied."""
    try:
        return db_manager.create_database(body.name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileExistsError as e:
        raise HTTPException(409, str(e))


@router.post("/disconnect", response_model=ConnectionStatus)
def disconnect():
    """Close the active connection; the app then has no database."""
    manager.disconnect()
    return _status()


@router.post("/open", response_model=ConnectionStatus)
def open_database(body: OpenBody):
    """Connect to a database file at an arbitrary filesystem path."""
    try:
        manager.connect_path(body.path)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except OSError as e:
        raise HTTPException(400, f"Could not open that file: {e}")
    return _status()


@router.post("/{name}/connect", response_model=ConnectionStatus)
def connect(name: str):
    """Make the named managed database the active one."""
    try:
        manager.connect(name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    return _status()


@router.put("/{name}", response_model=DatabaseInfo)
def rename_database(name: str, body: RenameBody):
    """Rename a managed database file."""
    try:
        return db_manager.rename_database(name, body.new_name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except FileExistsError as e:
        raise HTTPException(409, str(e))


@router.delete("/{name}", status_code=204)
def delete_database(name: str):
    """Delete a managed database file (must be disconnected first)."""
    try:
        db_manager.delete_database(name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except PermissionError as e:
        raise HTTPException(409, str(e))
