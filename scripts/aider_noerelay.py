"""
Aider wrapper that injects /noerelay-* slash commands.

Usage:
    python scripts/aider_noerelay.py [aider args...]

This monkey-patches aider's Commands class to add noerelay subcommands
that shell out to the noerelay.py CLI. The noerelay script path is
resolved from the NOERELAY_SCRIPT env var or defaults to the known
ElectroHire location.
"""

import os
import subprocess
import sys

# --- Resolve noerelay.py path ---
NOERELAY_SCRIPT = os.environ.get(
    "NOERELAY_SCRIPT",
    r"C:\\Users\\trist\\Development\\ElectroHire\\noerelay\\scripts\\noerelay.py",
)

# --- Noerelay subcommands to expose ---
NOERELAY_COMMANDS = {
    "status": ("status", "Check NoeRelay gateway health"),
    "models": ("models", "List available models"),
    "costs": ("costs", "Show cost report"),
    "audit": ("audit", "Check project state"),
    "onboard": ("onboard", "Initialize a new project"),
    "chat": ("chat", "One-shot chat completion"),
    "receipt": ("receipt", "Get run receipt by ID"),
    "run": ("run", "Launch a tool (codex, aider, cursor, opencode)"),
    "install": ("install", "Install a tool (codex, aider, opencode, cursor)"),
    "config": ("config", "Show or set configuration"),
    "setup": ("setup", "Scaffold noerelay integration in a project"),
}


def _make_cmd_method(subcommand: str, description: str):
    """Create a cmd_noerelay_* method that shells out to noerelay.py."""

    def cmd_method(self, args: str = ""):
        cmd_parts = [sys.executable, NOERELAY_SCRIPT, subcommand]
        if args:
            cmd_parts.extend(args.split())

        self.io.tool_output(f"Running: {' '.join(cmd_parts)}")
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.stdout:
                self.io.tool_output(result.stdout.rstrip())
            if result.stderr:
                self.io.tool_error(result.stderr.rstrip())
            if result.returncode != 0:
                self.io.tool_error(f"Exit code: {result.returncode}")
        except subprocess.TimeoutExpired:
            self.io.tool_error("Command timed out (120s)")
        except FileNotFoundError:
            self.io.tool_error(f"noerelay.py not found at: {NOERELAY_SCRIPT}")

    cmd_method.__doc__ = description
    return cmd_method


def patch_commands():
    """Monkey-patch aider's Commands class with noerelay commands."""
    from aider.commands import Commands

    for suffix, (subcommand, description) in NOERELAY_COMMANDS.items():
        method_name = f"cmd_noerelay_{suffix}"
        setattr(Commands, method_name, _make_cmd_method(subcommand, description))

    def completions_noerelay_run(self):
        return ["codex", "aider", "cursor", "opencode"]

    def completions_noerelay_install(self):
        return ["codex", "aider", "opencode", "cursor", "cursor-ide"]

    def completions_noerelay_config(self):
        return ["show", "set"]

    def completions_noerelay_setup(self):
        return ["--help"]

    setattr(Commands, "completions_noerelay_run", completions_noerelay_run)
    setattr(Commands, "completions_noerelay_install", completions_noerelay_install)
    setattr(Commands, "completions_noerelay_config", completions_noerelay_config)
    setattr(Commands, "completions_noerelay_setup", completions_noerelay_setup)


def main():
    patch_commands()
    from aider.main import main as aider_main
    status = aider_main()
    sys.exit(status)


if __name__ == "__main__":
    main()
