"""Runtime database connection manager (the Database Browser back end).

The application holds TWO separate databases at the same time:

* a **catalog** database (``databases/catalogs/*.db``) containing the system
  reference data — catalog_groups, the catalog_* tables, all extended cat_*
  tables, plus the custom-table schema/rows.  This database is shared across
  every project.
* a **project** database (``databases/projects/*.db``) containing the actual
  project rows — projects, project_equipment, project_cables, project_*.
  Each project file is fully standalone.

The two databases are managed by two ``DatabaseManager`` instances of the same
class, parameterised with their role (catalog vs project), their managed folder,
the table that identifies a valid database file, and the function that creates
the schema in a fresh database.  Endpoints that need catalog data depend on
``get_catalog_db``; endpoints that need project data depend on ``get_project_db``.

A database is "connected" when its manager holds a live session factory; an
endpoint returns HTTP 409 while the database it needs is not connected.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections.abc import Callable, Generator
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import (
    CATALOG_DATABASES_DIR,
    DEFAULT_CATALOG_DATABASE,
    DEFAULT_PROJECT_DATABASE,
    PROJECT_DATABASES_DIR,
    STATE_FILE,
)
from .database import Base, make_engine

# A managed database name (without the .db extension) is restricted to a safe,
# simple character set -- this is also the guard against path traversal inside
# the managed folders.
_NAME_RE = re.compile(r"[A-Za-z0-9 _-]+")

# How many recently opened databases to remember (per role).
_RECENT_LIMIT = 10


# --------------------------------------------------------------------------
# Name / path handling
# --------------------------------------------------------------------------


def safe_db_filename(raw: str) -> str:
    """Validate a user-supplied name and return a safe ``*.db`` filename."""
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


def _resolve_managed(folder: Path, filename: str) -> Path:
    """Resolve ``filename`` inside ``folder`` (guards against path escape)."""
    path = (folder / filename).resolve()
    if path.parent != folder.resolve():
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


# --------------------------------------------------------------------------
# Combined state file (catalog + project)
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


def _role_state(state: dict, role: str) -> dict:
    sub = state.get(role)
    return sub if isinstance(sub, dict) else {}


# --------------------------------------------------------------------------
# Schema creation -- catalog vs project subset of Base.metadata
# --------------------------------------------------------------------------


# Tables that live in the CATALOG database.  Filled lazily on first use so that
# importing this module does not require importing every model upfront.
_CATALOG_TABLES: set[str] | None = None
_PROJECT_TABLES: set[str] | None = None


def _ensure_table_sets() -> None:
    """Populate _CATALOG_TABLES and _PROJECT_TABLES (idempotent)."""
    global _CATALOG_TABLES, _PROJECT_TABLES
    if _CATALOG_TABLES is not None:
        return

    # Importing the model modules registers them on Base.metadata.
    from .models import (  # noqa: F401 -- side-effect imports
        catalog_groups,
        catalogs,
        catalogs_ext,
        custom_tables,
        pipeline,
        projects,
    )

    # Catalog tables: catalog_groups + catalog_column_defs + catalog_custom_rows
    # + every catalog_* table + every cat_* table.
    catalog_names: set[str] = set()
    project_names: set[str] = set()
    for name in Base.metadata.tables:
        if name.startswith("project_") or name == "projects":
            project_names.add(name)
        else:
            catalog_names.add(name)

    _CATALOG_TABLES = catalog_names
    _PROJECT_TABLES = project_names


def create_catalog_schema(engine: Engine) -> None:
    """Create every catalog table in ``engine`` if it does not already exist."""
    _ensure_table_sets()
    tables = [Base.metadata.tables[n] for n in _CATALOG_TABLES if n in Base.metadata.tables]
    Base.metadata.create_all(engine, tables=tables, checkfirst=True)


def create_project_schema(engine: Engine) -> None:
    """Create every project table in ``engine`` if it does not already exist."""
    _ensure_table_sets()
    tables = [Base.metadata.tables[n] for n in _PROJECT_TABLES if n in Base.metadata.tables]
    Base.metadata.create_all(engine, tables=tables, checkfirst=True)


# --------------------------------------------------------------------------
# The DatabaseManager (one instance per role)
# --------------------------------------------------------------------------


class DatabaseManager:
    """Holds the engine / session factory for one of the two databases.

    Each role (``"catalog"`` or ``"project"``) gets its own manager instance,
    its own managed folder, and its own validation table.  The two managers
    persist their state in separate sections of the same JSON state file.
    """

    def __init__(
        self,
        *,
        role: str,
        databases_dir: Path,
        default_database: str,
        required_table: str,
        create_schema: Callable[[Engine], None],
        display_label: str,
    ) -> None:
        self.role = role
        self.databases_dir = databases_dir
        self.default_database = default_database
        self.required_table = required_table
        self.create_schema = create_schema
        self.display_label = display_label

        self._engine: Engine | None = None
        self._session_factory: sessionmaker | None = None
        self._current_path: Path | None = None

    # ---- properties --------------------------------------------------------

    @property
    def connected(self) -> bool:
        return self._session_factory is not None

    @property
    def current_path(self) -> str | None:
        return str(self._current_path) if self._current_path else None

    @property
    def current(self) -> str | None:
        return self._current_path.name if self._current_path else None

    # ---- helpers -----------------------------------------------------------

    def _managed_path(self, filename: str) -> Path:
        return _resolve_managed(self.databases_dir, filename)

    def _validate(self, path: Path) -> None:
        """Check that ``path`` is a usable database for this role."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise ValueError(f"Not a file: {path}")
        try:
            conn = sqlite3.connect(str(path))
            try:
                found = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (self.required_table,),
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.DatabaseError:
            raise ValueError(f"'{path.name}' is not a valid SQLite database file.")
        if found is None:
            raise ValueError(
                f"'{path.name}' is not a valid {self.display_label} database "
                f"(it has no '{self.required_table}' table). Use Create Database "
                f"to make a new one."
            )

    def _dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None
        self._current_path = None

    # ---- state file --------------------------------------------------------

    def _remember(self, path: Path) -> None:
        state = _load_state()
        sub = dict(_role_state(state, self.role))
        full = str(path)
        sub["last"] = full
        recent = [r for r in sub.get("recent", []) if r != full]
        recent.insert(0, full)
        sub["recent"] = recent[:_RECENT_LIMIT]
        state[self.role] = sub
        _save_state(state)

    def _forget_last(self) -> None:
        state = _load_state()
        sub = dict(_role_state(state, self.role))
        sub["last"] = None
        state[self.role] = sub
        _save_state(state)

    def recent(self) -> list[dict]:
        state = _load_state()
        sub = _role_state(state, self.role)
        result = []
        for entry in sub.get("recent", []):
            p = Path(entry)
            result.append({"path": entry, "name": p.name, "exists": p.exists()})
        return result

    # ---- connect / disconnect ---------------------------------------------

    def connect_path(self, raw_path: str) -> None:
        """Connect to a database file anywhere on the filesystem."""
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = self.databases_dir / path
        path = path.resolve()

        self._validate(path)

        self._dispose()
        self._engine = make_engine(f"sqlite:///{path}")
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, autocommit=False, future=True
        )
        self._current_path = path
        self._remember(path)

    def connect(self, name: str) -> None:
        """Connect to a managed database, by name."""
        self.connect_path(str(self._managed_path(safe_db_filename(name))))

    def disconnect(self) -> None:
        self._dispose()
        self._forget_last()

    def get_session(self) -> Generator[Session, None, None]:
        if self._session_factory is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"No {self.display_label} database is connected. "
                    f"Open the Database Browser to connect to or create one."
                ),
            )
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    def startup(self) -> None:
        """On launch, reconnect to the last-used database (if it still exists)."""
        candidates: list[str] = []
        last = _role_state(_load_state(), self.role).get("last")
        if last:
            candidates.append(last)
        candidates.append(str(self._managed_path(self.default_database)))
        for candidate in candidates:
            try:
                self.connect_path(candidate)
                return
            except (FileNotFoundError, ValueError, OSError):
                continue
        # No database to connect to -- stay disconnected.

    # ---- file operations on the managed folder ---------------------------

    def list_databases(self) -> list[dict]:
        current = self.current_path
        return [
            _info(p.resolve(), connected=(str(p.resolve()) == current))
            for p in sorted(self.databases_dir.glob("*.db"))
        ]

    def create_database(self, name: str) -> dict:
        """Create a new database file in the managed folder, schema applied."""
        filename = safe_db_filename(name)
        path = self._managed_path(filename)
        if path.exists():
            raise FileExistsError(f"A database named '{filename}' already exists.")
        engine = make_engine(f"sqlite:///{path}")
        try:
            self.create_schema(engine)
        finally:
            engine.dispose()
        return _info(path, connected=False)

    def rename_database(self, name: str, new_name: str) -> dict:
        src = self._managed_path(safe_db_filename(name))
        dst = self._managed_path(safe_db_filename(new_name))
        if not src.exists():
            raise FileNotFoundError(f"Database '{src.name}' does not exist.")
        if dst.exists():
            raise FileExistsError(f"A database named '{dst.name}' already exists.")

        was_connected = self.current_path == str(src.resolve())
        if was_connected:
            self.disconnect()
        os.rename(src, dst)
        if was_connected:
            self.connect(dst.name)
        return _info(dst, connected=was_connected)

    def delete_database(self, name: str) -> None:
        path = self._managed_path(safe_db_filename(name))
        if not path.exists():
            raise FileNotFoundError(f"Database '{path.name}' does not exist.")
        if self.current_path == str(path.resolve()):
            raise PermissionError(
                "This database is currently connected. Disconnect from it before "
                "deleting it."
            )
        path.unlink()


# --------------------------------------------------------------------------
# Singletons -- one manager per role
# --------------------------------------------------------------------------


catalog_manager = DatabaseManager(
    role="catalog",
    databases_dir=CATALOG_DATABASES_DIR,
    default_database=DEFAULT_CATALOG_DATABASE,
    required_table="catalog_groups",
    create_schema=create_catalog_schema,
    display_label="catalog",
)

project_manager = DatabaseManager(
    role="project",
    databases_dir=PROJECT_DATABASES_DIR,
    default_database=DEFAULT_PROJECT_DATABASE,
    required_table="projects",
    create_schema=create_project_schema,
    display_label="project",
)

# Backward-compatible alias -- some older code still imports ``manager``.
manager = project_manager
