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

# Directory that holds every project database file.  Each *.db file here is one
# "database" in the Database Browser.  Created on first import so the directory
# always exists.
DATABASES_DIR = BACKEND_DIR / "databases"
DATABASES_DIR.mkdir(exist_ok=True)

# Name of the database created by the standard setup flow / seed script.
DEFAULT_DATABASE = "project.db"

# Small JSON file remembering the last connected database, so the app can
# reconnect to it automatically on the next launch.
STATE_FILE = BACKEND_DIR / ".db_state.json"

# Fallback database URL for the Alembic command-line tool (``alembic upgrade
# head``).  The running application selects its database at runtime via the
# Database Browser; this constant only matters when alembic is invoked directly.
DATABASE_URL = os.environ.get(
    "EPDB_DATABASE_URL",
    f"sqlite:///{DATABASES_DIR / DEFAULT_DATABASE}",
)
