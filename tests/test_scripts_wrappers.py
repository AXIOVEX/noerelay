"""Tests for the generated installer scripts (NR-LLM-004, T-LLM-004).

The installer must emit only thin ``.bat``/``.sh`` wrappers that resolve the
venv interpreter and invoke the Python lifecycle entry points.  **No**
PowerShell (``.ps1``) scripts may be generated.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "reference"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from noerelay.provision import ProvisionPlan  # noqa: E402
from noerelay.scripts import generate_scripts, venv_python_path  # noqa: E402
from noerelay.system_info import SystemInfo  # noqa: E402


def _plan(os_name: str, install_dir: Path) -> ProvisionPlan:
    return ProvisionPlan(system=SystemInfo(os=os_name), os=os_name,
                         install_dir=install_dir)


class WindowsWrapperTests(unittest.TestCase):
    def test_no_powershell_emitted(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("windows", Path(td) / "install")
            generate_scripts(plan)
            names = [p.name for p in plan.bin_dir.iterdir()]
            self.assertFalse(any(n.endswith(".ps1") for n in names), names)

    def test_expected_bat_files(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("windows", Path(td) / "install")
            generate_scripts(plan)
            names = {p.name for p in plan.bin_dir.iterdir()}
            for expected in ("activate.bat", "start-server.bat",
                             "stop-server.bat", "autostart.bat", "noerelay.bat"):
                self.assertIn(expected, names)

    def test_start_wrapper_invokes_python_llm_start(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("windows", Path(td) / "install")
            generate_scripts(plan)
            content = (plan.bin_dir / "start-server.bat").read_text(encoding="utf-8")
            self.assertIn(str(venv_python_path(plan)), content)
            self.assertIn("-m noerelay.cli llm start", content)
            self.assertIn(f'--dir "{plan.install_dir}"', content)

    def test_stop_wrapper(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("windows", Path(td) / "install")
            generate_scripts(plan)
            content = (plan.bin_dir / "stop-server.bat").read_text(encoding="utf-8")
            self.assertIn("-m noerelay.cli llm stop", content)

    def test_autostart_wrapper_uses_schedule(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("windows", Path(td) / "install")
            generate_scripts(plan)
            content = (plan.bin_dir / "autostart.bat").read_text(encoding="utf-8")
            self.assertIn("-m noerelay.cli llm schedule", content)


class UnixWrapperTests(unittest.TestCase):
    def test_no_powershell_emitted(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("linux", Path(td) / "install")
            generate_scripts(plan)
            names = [p.name for p in plan.bin_dir.iterdir()]
            self.assertFalse(any(n.endswith(".ps1") for n in names), names)

    def test_expected_sh_files(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("linux", Path(td) / "install")
            generate_scripts(plan)
            names = {p.name for p in plan.bin_dir.iterdir()}
            for expected in ("activate.sh", "start-server.sh",
                             "stop-server.sh", "noerelay"):
                self.assertIn(expected, names)
            self.assertNotIn("autostart.sh", names)  # darwin only

    def test_darwin_emits_autostart(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("darwin", Path(td) / "install")
            generate_scripts(plan)
            self.assertIn("autostart.sh", {p.name for p in plan.bin_dir.iterdir()})

    def test_start_wrapper_execs_python(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan("linux", Path(td) / "install")
            generate_scripts(plan)
            content = (plan.bin_dir / "start-server.sh").read_text(encoding="utf-8")
            self.assertIn(str(venv_python_path(plan)), content)
            self.assertIn("noerelay.cli llm start", content)


if __name__ == "__main__":
    unittest.main()
