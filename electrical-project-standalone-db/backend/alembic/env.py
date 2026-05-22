"""Alembic environment.

The target database URL is resolved in this order:

1. an URL already set on the Alembic ``Config`` (this is how the application
   creates the schema in a brand-new database file at runtime -- see
   ``app.db_manager.apply_migrations``);
2. otherwise ``app.config.DATABASE_URL`` -- the command-line default.

``render_as_batch=True`` keeps migrations working on SQLite (which cannot ALTER
most things in place); it is harmless on PostgreSQL.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool

from alembic import context

# Make the backend/ directory importable so "import app" works regardless of
# where alembic is invoked from.
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import DATABASE_URL as DEFAULT_URL  # noqa: E402
from app.database import Base  # noqa: E402
import app.models  # noqa: E402,F401  (imported for its side effect: registers all tables)

config = context.config

# Resolve the URL: an explicitly-set one wins, else the command-line default.
database_url = config.get_main_option("sqlalchemy.url") or DEFAULT_URL
config.set_main_option("sqlalchemy.url", database_url)

# Only configure logging when run from the alembic.ini command line; the
# programmatic Config used at runtime has no .ini file and should stay quiet.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emits SQL)."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = create_engine(database_url, poolclass=pool.NullPool, future=True)
    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
