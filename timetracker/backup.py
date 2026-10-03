"""Consistent local snapshots of the activity database."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path


def _same_file(left: Path, right: Path) -> bool:
    if left.resolve() == right.resolve():
        return True
    try:
        return left.exists() and right.exists() and left.samefile(right)
    except OSError:
        return False


def backup_activity_database(source: str | Path, destination: str | Path) -> Path:
    """Copy committed activity into ``destination`` without changing ``source``.

    The destination is replaced only after the SQLite backup succeeds. A failed
    attempt removes only the temporary file created for that attempt.
    """

    source_path = Path(source)
    destination_path = Path(destination)
    if not source_path.is_file():
        raise FileNotFoundError(f"Activity database not found: {source_path}")
    if _same_file(source_path, destination_path):
        raise ValueError("The backup destination must be a different file from the activity database")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination_path.name}.",
        suffix=".tmp",
        dir=destination_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    source_connection = sqlite3.connect(source_path)
    try:
        destination_connection = sqlite3.connect(temporary_path)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
        temporary_path.replace(destination_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    finally:
        source_connection.close()
    return destination_path
