"""Filesystem browse router.

Backs the Database Browser's file picker: the browser cannot read the OS
filesystem itself, so the (local-only) backend lists directories and database
files on request.  This router works whether or not a database is connected.
"""

from __future__ import annotations

import os
import string
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/fs", tags=["File system"])

# Extensions treated as openable database files.
_DB_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}


class FsEntry(BaseModel):
    name: str
    path: str
    size_bytes: int | None = None
    modified: str | None = None


class FsListing(BaseModel):
    path: str
    parent: str | None
    directories: list[FsEntry]
    files: list[FsEntry]
    drives: list[str]


def _drives() -> list[str]:
    """Available drive roots (Windows) or the filesystem root (POSIX)."""
    if os.name != "nt":
        return ["/"]
    return [f"{letter}:\\" for letter in string.ascii_uppercase if os.path.exists(f"{letter}:\\")]


@router.get("/browse", response_model=FsListing)
def browse(
    path: str | None = Query(
        None, description="Directory to list. Defaults to the user's home folder."
    ),
):
    """List the sub-directories and database files of a directory."""
    target = Path(path).expanduser() if path else Path.home()
    try:
        target = target.resolve()
    except OSError:
        raise HTTPException(400, "Invalid path.")
    if not target.is_dir():
        raise HTTPException(400, f"Not a directory: {target}")

    try:
        entries = list(target.iterdir())
    except PermissionError:
        raise HTTPException(403, f"Permission denied: {target}")
    except OSError as exc:
        raise HTTPException(400, f"Cannot read folder: {exc}")

    directories: list[dict] = []
    files: list[dict] = []
    for entry in entries:
        try:
            if entry.name.startswith("."):
                continue  # skip dotfiles / dot-folders
            if entry.is_dir():
                directories.append({"name": entry.name, "path": str(entry)})
            elif entry.suffix.lower() in _DB_EXTENSIONS:
                stat = entry.stat()
                files.append(
                    {
                        "name": entry.name,
                        "path": str(entry),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(
                            stat.st_mtime, tz=timezone.utc
                        ).isoformat(),
                    }
                )
        except (PermissionError, OSError):
            continue  # skip entries we cannot inspect

    directories.sort(key=lambda d: d["name"].lower())
    files.sort(key=lambda f: f["name"].lower())
    parent = str(target.parent) if target.parent != target else None

    return {
        "path": str(target),
        "parent": parent,
        "directories": directories,
        "files": files,
        "drives": _drives(),
    }
