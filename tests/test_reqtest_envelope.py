"""Tests for noerelay.reqtest evidence-envelope writing (write_envelope / record_evidence)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from noerelay import reqtest


def _make_root(tmp: str) -> Path:
    root = Path(tmp)
    (root / "spec").mkdir(parents=True)
    (root / "spec" / "coverage-manifest.json").write_text("{}", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "requirements.md").write_text("", encoding="utf-8")
    return root


class WriteEnvelopeTests(unittest.TestCase):
    def test_writes_envelope_with_required_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            path = reqtest.write_envelope(
                root,
                work_package_id="LLM-01",
                test_id="T-LLM-003",
                command="python scripts/benchmark_local_models.py",
                requirement_ids=["NR-LLM-003"],
                status="observed_pass",
                result_artifact_sha256="a" * 64,
                logs_artifact_sha256="b" * 64,
                started_at="2026-09-11T00:00:00.000Z",
                finished_at="2026-09-11T00:05:00.000Z",
                artifact_digests={"T-LLM-003-benchmark.json": "c" * 64},
                notes="benchmark",
            )
            self.assertEqual(path, root / "evidence" / "LLM-01" / "T-LLM-003.json")
            env = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(env["evidence_version"], "1.0.0")
            self.assertEqual(env["work_package_id"], "LLM-01")
            self.assertEqual(env["requirement_ids"], ["NR-LLM-003"])
            self.assertEqual(env["test_ids"], ["T-LLM-003"])
            self.assertEqual(env["status"], "observed_pass")
            self.assertEqual(env["result_artifact_sha256"], "a" * 64)
            self.assertEqual(env["logs_artifact_sha256"], "b" * 64)
            self.assertEqual(env["artifact_digests"], {"T-LLM-003-benchmark.json": "c" * 64})
            self.assertEqual(env["notes"], "benchmark")
            self.assertEqual(env["exceptions"], [])
            self.assertNotIn("independent_verifier_identity", env)
            self.assertTrue(reqtest.is_release_ready(env))

    def test_verifier_included_when_given(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            path = reqtest.write_envelope(
                root,
                work_package_id="LLM-01",
                test_id="T-LLM-003",
                command="true",
                requirement_ids=["NR-LLM-003"],
                status="observed_pass",
                result_artifact_sha256="a" * 64,
                logs_artifact_sha256="b" * 64,
                started_at="2026-09-11T00:00:00.000Z",
                finished_at="2026-09-11T00:05:00.000Z",
                verifier="ROLE-AUDITOR",
            )
            env = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(env["independent_verifier_identity"], "ROLE-AUDITOR")

    def test_invalid_test_id_raises(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            with self.assertRaises(ValueError):
                reqtest.write_envelope(
                    root, "LLM-01", "BAD-ID", "true", ["NR-LLM-003"],
                    status="observed_pass",
                    result_artifact_sha256="a" * 64, logs_artifact_sha256="b" * 64,
                    started_at="2026-09-11T00:00:00.000Z",
                    finished_at="2026-09-11T00:05:00.000Z",
                )

    def test_invalid_status_raises(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            with self.assertRaises(ValueError):
                reqtest.write_envelope(
                    root, "LLM-01", "T-LLM-003", "true", ["NR-LLM-003"],
                    status="not_a_status",
                    result_artifact_sha256="a" * 64, logs_artifact_sha256="b" * 64,
                    started_at="2026-09-11T00:00:00.000Z",
                    finished_at="2026-09-11T00:05:00.000Z",
                )

    def test_observed_fail_envelope_not_release_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            path = reqtest.write_envelope(
                root, "LLM-01", "T-LLM-003", "true", ["NR-LLM-003"],
                status="observed_fail",
                result_artifact_sha256="a" * 64, logs_artifact_sha256="b" * 64,
                started_at="2026-09-11T00:00:00.000Z",
                finished_at="2026-09-11T00:05:00.000Z",
                exceptions=["command exited with code 1"],
            )
            env = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(reqtest.is_release_ready(env))
            self.assertEqual(env["exceptions"], ["command exited with code 1"])


class RecordEvidenceRefactorTests(unittest.TestCase):
    def test_record_evidence_produces_observed_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            fake = mock.Mock(returncode=0, stdout="ok\n", stderr="")
            with mock.patch.object(reqtest.subprocess, "run", return_value=fake) as run:
                with mock.patch.object(reqtest, "_git_revision", return_value="abc1234def"):
                    path = reqtest.record_evidence(
                        root, "LLM-01", "T-LLM-001", "echo ok", ["NR-LLM-001"]
                    )
            run.assert_called_once()
            env = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(env["status"], "observed_pass")
            self.assertEqual(env["source_revision"], "abc1234def")
            self.assertEqual(env["result_artifact_sha256"], env["logs_artifact_sha256"])
            self.assertEqual(env["artifact_digests"], {})
            self.assertTrue(reqtest.is_release_ready(env))

    def test_record_evidence_failure_records_observed_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            fake = mock.Mock(returncode=2, stdout="", stderr="boom\n")
            with mock.patch.object(reqtest.subprocess, "run", return_value=fake):
                with mock.patch.object(reqtest, "_git_revision", return_value="abc1234def"):
                    path = reqtest.record_evidence(
                        root, "LLM-01", "T-LLM-001", "false", ["NR-LLM-001"]
                    )
            env = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(env["status"], "observed_fail")
            self.assertEqual(env["exceptions"], ["command exited with code 2"])
            self.assertFalse(reqtest.is_release_ready(env))


if __name__ == "__main__":
    unittest.main()
