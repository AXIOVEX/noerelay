"""Tests for the `noerelay llm` / `noerelay hf` / `models --local` CLI verbs.

Covers the operator-facing surface added in Phase 2 (NR-LLM-004 / NR-LLM-006):

* ``models --local`` renders the offline supported-model catalog.
* ``llm <action> --dir <path>`` parses exactly the argument form the
  installer-emitted wrappers invoke (``python -m noerelay.cli llm start --dir ...``).
* ``hf complete`` works fully offline.
* The standalone ``scripts/noerelay.py`` exposes the same verbs.
"""

import argparse
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from noerelay import cli  # noqa: E402


class _StopParsing(Exception):
    """Sentinel raised to abort main() immediately after argument parsing."""


def _parse(argv):
    """Parse *argv* with the package CLI parser without executing the command.

    ``main()`` is invoked with ``sys.argv`` patched; the real ``parse_args``
    is wrapped so that, once the namespace is captured, a bare sentinel
    aborts dispatch (the namespace is carried via closure, never through the
    exception machinery).
    """
    captured = {}
    orig_parse = argparse.ArgumentParser.parse_args

    def fake_parse(self, args=None, namespace=None):
        captured["ns"] = orig_parse(self, args, namespace)
        raise _StopParsing()

    with mock.patch.object(argparse.ArgumentParser, "parse_args", fake_parse), \
            mock.patch.object(sys, "argv", ["noerelay"] + argv):
        try:
            cli.main()
        except _StopParsing:
            pass
    if "ns" not in captured:
        raise AssertionError("main() returned without parsing")
    return captured["ns"]


class ModelsLocalTests(unittest.TestCase):
    def test_models_local_parser_flags(self):
        args = _parse(["models", "--local", "--json"])
        self.assertEqual(args.command, "models")
        self.assertTrue(args.local)
        self.assertTrue(args.json)

    def test_models_local_renders_catalog_offline(self):
        args = _parse(["models", "--local"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.cmd_models(args)
        out = buf.getvalue()
        self.assertIn("Supported local models", out)
        self.assertIn("gpt-oss-20b", out)
        self.assertIn("qwen3.8-27b", out)
        self.assertIn("fast", out)
        self.assertIn("hard", out)

    def test_models_local_json_is_machine_readable(self):
        args = _parse(["models", "--local", "--json"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.cmd_models(args)
        rows = json.loads(buf.getvalue())
        self.assertIsInstance(rows, list)
        keys = {r["key"] for r in rows}
        self.assertIn("gpt-oss-20b", keys)
        self.assertIn("qwen3.8-27b", keys)
        for r in rows:
            self.assertIn("tier", r)
            self.assertIn("quant", r)
            self.assertIn("size_gb", r)
            self.assertIn("min_vram_gb", r)


class LlmVerbTests(unittest.TestCase):
    def test_wrapper_form_start_parses(self):
        # Exact form emitted by scripts.py wrappers (NR-LLM-004).
        args = _parse(["llm", "start", "--dir", "C:\\noerelay-llm"])
        self.assertEqual(args.command, "llm")
        self.assertEqual(args.llm_action, "start")
        self.assertEqual(args.dir, "C:\\noerelay-llm")

    def test_stop_status_schedule_unschedule_parse(self):
        a = _parse(["llm", "stop", "--dir", "/tmp/nr"])
        self.assertEqual(a.llm_action, "stop")
        self.assertEqual(a.dir, "/tmp/nr")

        b = _parse(["llm", "status"])
        self.assertEqual(b.llm_action, "status")
        self.assertIsNone(b.dir)

        c = _parse(["llm", "schedule", "--dir", "/tmp/nr", "--task-name", "T1"])
        self.assertEqual(c.llm_action, "schedule")
        self.assertEqual(c.task_name, "T1")

        d = _parse(["llm", "unschedule", "--task-name", "T2"])
        self.assertEqual(d.llm_action, "unschedule")
        self.assertEqual(d.task_name, "T2")

    def test_start_wait_and_timeout(self):
        args = _parse(["llm", "start", "--dir", "/tmp/nr", "--wait", "--timeout", "30"])
        self.assertTrue(args.wait)
        self.assertEqual(args.timeout, 30)

    def test_status_dispatch_reports(self):
        args = _parse(["llm", "status", "--dir", "/tmp/does-not-exist"])
        with mock.patch("noerelay.lifecycle.server_status", return_value={
            "install_dir": "/tmp/does-not-exist",
            "pid": None,
            "process_alive": False,
            "base_url": "http://127.0.0.1:8080",
            "api_reachable": False,
        }) as ss:
            buf = io.StringIO()
            with redirect_stdout(buf):
                cli.cmd_llm(args)
            ss.assert_called_once_with("/tmp/does-not-exist")
        out = buf.getvalue()
        self.assertIn("process_alive", out)
        self.assertIn("api_reachable", out)

    def test_stop_dispatch(self):
        args = _parse(["llm", "stop", "--dir", "/tmp/nr"])
        with mock.patch("noerelay.lifecycle.stop_server",
                        return_value={"stopped": True, "pid": 42}) as st:
            buf = io.StringIO()
            with redirect_stdout(buf):
                cli.cmd_llm(args)
            st.assert_called_once_with("/tmp/nr")
        self.assertIn("42", buf.getvalue())


class HfVerbTests(unittest.TestCase):
    def test_complete_offline(self):
        args = _parse(["hf", "complete", "gpt-oss"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.cmd_hf(args)
        self.assertIn("gpt-oss-20b", buf.getvalue())

    def test_quant_completion_offline(self):
        args = _parse(["hf", "complete", "Q4_"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.cmd_hf(args)
        self.assertIn("Q4_K_M", buf.getvalue())

    def test_search_dispatch(self):
        args = _parse(["hf", "search", "qwen", "--limit", "3"])
        with mock.patch("noerelay.hf.search_hf",
                        return_value=[{"repo_id": "x/y", "downloads": 1, "gguf": True}]) as sh:
            buf = io.StringIO()
            with redirect_stdout(buf):
                cli.cmd_hf(args)
            sh.assert_called_once_with("qwen", limit=3, gguf_only=True)
        self.assertIn("x/y", buf.getvalue())

    def test_download_dispatch(self):
        args = _parse(["hf", "download", "unsloth/gpt-oss-20b-GGUF",
                       "--quant", "Q4_K_M", "--dest", "/tmp/models"])
        with mock.patch("noerelay.hf.download_gguf",
                        return_value=Path("/tmp/models/gpt-oss-20b-Q4_K_M.gguf")) as dg:
            buf = io.StringIO()
            with redirect_stdout(buf):
                cli.cmd_hf(args)
            self.assertEqual(dg.call_args.args[0], "unsloth/gpt-oss-20b-GGUF")
            self.assertEqual(dg.call_args.args[2], Path("/tmp/models"))
        self.assertIn("downloaded", buf.getvalue())


class StandaloneMirrorTests(unittest.TestCase):
    def test_standalone_script_has_llm_hf_and_models_local(self):
        import subprocess
        for args in (["llm", "--help"], ["hf", "--help"], ["models", "--local", "--json"]):
            result = subprocess.run([sys.executable, str(ROOT / "scripts/noerelay.py"), *args],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout)

    def test_package_registers_llm_hf(self):
        src = (ROOT / "src" / "noerelay" / "cli.py").read_text("utf-8")
        self.assertIn('"llm",', src)
        self.assertIn('"hf",', src)
        self.assertIn('args.command == "llm"', src)
        self.assertIn('args.command == "hf"', src)
        self.assertIn("def cmd_llm", src)
        self.assertIn("def cmd_hf", src)


if __name__ == "__main__":
    unittest.main()
