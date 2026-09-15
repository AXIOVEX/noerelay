"""Tests for the `noerelay adopt` and `noerelay update` CLI commands.

These exercise the pure command-building logic and the file-scaffolding
behavior of the CLI without touching the network or the real filesystem
outside a temp dir. The CLI is imported from ``src/`` (the package is not
installed in CI), matching the sys.path pattern used by the other tests.
"""

from __future__ import annotations

import argparse
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import noerelay.cli as cli  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _adopt_args(**overrides) -> argparse.Namespace:
    base = {
        "dir": None,
        "name": None,
        "force": False,
        "onboard": False,
        "project": None,
        "description": None,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def _update_args(**overrides) -> argparse.Namespace:
    base = {
        "editable": False,
        "extras": "full",
        "dry_run": False,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def _run_adopt(target: Path, **overrides):
    """Run cmd_adopt against a temp target with the gateway mocked out."""
    args = _adopt_args(dir=str(target), **overrides)
    with mock.patch.object(cli, "load_config", return_value={}):
        cli.cmd_adopt(args)


# ---------------------------------------------------------------------------
# adopt
# ---------------------------------------------------------------------------


class AdoptScaffoldingTests(unittest.TestCase):
    def test_creates_specify_structure(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            _run_adopt(target, name="T")
            self.assertTrue((target / ".specify" / "memory" / "constitution.md").is_file())
            self.assertTrue((target / ".specify" / "features").is_dir())
            self.assertTrue((target / ".specify" / "templates" / "spec.md").is_file())
            self.assertTrue((target / ".specify" / "templates" / "plan.md").is_file())
            self.assertTrue((target / ".specify" / "templates" / "tasks.md").is_file())

    def test_creates_docs_and_noerelay(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            _run_adopt(target)
            self.assertTrue((target / "docs" / "STATE.md").is_file())
            self.assertTrue((target / ".noerelay" / "verification-matrix.md").is_file())
            self.assertTrue((target / ".noerelay" / "GAPS.md").is_file())

    def test_creates_aider_integration(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            _run_adopt(target)
            self.assertTrue((target / "scripts" / "aider.ps1").is_file())
            self.assertTrue((target / "scripts" / "aider.cmd").is_file())
            self.assertTrue((target / ".aider.conf.yml").is_file())
            self.assertTrue((target / ".aider.model.metadata.json").is_file())

    def test_creates_gitignore_when_missing(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            _run_adopt(target)
            self.assertTrue((target / ".gitignore").is_file())
            self.assertIn(".aider*", (target / ".gitignore").read_text("utf-8"))

    def test_appends_gitignore_when_present(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            (target / ".gitignore").write_text("# existing\n", "utf-8")
            _run_adopt(target)
            content = (target / ".gitignore").read_text("utf-8")
            self.assertIn("# existing", content)
            self.assertIn(".aider*", content)

    def test_idempotent_second_run_skips(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            _run_adopt(target)
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                _run_adopt(target)
            out = buf.getvalue()
            self.assertIn("Skipped", out)
            self.assertIn("constitution.md", out)

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            _run_adopt(target)
            const = target / ".specify" / "memory" / "constitution.md"
            const.write_text("CUSTOM", "utf-8")
            _run_adopt(target, force=True)
            self.assertNotEqual(const.read_text("utf-8"), "CUSTOM")

    def test_invalid_dir_exits(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "nope"
            with self.assertRaises(SystemExit):
                _run_adopt(missing)

    def test_onboard_posts_to_gateway(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            with mock.patch.object(cli, "api_request") as api:
                api.return_value = {"project_name": "T"}
                _run_adopt(target, name="T", onboard=True)
                api.assert_called_once()
                # api_request(config, method, path, body)
                _config, method, path, body = api.call_args[0]
                self.assertEqual(method, "POST")
                self.assertEqual(path, "/v1/noerelay/projects/onboard")
                self.assertEqual(body["project_name"], "T")

    def test_onboard_failure_is_nonfatal(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            with mock.patch.object(cli, "api_request", side_effect=RuntimeError("down")):
                # Should not raise; the command completes.
                _run_adopt(target, name="T", onboard=True)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class UpdateCommandBuildTests(unittest.TestCase):
    def test_standard_mode_commands(self):
        cmds = cli._build_update_commands(_update_args())
        labels = [label for label, _ in cmds]
        self.assertIn("pip install -U noerelay[full]", labels)
        self.assertIn("pip install -U (core deps)", labels)
        # Standard mode must NOT include a git pull.
        self.assertNotIn("git pull", labels)

    def test_editable_mode_includes_git_pull(self):
        cmds = cli._build_update_commands(_update_args(editable=True))
        labels = [label for label, _ in cmds]
        self.assertIn("git pull", labels)
        self.assertIn("pip install -e .[full]", labels)
        # git pull must come first.
        self.assertEqual(labels[0], "git pull")

    def test_extras_are_respected(self):
        cmds = cli._build_update_commands(_update_args(extras="ui"))
        flat = " ".join(" ".join(argv) for _, argv in cmds)
        self.assertIn("noerelay[ui]", flat)
        self.assertNotIn("noerelay[full]", flat)

    def test_core_deps_always_present(self):
        for editable in (False, True):
            cmds = cli._build_update_commands(_update_args(editable=editable))
            flat = " ".join(" ".join(argv) for _, argv in cmds)
            self.assertIn("pip", flat)
            self.assertIn("setuptools", flat)
            self.assertIn("wheel", flat)

    def test_argv_uses_pip_module(self):
        cmds = cli._build_update_commands(_update_args())
        # Every pip command should invoke `python -m pip`.
        for label, argv in cmds:
            if "pip" in label:
                self.assertIn("-m", argv)
                self.assertIn("pip", argv)


class UpdateExecutionTests(unittest.TestCase):
    def test_dry_run_does_not_run_subprocess(self):
        args = _update_args(dry_run=True)
        with mock.patch.object(cli.subprocess, "run") as run:
            cli.cmd_update(args)
            run.assert_not_called()

    def test_runs_commands_in_order(self):
        args = _update_args(editable=True)
        ok = types.SimpleNamespace(returncode=0)
        with mock.patch.object(cli.subprocess, "run", return_value=ok) as run:
            cli.cmd_update(args)
            # git pull, pip -e ., core deps => 3 calls
            self.assertEqual(run.call_count, 3)
            first_argv = run.call_args_list[0][0][0]
            self.assertEqual(first_argv[0], "git")

    def test_aborts_on_failure(self):
        args = _update_args(editable=True)
        fail = types.SimpleNamespace(returncode=1)
        with mock.patch.object(cli.subprocess, "run", return_value=fail):
            with self.assertRaises(SystemExit) as ctx:
                cli.cmd_update(args)
            self.assertEqual(ctx.exception.code, 1)

    def test_missing_binary_exits(self):
        args = _update_args(editable=True)
        with mock.patch.object(cli.subprocess, "run", side_effect=FileNotFoundError("no git")):
            with self.assertRaises(SystemExit) as ctx:
                cli.cmd_update(args)
            self.assertEqual(ctx.exception.code, 1)


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------


class ArgparseWiringTests(unittest.TestCase):
    def test_adopt_and_update_registered_in_package(self):
        src = (ROOT / "src" / "noerelay" / "cli.py").read_text("utf-8")
        # Subparsers are registered (multi-line add_parser calls).
        self.assertIn('"adopt",', src)
        self.assertIn('"update",', src)
        # Dispatch branches exist.
        self.assertIn('args.command == "adopt"', src)
        self.assertIn('args.command == "update"', src)

    def test_standalone_script_has_same_commands(self):
        import subprocess
        result = subprocess.run([sys.executable, str(ROOT / "scripts/noerelay.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("adopt", result.stdout)
        self.assertIn("update", result.stdout)



if __name__ == "__main__":
    unittest.main()
