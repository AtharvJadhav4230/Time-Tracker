from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from timetracker.backup import backup_activity_database
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState


class BackupTests(unittest.TestCase):
    def _rows(self, path: Path, start: datetime) -> list[str]:
        with ActivityDatabase(path) as database:
            periods = database.periods_between(start - timedelta(days=1), start + timedelta(days=1))
        return [period.window_title for period in periods]

    def test_open_connection_write_is_included_and_source_stays_unchanged(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            destination = root / "nested" / "backup.db"
            with ActivityDatabase(source) as database:
                period_id = database.create_period(ActivityState("Code.exe", "Fictional"), start)
                database.update_period(period_id, start, start + timedelta(minutes=3))
                backup_activity_database(source, destination)
                original = database.periods_between(start - timedelta(days=1), start + timedelta(days=1))
            copied = self._rows(destination, start)
            after = self._rows(source, start)
        self.assertEqual(copied, ["Fictional"])
        self.assertEqual(after, [period.window_title for period in original])
        self.assertEqual(original[0].duration_seconds, 180)

    def test_same_destination_is_rejected_while_the_source_stays_open(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "activity.db"
            with ActivityDatabase(source) as database:
                database.create_period(ActivityState("Code.exe", "Fictional"), start)
                with self.assertRaises(ValueError):
                    backup_activity_database(source, source)
                titles = [
                    period.window_title
                    for period in database.periods_between(
                        start - timedelta(days=1), start + timedelta(days=1)
                    )
                ]
            self.assertEqual(titles, ["Fictional"])
            self.assertTrue(source.read_bytes().startswith(b"SQLite format 3"))

    def test_failed_backup_preserves_existing_files(self) -> None:
        start = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "activity.db"
            destination = root / "backup.db"
            sibling = root / "backup.db.partial"
            sibling.write_text("keep this sibling", encoding="utf-8")
            with ActivityDatabase(source) as database:
                period_id = database.create_period(ActivityState("Code.exe", "Fictional"), start)
                database.update_period(period_id, start, start + timedelta(minutes=3))
            backup_activity_database(source, destination)

            real_connect = sqlite3.connect

            def connect(path, *args, **kwargs):  # type: ignore[no-untyped-def]
                if Path(path).resolve() != source.resolve():
                    raise sqlite3.DatabaseError("disk full")
                return real_connect(path, *args, **kwargs)

            with mock.patch("timetracker.backup.sqlite3.connect", side_effect=connect):
                with self.assertRaises(sqlite3.DatabaseError):
                    backup_activity_database(source, destination)

            self.assertEqual(self._rows(destination, start), ["Fictional"])
            self.assertEqual(sibling.read_text(encoding="utf-8"), "keep this sibling")
            self.assertEqual(list(root.glob("backup.db*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
