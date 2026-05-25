"""Declarative base and engine construction.

The application owns TWO databases at runtime:

* the **catalog** database (system reference data, shared across projects);
* the **project** database (one electrical project's actual rows).

Each is managed by its own ``DatabaseManager`` in :mod:`app.db_manager`.
Endpoints depend on either :func:`get_catalog_db` or :func:`get_project_db`
to pick the right session.  The legacy :func:`get_db` symbol is kept as an
alias for :func:`get_catalog_db` so any unmigrated caller still resolves.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import NullPool


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model.

    Both the catalog DB and the project DB share this metadata; we create only
    the relevant subset of tables in each (see ``db_manager.create_*_schema``).
    """


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """Turn on foreign-key enforcement for a new SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(url: str) -> Engine:
    """Build an engine for ``url`` with the project's standard settings.

    SQLite uses NullPool so connections are never held open in a pool —
    this ensures file handles are released immediately on disconnect/rename/delete.
    """
    is_sqlite = url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    pool_kwargs = {"poolclass": NullPool} if is_sqlite else {}
    engine = create_engine(url, connect_args=connect_args, future=True, **pool_kwargs)
    if is_sqlite:
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def get_catalog_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session bound to the connected catalog DB."""
    from .db_manager import catalog_manager

    yield from catalog_manager.get_session()


def get_project_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session bound to the connected project DB."""
    from .db_manager import project_manager

    yield from project_manager.get_session()


# Backward-compat alias.  Anything still depending on ``get_db`` resolves to the
# catalog DB by default -- that's where the bulk of the reference data lives.
get_db = get_catalog_db
