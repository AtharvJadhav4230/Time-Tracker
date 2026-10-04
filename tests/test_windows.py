from __future__ import annotations

import unittest
import builtins
import sys
from unittest import mock


from timetracker.windows import WindowsActivityProvider

class FakeApi:
    def __init__(self, last_input: int, tick: int) -> None:
        self.last_input = last_input
        self.tick = tick

    def GetLastInputInfo(self) -> int:
        return self.last_input

    def GetTickCount(self) -> int:
        return self.tick


class FakeGui:
    def __init__(self, hwnd: int, title: str) -> None:
        self.hwnd = hwnd
        self.title = title

    def GetForegroundWindow(self) -> int:
        return self.hwnd

    def GetWindowText(self, _hwnd: int) -> str:
        return self.title


class FakeProcessApi:
    def __init__(self, process_id: int = 42, error: Exception | None = None) -> None:
        self.process_id = process_id
        self.error = error

    def GetWindowThreadProcessId(self, _hwnd: int) -> tuple[int, int]:
        if self.error is not None:
            raise self.error
        return (7, self.process_id)


class FakePsutil:
    class Error(Exception):
        pass

    def __init__(self, name: str = "Code.exe", error: Exception | None = None) -> None:
        self._name = name
        self._error = error

    def Process(self, _process_id: int) -> "FakePsutil":
        return self

    def name(self) -> str:
        if self._error is not None:
            raise self._error
        return self._name


def provider(
    *,
    last_input: int = 1_000,
    tick: int = 5_000,
    hwnd: int = 10,
    title: str = "Fictional document",
    process_error: Exception | None = None,
    process_name: str = "Code.exe",
    name_error: Exception | None = None,
) -> WindowsActivityProvider:
    fake = WindowsActivityProvider.__new__(WindowsActivityProvider)
    fake.win32api = FakeApi(last_input, tick)
    fake.win32gui = FakeGui(hwnd, title)
    fake.win32process = FakeProcessApi(error=process_error)
    fake.psutil = FakePsutil(process_name, name_error)
    return fake


class WindowsProviderTests(unittest.TestCase):
    def test_idle_seconds_and_tick_wraparound(self) -> None:
        self.assertEqual(provider().sample().idle_seconds, 4)
        wrapped = provider(last_input=0xFFFFFFF0, tick=1000)
        self.assertAlmostEqual(wrapped._idle_seconds(), 1.016)

    def test_foreground_fallbacks_use_synthetic_values(self) -> None:
        missing = provider(hwnd=0)
        self.assertEqual(missing._foreground_window(), ("System", "No active window"))

        untitled = provider(title="   ")
        self.assertEqual(untitled._foreground_window()[1], "(Untitled)")

        named = provider(process_name="FictionalApp.exe", title="Fictional document")
        self.assertEqual(named._foreground_window(), ("FictionalApp.exe", "Fictional document"))

        psutil_error = provider(name_error=FakePsutil.Error("lookup failed"))
        self.assertEqual(psutil_error._foreground_window()[0], "Unknown process")

        os_error = provider(process_error=OSError("access denied"))
        self.assertEqual(os_error._foreground_window()[0], "Unknown process")

    def test_sample_combines_foreground_state_and_idle_duration(self) -> None:
        snapshot = provider(process_name="notes.exe", title="Fictional note").sample()
        self.assertEqual(snapshot.state.application, "notes.exe")
        self.assertEqual(snapshot.state.window_title, "Fictional note")
        self.assertFalse(snapshot.state.is_idle)
        self.assertEqual(snapshot.idle_seconds, 4)



WINDOWS_DEPENDENCIES = ("psutil", "win32api", "win32gui", "win32process")


def selective_import(failing=None, error=None, attempted=None):
    """Return an __import__ replacement that delegates to the real import.

    Records imports of the Windows dependencies in `attempted` and raises
    `error` when `failing` is imported. All other imports behave normally.
    """
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        top_level = name.split(".")[0]
        if level == 0 and top_level in WINDOWS_DEPENDENCIES:
            if attempted is not None:
                attempted.append(top_level)
            if top_level == failing:
                raise error
        return real_import(name, globals, locals, fromlist, level)

    return fake_import


class WindowsProviderStartupTests(unittest.TestCase):
    def test_unsupported_platform_fails_before_dependency_imports(self):
        attempted = []
        with mock.patch.object(sys, "platform", "linux"), mock.patch(
            "builtins.__import__", new=selective_import(attempted=attempted)
        ):
            with self.assertRaises(RuntimeError) as ctx:
                WindowsActivityProvider()

        self.assertEqual(
            str(ctx.exception), "Activity tracking is available on Windows only."
        )
        self.assertEqual(attempted, [])

    def test_missing_dependency_reports_install_guidance_and_chains_cause(self):
        original = ImportError("No module named 'win32gui'", name="win32gui")
        harmless = {
            name: mock.MagicMock()
            for name in ("psutil", "win32api", "win32process")
        }
        with mock.patch.object(sys, "platform", "win32"), mock.patch.dict(
            sys.modules, harmless
        ), mock.patch(
            "builtins.__import__",
            new=selective_import(failing="win32gui", error=original),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                WindowsActivityProvider()

        message = str(ctx.exception)
        self.assertIn("Windows dependencies are missing", message)
        self.assertIn("pip install -r requirements.txt", message)
        self.assertIs(ctx.exception.__cause__, original)

if __name__ == "__main__":
    unittest.main()        