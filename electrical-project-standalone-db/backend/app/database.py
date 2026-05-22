"""Declarative base and engine construction.

The application no longer owns a single fixed engine: the Database Browser lets
the user connect to one of several database files at runtime.  The live engine
and session factory are therefore held by :mod:`app.db_manager`; this module
only provides the shared :class:`Base` and a factory for building a correctly
configured engine for a given URL.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """Turn on foreign-key enforcement for a new SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(url: str) -> Engine:
    """Build an engine for ``url`` with the project's standard settings.

    SQLite needs ``check_same_thread=False`` (FastAPI may touch a session from
    another thread) and an explicit ``PRAGMA foreign_keys=ON`` per connection.
    Both are no-ops / unnecessary on PostgreSQL.
    """
    is_sqlite = url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    if is_sqlite:
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session from the currently connected database.

    Delegates to the runtime database manager.  Imported lazily to avoid a
    circular import at module load time.  Raises HTTP 409 when no database is
    connected.
    """
    from .db_manager import manager

    yield from manager.get_session()
