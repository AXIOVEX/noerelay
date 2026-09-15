"""Tests for the Python-native server lifecycle (NR-LLM-004, T-LLM-004).

Start/stop/schedule are implemented in Python.  Windows scheduling uses the
native ``schtasks`` executable (no PowerShell).  Subprocess and network calls
are mocked so no real processes, tasks, or connections are created.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "reference"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import noerelay.lifecycle as lifecycle  # noqa: E402


def _ok():
    return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")


def _make_wrapper(install: Path) -> Path:
    wrapper = install / "bin" / "start-server.bat"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text("@echo off\n", encoding="utf-8")
    return wrapper


@mock.patch.object(lifecycle, "IS_WINDOWS", True)
class ScheduleWindowsTests(unittest.TestCase):
    def test_schtasks_argv(self):
        with tempfile.TemporaryDirectory() as td:
            install = Path(td)
            wrapper = _make_wrapper(install)
            with mock.patch.object(lifecycle.subprocess, "run", return_value=_ok()) as run:
                out = lifecycle._schedule_windows(install, "NoeRelay Test Task")
            argv = run.call_args[0][0]
            self.assertEqual(argv[0], "schtasks")
            for flag in ("/Create", "/F", "/TN", "/TR", "/SC", "/RL", "/IT"):
                self.assertIn(flag, argv)
            self.assertEqual(argv[argv.index("/TN") + 1], "NoeRelay Test Task")
            self.assertEqual(argv[argv.index("/TR") + 1], f'"{wrapper}"')
            self.assertEqual(argv[argv.index("/SC") + 1], "ONLOGON")
            self.assertEqual(argv[argv.index("/RL") + 1], "LIMITED")
            self.assertTrue(out["scheduled"])
            self.assertEqual(out["platform"], "windows")

    def test_missing_wrapper_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(lifecycle.LifecycleError):
                lifecycle._schedule_windows(Path(td), "Task")

    def test_schtasks_failure_raises(self):
        with tempfile.TemporaryDirectory() as td:
            install = Path(td)
            _make_wrapper(install)
            fail = subprocess.CompletedProcess(args=[], returncode=1,
                                              stdout="", stderr="denied")
            with mock.patch.object(lifecycle.subprocess, "run", return_value=fail):
                with self.assertRaises(lifecycle.LifecycleError):
                    lifecycle._schedule_windows(install, "Task")


class UnscheduleWindowsTests(unittest.TestCase):
    def test_unschedule_argv(self):
        with mock.patch.object(lifecycle, "IS_WINDOWS", True), \
                tempfile.TemporaryDirectory() as td:
            with mock.patch.object(lifecycle.subprocess, "run", return_value=_ok()) as run:
                out = lifecycle.unschedule_task(install_dir_arg=td, task_name="T")
            argv = run.call_args[0][0]
            self.assertEqual(argv[0], "schtasks")
            for flag in ("/Delete", "/F", "/TN"):
                self.assertIn(flag, argv)
            self.assertEqual(argv[argv.index("/TN") + 1], "T")
            self.assertTrue(out["unscheduled"])


class PidAndPathTests(unittest.TestCase):
    def test_read_pid_missing(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(lifecycle.read_pid(Path(td)))

    def test_read_pid_parses(self):
        with tempfile.TemporaryDirectory() as td:
            install = Path(td)
            lifecycle.pid_file(install).write_text("1234", encoding="utf-8")
            self.assertEqual(lifecycle.read_pid(install), 1234)

    def test_read_pid_bad_value(self):
        with tempfile.TemporaryDirectory() as td:
            install = Path(td)
            lifecycle.pid_file(install).write_text("not-a-pid", encoding="utf-8")
            self.assertIsNone(lifecycle.read_pid(install))

    def test_install_dir_from_explicit(self):
        self.assertEqual(lifecycle.install_dir_from("/tmp/foo"),
                         Path("/tmp/foo").expanduser().resolve())

    def test_server_status_no_pid(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(lifecycle.urllib.request, "urlopen",
                                   side_effect=OSError("refused")):
                st = lifecycle.server_status(install_dir_arg=td)
            self.assertIsNone(st["pid"])
            self.assertFalse(st["process_alive"])
            self.assertFalse(st["api_reachable"])


if __name__ == "__main__":
    unittest.main()
