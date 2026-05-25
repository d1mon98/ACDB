"""Application-wide configuration.

Stage 1 runs entirely on the local machine.  The application can hold several
SQLite database files under ``backend/databases/`` and connect to one at a time
through the Database Browser; this module defines where those files live and
the fallback target for the Alembic command-line tool.
"""

from __future__ import annotations

import os
from pathlib import Path

# Human-readable application name.  Used in the FastAPI title, the README and
# echoed by the frontend.  Keep this in sync with the value in the frontend.
APP_NAME = "Electrical Project Standalone DB"

# backend/ directory (this file lives in backend/app/config.py).
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Directory that holds every database file.  Split into two sub-folders so the
# Database Browser can manage CATALOG databases (system reference data, shared
# across all projects) and PROJECT databases (one per electrical project)
# independently.  Created on first import so the directories always exist.
DATABASES_DIR = BACKEND_DIR / "databases"
CATALOG_DATABASES_DIR = DATABASES_DIR / "catalogs"
PROJECT_DATABASES_DIR = DATABASES_DIR / "projects"
DATABASES_DIR.mkdir(exist_ok=True)
CATALOG_DATABASES_DIR.mkdir(exist_ok=True)
PROJECT_DATABASES_DIR.mkdir(exist_ok=True)

# Default file names created by the standard setup flow / seed script.
DEFAULT_CATALOG_DATABASE = "system_catalog.db"
DEFAULT_PROJECT_DATABASE = "project.db"
# Kept for backward compatibility with anything still referencing the old name.
DEFAULT_DATABASE = DEFAULT_PROJECT_DATABASE

# Small JSON file remembering both the last-connected catalog database and the
# last-connected project database, so the app can reconnect to them on launch.
# Schema: {"catalog": {"last": str|None, "recent": [str]},
#          "project": {"last": str|None, "recent": [str]}}
STATE_FILE = BACKEND_DIR / ".db_state.json"

# Fallback database URLs for the Alembic command-line tool.  The running
# application selects its databases at runtime via the Database Browser; these
# constants only matter when alembic is invoked directly.
CATALOG_DATABASE_URL = os.environ.get(
    "EPDB_CATALOG_DATABASE_URL",
    f"sqlite:///{CATALOG_DATABASES_DIR / DEFAULT_CATALOG_DATABASE}",
)
PROJECT_DATABASE_URL = os.environ.get(
    "EPDB_PROJECT_DATABASE_URL",
    f"sqlite:///{PROJECT_DATABASES_DIR / DEFAULT_PROJECT_DATABASE}",
)
# Backward-compat alias (old code may still import DATABASE_URL).
DATABASE_URL = PROJECT_DATABASE_URL
