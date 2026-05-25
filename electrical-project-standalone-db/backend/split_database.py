"""One-shot utility: split an existing combined .db into catalog + project DBs.

After the architecture split, the application keeps catalogs and project data
in two separate SQLite files (under ``databases/catalogs/`` and
``databases/projects/`` respectively).  Existing combined databases
(``project_new.db``, ``project.db``, ``111.db``) still hold everything in one
file; this script copies their rows into freshly-created split databases so
nothing has to be re-entered by hand.

Usage::

    cd backend
    python split_database.py <source.db> [catalog_target_name] [project_target_name]

Defaults:
    catalog target  -> databases/catalogs/system_catalog.db
    project target  -> databases/projects/<source filename>
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Bootstrap: import the app so the models register on Base.metadata.
sys.path.insert(0, str(Path(__file__).parent))
from app.config import CATALOG_DATABASES_DIR, PROJECT_DATABASES_DIR  # noqa: E402
from app.database import Base, make_engine  # noqa: E402
from app.db_manager import (  # noqa: E402
    _ensure_table_sets,
    create_catalog_schema,
    create_project_schema,
)


def _open_source(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise SystemExit(f"Source database not found: {path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _existing_tables(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cur.fetchall()}


def _copy_table(
    src: sqlite3.Connection,
    dst: sqlite3.Connection,
    table: str,
) -> int:
    """Copy every row of ``table`` from src into dst.  Returns row count."""
    # Use the destination's column list (the source might have extras like
    # alembic_version we ignore, or fewer columns the dst defaults handle).
    dst_cols = [
        row[1]
        for row in dst.execute(f'PRAGMA table_info("{table}")').fetchall()
    ]
    if not dst_cols:
        return 0
    src_cols = {
        row[1]
        for row in src.execute(f'PRAGMA table_info("{table}")').fetchall()
    }
    common = [c for c in dst_cols if c in src_cols]
    if not common:
        return 0
    col_list = ", ".join(f'"{c}"' for c in common)
    placeholders = ", ".join("?" for _ in common)
    rows = src.execute(f"SELECT {col_list} FROM \"{table}\"").fetchall()
    if not rows:
        return 0
    data = [tuple(r[c] for c in common) for r in rows]
    # foreign_keys OFF for the bulk copy so cross-table insertion order doesn't
    # bite us, then ON afterwards.
    dst.execute("PRAGMA foreign_keys=OFF")
    dst.executemany(
        f'INSERT OR REPLACE INTO "{table}" ({col_list}) VALUES ({placeholders})',
        data,
    )
    dst.commit()
    dst.execute("PRAGMA foreign_keys=ON")
    return len(rows)


def split(source: Path, catalog_name: str, project_name: str) -> None:
    catalog_path = CATALOG_DATABASES_DIR / catalog_name
    project_path = PROJECT_DATABASES_DIR / project_name

    # 1. Create the two empty target databases with the right schema.
    print(f"Creating catalog DB:  {catalog_path}")
    if catalog_path.exists():
        raise SystemExit(f"Target already exists: {catalog_path}")
    cat_engine = make_engine(f"sqlite:///{catalog_path}")
    try:
        create_catalog_schema(cat_engine)
    finally:
        cat_engine.dispose()

    print(f"Creating project DB:  {project_path}")
    if project_path.exists():
        raise SystemExit(f"Target already exists: {project_path}")
    proj_engine = make_engine(f"sqlite:///{project_path}")
    try:
        create_project_schema(proj_engine)
    finally:
        proj_engine.dispose()

    # 2. Open all three connections and copy the rows.
    src = _open_source(source)
    cat_conn = sqlite3.connect(str(catalog_path))
    proj_conn = sqlite3.connect(str(project_path))

    src_tables = _existing_tables(src)
    _ensure_table_sets()
    from app.db_manager import _CATALOG_TABLES, _PROJECT_TABLES

    cat_tables = sorted(_CATALOG_TABLES & src_tables)
    proj_tables = sorted(_PROJECT_TABLES & src_tables)

    print(f"\nCatalog tables ({len(cat_tables)}):")
    for t in cat_tables:
        n = _copy_table(src, cat_conn, t)
        if n:
            print(f"  {t:40s} {n:>6} rows")

    print(f"\nProject tables ({len(proj_tables)}):")
    for t in proj_tables:
        n = _copy_table(src, proj_conn, t)
        if n:
            print(f"  {t:40s} {n:>6} rows")

    src.close()
    cat_conn.close()
    proj_conn.close()

    print("\nDone.  Connect to the new databases from the Database Browser.")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python split_database.py <source.db> "
              "[catalog_target_name] [project_target_name]")
        sys.exit(1)
    source = Path(sys.argv[1]).resolve()
    catalog_name = sys.argv[2] if len(sys.argv) > 2 else "system_catalog.db"
    project_name = sys.argv[3] if len(sys.argv) > 3 else source.name
    split(source, catalog_name, project_name)


if __name__ == "__main__":
    main()
