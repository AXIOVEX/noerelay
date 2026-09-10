"""Tests for cross-platform system detection (src/noerelay/system_info.py).

These tests are host-agnostic: they exercise the pure/defensive logic (arch
normalization, OS-version parsing, summary rendering, GPU math) with patched
platform values, and assert that ``detect_system()`` never raises and always
returns a well-formed :class:`SystemInfo` regardless of the host OS.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

# Make the src/ layout importable without installing the package (CI parity).
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from noerelay import system_info  # noqa: E402
from noerelay.system_info import (  # noqa: E402
    GPU,
    SystemInfo,
    _arch_name,
    _os_version,
    detect_system,
)


class ArchNameTests(unittest.TestCase):
    def test_amd64_normalized(self):
        with mock.patch.object(system_info.platform, "machine", return_value="AMD64"):
            self.assertEqual(_arch_name(), "x86_64")

    def test_x86_64_passthrough(self):
        with mock.patch.object(system_info.platform, "machine", return_value="x86_64"):
            self.assertEqual(_arch_name(), "x86_64")

    def test_aarch64_normalized(self):
        with mock.patch.object(system_info.platform, "machine", return_value="aarch64"):
            self.assertEqual(_arch_name(), "arm64")

    def test_arm64_passthrough(self):
        with mock.patch.object(system_info.platform, "machine", return_value="arm64"):
            self.assertEqual(_arch_name(), "arm64")

    def test_unknown_machine(self):
        with mock.patch.object(system_info.platform, "machine", return_value="riscv64"):
            self.assertEqual(_arch_name(), "riscv64")

    def test_empty_machine(self):
        with mock.patch.object(system_info.platform, "machine", return_value=""):
            self.assertEqual(_arch_name(), "unknown")


class OsVersionTests(unittest.TestCase):
    def test_windows_11_build(self):
        with mock.patch.object(system_info.platform, "system", return_value="Windows"), \
             mock.patch.object(system_info.platform, "version", return_value="10.0.26200"):
            self.assertEqual(_os_version(), "11 (build 26200)")

    def test_windows_10_build(self):
        with mock.patch.object(system_info.platform, "system", return_value="Windows"), \
             mock.patch.object(system_info.platform, "version", return_value="10.0.19045"):
            self.assertEqual(_os_version(), "10 (build 19045)")

    def test_darwin_version(self):
        with mock.patch.object(system_info.platform, "system", return_value="Darwin"), \
             mock.patch.object(system_info.platform, "mac_ver", return_value=("14.5",)):
            self.assertEqual(_os_version(), "14.5")

    def test_linux_pretty_name(self):
        os_release = 'NAME="Ubuntu"\nVERSION_ID="24.04"\nPRETTY_NAME="Ubuntu 24.04.2 LTS"\n'
        with mock.patch.object(system_info.platform, "system", return_value="Linux"), \
             mock.patch.object(system_info.platform, "release", return_value="6.8.0"), \
             mock.patch("builtins.open", mock.mock_open(read_data=os_release)):
            self.assertEqual(_os_version(), "Ubuntu 24.04.2 LTS")

    def test_linux_falls_back_to_release(self):
        with mock.patch.object(system_info.platform, "system", return_value="Linux"), \
             mock.patch.object(system_info.platform, "release", return_value="6.8.0-generic"), \
             mock.patch("builtins.open", side_effect=OSError("no os-release")):
            self.assertEqual(_os_version(), "6.8.0-generic")

    def test_never_raises_on_garbage(self):
        with mock.patch.object(system_info.platform, "system", return_value="WeirdOS"), \
             mock.patch.object(system_info.platform, "release", return_value=""):
            # Must not raise; returns a string (possibly empty).
            result = _os_version()
            self.assertIsInstance(result, str)


class SummaryRenderingTests(unittest.TestCase):
    def test_cpu_label_single_core_count(self):
        s = SystemInfo(os="linux", os_version="24.04", arch="x86_64",
                       cpu_model="AMD Ryzen 9", cpu_count=16, physical_cores=16)
        self.assertIn("AMD Ryzen 9  (16 cores)", s.summary_lines()[1])

    def test_cpu_label_threads_vs_cores(self):
        s = SystemInfo(os="windows", os_version="11 (build 26200)", arch="x86_64",
                       cpu_model="Intel i9", cpu_count=32, physical_cores=24)
        self.assertIn("Intel i9  (32 threads / 24 cores)", s.summary_lines()[1])

    def test_cpu_label_unknown_model(self):
        s = SystemInfo(os="linux", arch="x86_64", cpu_model="", cpu_count=8)
        self.assertIn("unknown  (8 cores)", s.summary_lines()[1])

    def test_os_line_includes_version(self):
        s = SystemInfo(os="darwin", os_version="14.5", arch="arm64")
        self.assertEqual(s.summary_lines()[0], "OS:          darwin 14.5 (arm64)")

    def test_os_line_without_version(self):
        s = SystemInfo(os="linux", arch="x86_64")
        self.assertEqual(s.summary_lines()[0], "OS:          linux (x86_64)")

    def test_hostname_line_present_when_set(self):
        s = SystemInfo(os="linux", arch="x86_64", hostname="myhost")
        self.assertIn("Host:        myhost", s.summary_lines())

    def test_hostname_line_absent_when_empty(self):
        s = SystemInfo(os="linux", arch="x86_64")
        self.assertNotIn("Host:", s.summary_lines())

    def test_gpu_lines_rendered(self):
        gpus = [GPU(index=0, name="RTX 4090", total_mib=24576, display_active=True)]
        s = SystemInfo(os="linux", arch="x86_64", gpus=gpus)
        lines = s.summary_lines()
        self.assertIn("GPU 0:     RTX 4090  24.0 GB VRAM [display]", lines)

    def test_no_gpu_line(self):
        s = SystemInfo(os="linux", arch="x86_64")
        self.assertIn("GPU:         none detected (CPU-only)", s.summary_lines())


class GpuMathTests(unittest.TestCase):
    def test_total_gb(self):
        g = GPU(index=0, name="x", total_mib=16384)
        self.assertEqual(g.total_gb, 16.0)

    def test_free_gb(self):
        g = GPU(index=0, name="x", free_mib=8192)
        self.assertEqual(g.free_gb, 8.0)

    def test_total_vram_gb_sums(self):
        s = SystemInfo(gpus=[
            GPU(index=0, name="a", total_mib=12288),
            GPU(index=1, name="b", total_mib=16384),
        ])
        self.assertEqual(s.total_vram_gb, 28.0)
        self.assertEqual(s.gpu_count, 2)


class DetectSystemContractTests(unittest.TestCase):
    """detect_system() must never raise and must return a well-formed object."""

    def test_returns_system_info(self):
        s = detect_system()
        self.assertIsInstance(s, SystemInfo)

    def test_field_types(self):
        s = detect_system()
        self.assertIsInstance(s.os, str)
        self.assertIsInstance(s.os_version, str)
        self.assertIsInstance(s.arch, str)
        self.assertIsInstance(s.cpu_model, str)
        self.assertIsInstance(s.cpu_count, int)
        self.assertIsInstance(s.physical_cores, int)
        self.assertIsInstance(s.ram_gb, float)
        self.assertIsInstance(s.hostname, str)
        self.assertIsInstance(s.gpus, list)
        self.assertIsInstance(s.backend, str)
        self.assertIsInstance(s.python_version, str)
        self.assertIsInstance(s.apple_silicon, bool)

    def test_backend_is_known_value(self):
        s = detect_system()
        self.assertIn(s.backend, {"cuda", "metal", "cpu"})

    def test_cpu_count_nonnegative(self):
        s = detect_system()
        self.assertGreaterEqual(s.cpu_count, 0)

    def test_physical_cores_nonnegative(self):
        s = detect_system()
        self.assertGreaterEqual(s.physical_cores, 0)

    def test_ram_gb_nonnegative(self):
        s = detect_system()
        self.assertGreaterEqual(s.ram_gb, 0.0)

    def test_summary_lines_are_strings(self):
        s = detect_system()
        lines = s.summary_lines()
        self.assertTrue(lines)
        for line in lines:
            self.assertIsInstance(line, str)
            self.assertTrue(line.strip())


if __name__ == "__main__":
    unittest.main()
