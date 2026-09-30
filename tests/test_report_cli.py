from __future__ import annotations

import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import report


class ReportCliSqliteFailureTests(unittest.TestCase):
    def test_fake_database_error_exits_nonzero_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "activity.db"
            database.write_bytes(b"")
            config = root / "config.json"
            config.write_text(
                '{"default_category": "Other", "categories": []}',
                encoding="utf-8",
            )
            output = root / "report.html"
            argv = [
                "report.py",
                "--database",
                str(database),
                "--config",
                str(config),
                "--output",
                str(output),
            ]
            stderr = io.StringIO()
            with (
                mock.patch("sys.argv", argv),
                mock.patch("report.generate_report", side_effect=sqlite3.DatabaseError("database is locked")),
                mock.patch("sys.stderr", stderr),
            ):
                with self.assertRaises(SystemExit) as raised:
                    report.main()

            self.assertEqual(raised.exception.code, 1)
            message = stderr.getvalue()
            self.assertIn("Error:", message)
            self.assertIn("database is locked", message)
            self.assertNotIn("Traceback", message)
            self.assertFalse(output.exists())
            self.assertEqual(database.read_bytes(), b"")

    def test_corrupt_database_exits_nonzero_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "activity.db"
            database.write_bytes(b"this is not a sqlite database")
            original = database.read_bytes()
            config = root / "config.json"
            config.write_text(
                '{"default_category": "Other", "categories": []}',
                encoding="utf-8",
            )
            output = root / "report.html"
            argv = [
                "report.py",
                "--database",
                str(database),
                "--config",
                str(config),
                "--output",
                str(output),
            ]
            stderr = io.StringIO()
            stdout = io.StringIO()
            with (
                mock.patch("sys.argv", argv),
                mock.patch("sys.stderr", stderr),
                mock.patch("sys.stdout", stdout),
            ):
                with self.assertRaises(SystemExit) as raised:
                    report.main()

            self.assertEqual(raised.exception.code, 1)
            message = stderr.getvalue()
            self.assertIn("Error:", message)
            self.assertNotIn("Traceback", message)
            self.assertNotIn("Report generated:", stdout.getvalue())
            self.assertFalse(output.exists())
            self.assertEqual(database.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
