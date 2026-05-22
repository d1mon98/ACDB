"""Runtime database connection manager (the Database Browser back end).

The application keeps a folder of project databases under ``backend/databases/``
and can also connect to a database file located *anywhere* on the filesystem
(chosen with the Database Browser's file picker).  This module owns:

* the currently connected engine and session factory,
* the file operations on the managed folder (list / create / rename / delete),
* the list of recently opened databases.

A database is "connected" when the manager holds a live session factory for it;
endpoints that touch project data go through :func:`DatabaseManager.get_session`
and return HTTP 409 while nothing is connected.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy.orm import Session, sessionmaker

from .config import BACKEND_DIR, DATABASES_DIR, DEFAULT_DATABASE, STATE_FILE
from .database import make_engine

# A managed database name (without the .db extension) is restricted to a safe,
# simple character set -- this is also the guard against path traversal inside
# the managed folder.
_NAME_RE = re.compile(r"[A-Za-z0-9 _-]+")

# How many recently opened databases to remember.
_RECENT_LIMIT = 10

# A database opened from the file picker must already be an Electrical Project
# Standalone DB database -- detected by the presence of the ``projects`` table.
_REQUIRED_TABLE = "projects"


# --------------------------------------------------------------------------
# Name / path handling
# --------------------------------------------------------------------------


def safe_db_filename(raw: str) -> str:
    """Validate a user-supplied name and return a safe ``*.db`` filename.

    Used for create / rename inside the managed folder.  Raises ``ValueError``
    with a human-readable message on anything invalid.
    """
    name = (raw or "").strip()
    if not name:
        raise ValueError("Database name cannot be empty.")
    stem = name[:-3] if name.lower().endswith(".db") else name
    stem = stem.strip()
    if not stem:
        raise ValueError("Database name cannot be empty.")
    if not _NAME_RE.fullmatch(stem):
        raise ValueError(
            "Database name may contain only letters, numbers, spaces, "
            "hyphens and underscores."
        )
    return stem + ".db"


def _managed_path(filename: str) -> Path:
    """Resolve a ``*.db`` filename inside DATABASES_DIR (guards against escape)."""
    path = (DATABASES_DIR / filename).resolve()
    if path.parent != DATABASES_DIR.resolve():
        raise ValueError("Invalid database name.")
    return path


def _info(path: Path, *, connected: bool) -> dict:
    """Build the metadata dict the API returns for one database file."""
    stat = path.stat()
    return {
        "name": path.name,
        "path": str(path),
        "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "connected": connected,
    }


def _validate_epdb_database(path: Path) -> None:
    """Check that ``path`` is a usable Electrical Project Standalone DB database.

    Raises ``FileNotFoundError`` if missing, or ``ValueError`` if it is not a
    SQLite file or not an EPDB database (no ``projects`` table).
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    try:
        conn = sqlite3.connect(str(path))
        try:
            found = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name=?",
                (_REQUIRED_TABLE,),
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        raise ValueError(f"'{path.name}' is not a valid SQLite database file.")
    if found is None:
        raise ValueError(
            f"'{path.name}' is not an Electrical Project Standalone DB database "
            f"(it has no '{_REQUIRED_TABLE}' table). Use Create Database to make "
            f"a new one."
        )


# --------------------------------------------------------------------------
# Connection-state persistence (last database + recent list)
# --------------------------------------------------------------------------


def _load_state() -> dict:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass  # remembering databases is a convenience, not critical


def _remember(path: Path) -> None:
    """Record ``path`` as the last connected database and add it to recents."""
    state = _load_state()
    full = str(path)
    state["last"] = full
    recent = [r for r in state.get("recent", []) if r != full]
    recent.insert(0, full)
    state["recent"] = recent[:_RECENT_LIMIT]
    _save_state(state)


def _clear_last() -> None:
    state = _load_state()
    state["last"] = None
    _save_state(state)


def recent_databases() -> list[dict]:
    """The recently opened databases, newest first, with an existence flag."""
    result = []
    for entry in _load_state().get("recent", []):
        path = Path(entry)
        result.append({"path": entry, "name": path.name, "exists": path.exists()})
    return result


# --------------------------------------------------------------------------
# Schema creation
# --------------------------------------------------------------------------


def apply_migrations(database_url: str) -> None:
    """Create the full schema in a database by running the Alembic migrations.

    A ``Config`` built without an .ini file is used on purpose: env.py then
    skips logging setup, so running this inside the live server does not disturb
    the server's own logging.
    """
    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")


# --------------------------------------------------------------------------
# The manager
# --------------------------------------------------------------------------


class DatabaseManager:
    """Holds the engine / session factory for the currently connected database."""

    def __init__(self) -> None:
        self._engine = None
        self._session_factory: sessionmaker | None = None
        self._current_path: Path | None = None

    @property
    def connected(self) -> bool:
        return self._session_factory is not None

    @property
    def current_path(self) -> str | None:
        """Absolute path of the connected database, or None."""
        return str(self._current_path) if self._current_path else None

    @property
    def current(self) -> str | None:
        """File name of the connected database (for display), or None."""
        return self._current_path.name if self._current_path else None

    def _dispose(self) -> None:
        """Drop the live engine, releasing the SQLite file lock."""
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None
        self._current_path = None

    def connect_path(self, raw_path: str) -> None:
        """Connect to a database file anywhere on the filesystem.

        A bare name / relative path is resolved inside the managed folder; an
        absolute path is used as-is.  The file must be an EPDB database.
        """
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = DATABASES_DIR / path
        path = path.resolve()

        _validate_epdb_database(path)  # raises FileNotFoundError / ValueError

        self._dispose()
        self._engine = make_engine(f"sqlite:///{path}")
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, autocommit=False, future=True
        )
        self._current_path = path
        _remember(path)

    def connect(self, name: str) -> None:
        """Connect to a database in the managed folder, by name."""
        self.connect_path(str(_managed_path(safe_db_filename(name))))

    def disconnect(self) -> None:
        """Close the current connection; the app then has no active database."""
        self._dispose()
        _clear_last()

    def get_session(self) -> Generator[Session, None, None]:
        """Yield a session, or raise HTTP 409 when nothing is connected."""
        if self._session_factory is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "No database is connected. Open the Database Browser to "
                    "connect to or create a database."
                ),
            )
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    def startup(self) -> None:
        """On launch, reconnect to the last-used database if it still exists."""
        candidates: list[str] = []
        last = _load_state().get("last")
        if last:
            candidates.append(last)
        candidates.append(str(_managed_path(DEFAULT_DATABASE)))
        for candidate in candidates:
            try:
                self.connect_path(candidate)
                return
            except (FileNotFoundError, ValueError, OSError):
                continue
        # No database to connect to -- stay disconnected.


manager = DatabaseManager()


# --------------------------------------------------------------------------
# File operations on the managed folder
# --------------------------------------------------------------------------


def list_databases() -> list[dict]:
    """Metadata for every ``*.db`` file in the managed databases directory."""
    current = manager.current_path
    return [
        _info(path.resolve(), connected=(str(path.resolve()) == current))
        for path in sorted(DATABASES_DIR.glob("*.db"))
    ]


def create_database(name: str) -> dict:
    """Create a new database file in the managed folder, schema applied."""
    filename = safe_db_filename(name)
    path = _managed_path(filename)
    if path.exists():
        raise FileExistsError(f"A database named '{filename}' already exists.")
    apply_migrations(f"sqlite:///{path}")
    return _info(path, connected=False)


def rename_database(name: str, new_name: str) -> dict:
    """Rename a managed database file.  Reconnects if it was the active one."""
    src = _managed_path(safe_db_filename(name))
    dst = _managed_path(safe_db_filename(new_name))
    if not src.exists():
        raise FileNotFoundError(f"Database '{src.name}' does not exist.")
    if dst.exists():
        raise FileExistsError(f"A database named '{dst.name}' already exists.")

    # The file cannot be renamed while SQLite holds it open, so drop the
    # connection first and restore it under the new name afterwards.
    was_connected = manager.current_path == str(src.resolve())
    if was_connected:
        manager.disconnect()
    os.rename(src, dst)
    if was_connected:
        manager.connect(dst.name)
    return _info(dst, connected=was_connected)


def delete_database(name: str) -> None:
    """Delete a managed database file.  Refused while it is connected."""
    path = _managed_path(safe_db_filename(name))
    if not path.exists():
        raise FileNotFoundError(f"Database '{path.name}' does not exist.")
    if manager.current_path == str(path.resolve()):
        raise PermissionError(
            "This database is currently connected. Disconnect from it before "
            "deleting it."
        )
    path.unlink()
