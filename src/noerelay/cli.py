"""
NoeRelay CLI — manage the NoeRelay gateway from the command line.

Usage:
    python scripts/noerelay.py <command> [options]

Commands:
    status              Check gateway health
    models              List available models
    costs               Show cost report
    audit               Check project state
    onboard             Initialize a new project
    chat                One-shot chat completion
    receipt             Get run receipt by ID
    run codex           Launch Codex CLI (installs if missing)
    run aider           Launch Aider (installs if missing)
    run cursor          Print Cursor setup instructions
    run opencode        Launch OpenCode (installs if missing)
    install codex       Install Codex CLI (npm)
    install aider       Install Aider (pip)
    install opencode    Install OpenCode (npm)
    install cursor      Install Cursor CLI (npm)
    install cursor-ide  Install Cursor IDE (winget)
    setup               Scaffold noerelay aider integration in a project
    adopt               Adopt an existing project into the spec-kit + noerelay workflow
    update              Update noerelay and its dependencies
    resume              Assess project state for resuming work
    config show         Show current configuration
    config set          Set configuration values

    Local LLM stack (cross-platform):
    detect              Detect this machine (OS, CPU, RAM, GPUs, backend)
    provision           Auto-provision the local LLM stack (llama.cpp + venv + model)
    doctor              Diagnose the local LLM stack (server reachability, API, chat)
    models --local      List the supported local model catalog (offline)
    llm start           Start the local llama-server (from llama.yaml, detached)
    llm stop            Stop the local llama-server
    llm status          Show local server process + API status
    llm schedule        Register a logon scheduled task (native, no PowerShell)
    llm unschedule      Remove the logon scheduled task
    hf search QUERY     Search Hugging Face for GGUF model repos
    hf download REPO    Download a GGUF (progress + resume)
    hf complete TOKEN   Offline completions for model/quant tokens (tab-completion hook)

    Coverage contract (append-only; mirrors xtask evidence):
    req list            List requirements with coverage status
    req show ID         Show one requirement with evidence
    req tests           List release tests with evidence status
    req add ID          Append a new requirement to the contract
    req test ID T       Append a release test to a requirement
    req coverage        Coverage report (mirrors xtask evidence coverage)
    req gate Gx         Check a gate (mirrors xtask evidence gate)
    req record          Run a command and record an evidence envelope
    req regenerate      Regenerate .specify/features/ from the manifest
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import subprocess
import shutil

# --- Configuration ---

DEFAULT_CONFIG = {
    "base_url": "http://localhost:8080",
    "api_key": "noerelay-local-development-key-0001",
    "model": "axiovex-agni",
    "model_raw": "axiovex-agni-raw",
    "project_id": "default",
}

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".noerelay", "config.json")


def load_config() -> dict:
    """Load config from file, merge with defaults."""
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config.update(json.load(f))
    # Env overrides
    if os.environ.get("NOERELAY_BASE_URL"):
        config["base_url"] = os.environ["NOERELAY_BASE_URL"]
    if os.environ.get("NOERELAY_API_KEY"):
        config["api_key"] = os.environ["NOERELAY_API_KEY"]
    return config


def save_config(config: dict):
    """Save config to file."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def _validate_url(url: str) -> str:
    """Validate that a URL is safe (no CRLF injection, valid scheme)."""
    import re
    if not re.match(r"^https?://[a-zA-Z0-9.\-]+(:\d+)?(/.*)?$", url):
        raise ValueError(f"Invalid URL: {url!r}")
    return url


def api_request(config: dict, method: str, path: str, body: dict = None) -> dict:
    """Make an API request to the NoeRelay gateway."""
    url = _validate_url(f"{config['base_url']}{path}")
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5100 if path == '/v1/noerelay/agent' else 600) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        print(f"Is the gateway running at {config['base_url']}?", file=sys.stderr)
        sys.exit(1)


# --- Commands ---

def cmd_status(args):
    """Check gateway health."""
    config = load_config()
    # Health (unauthenticated)
    try:
        req = urllib.request.Request(f"{config['base_url']}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            health = json.loads(resp.read().decode())
        print(f"Gateway: {config['base_url']}")
        print(f"Status:  {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"Gateway: {config['base_url']}")
        print(f"Status:  UNREACHABLE ({e})")
        sys.exit(1)

    # Ready (unauthenticated)
    try:
        req = urllib.request.Request(f"{config['base_url']}/ready")
        with urllib.request.urlopen(req, timeout=5) as resp:
            ready = json.loads(resp.read().decode())
        print(f"Authority: {ready.get('authority', '?')}")
        print(f"Model plane: {ready.get('model_plane', '?')}")
    except Exception:
        pass


def cmd_models(args):
    """List available models (gateway by default; offline local catalog with --local)."""
    if getattr(args, "local", False):
        _print_local_models(as_json=getattr(args, "json", False))
        return
    config = load_config()
    result = api_request(config, "GET", "/v1/models")
    print("Available models:")
    for m in result.get("data", []):
        marker = " *" if m["id"] == config.get("model") else ""
        print(f"  {m['id']}{marker}  (owned by {m.get('owned_by', '?')})")
    print(f"\n* = default model")


def cmd_costs(args):
    """Show cost report."""
    config = load_config()
    result = api_request(config, "GET", "/v1/noerelay/reports/costs")
    print("Cost Report:")
    print(json.dumps(result, indent=2))


def cmd_audit(args):
    """Check project state."""
    config = load_config()
    project_id = args.project or config.get("project_id", "default")
    result = api_request(config, "POST", "/v1/noerelay/projects/audit", {"project_id": project_id})
    print(f"Project: {result.get('project_id', project_id)}")
    print(f"Status:  {result.get('status', 'unknown')}")
    if result.get("status") == "in_progress":
        print(f"Runs:    {result.get('last_run_count', 0)}")
        print(f"Last:    {result.get('last_activity', 'unknown')}")
        print(f"Phase:   {result.get('current_phase', 'unknown')}")
    print(f"\nNext:    {result.get('next_action', 'n/a')}")
    print(f"Message: {result.get('message', '')}")


def cmd_onboard(args):
    """Initialize a new project."""
    config = load_config()
    project_id = args.project or config.get("project_id", "default")
    body = {
        "project_id": project_id,
        "project_name": args.name or project_id,
        "description": args.description or "",
    }
    result = api_request(config, "POST", "/v1/noerelay/projects/onboard", body)
    print(f"Project '{result.get('project_name', project_id)}' initialized.")
    print(f"Phase: {result.get('message', 'specify')}")
    for phase in result.get("phases", []):
        print(f"  - {phase['name']}: {phase['description']}")


def cmd_chat(args):
    """One-shot chat completion."""
    config = load_config()
    model = args.model or config.get("model_raw", "axiovex-agni-raw")
    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.prompt})
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": args.max_tokens or 1024,
    }
    result = api_request(config, "POST", "/v1/chat/completions", body)
    choice = result.get("choices", [{}])[0]
    print(choice.get("message", {}).get("content", ""))
    usage = result.get("usage", {})
    if usage:
        print(f"\n[tokens: {usage.get('prompt_tokens', 0)} in, {usage.get('completion_tokens', 0)} out, {usage.get('total_tokens', 0)} total]")


def cmd_receipt(args):
    """Get run receipt."""
    config = load_config()
    result = api_request(config, "GET", f"/v1/noerelay/runs/{args.run_id}/receipt")
    print(json.dumps(result, indent=2))


# --- Install Helpers ---

INSTALL_COMMANDS = {
    "codex": {
        "npm": ["npm", "install", "-g", "@openai/codex"],
        "pip": None,
        "binary": "codex",
        "description": "OpenAI Codex CLI",
    },
    "aider": {
        "npm": None,
        "pip": ["pip", "install", "aider-chat"],
        "binary": "aider",
        "description": "Aider (AI pair programming)",
    },
    "opencode": {
        "npm": ["npm", "install", "-g", "opencode-ai"],
        "pip": None,
        "binary": "opencode",
        "description": "OpenCode CLI",
    },
    "cursor": {
        "npm": ["npm", "install", "-g", "cursor-agent"],
        "pip": None,
        "binary": "cursor-agent",
        "description": "Cursor CLI (cursor-agent)",
    },
    "cursor-ide": {
        "npm": None,
        "pip": None,
        "binary": None,
        "description": "Cursor IDE (GUI)",
        "winget": ["winget", "install", "Anysphere.Cursor"],
        "url": "https://cursor.com/download",
    },
}


def install_tool(name: str) -> bool:
    """Install a tool if not already present. Returns True if available after."""
    info = INSTALL_COMMANDS.get(name)
    if not info:
        print(f"Unknown tool: {name}")
        return False

    binary = info.get("binary")
    if binary and shutil.which(binary):
        print(f"{info['description']} is already installed.")
        return True

    print(f"Installing {info['description']}...")

    # Try npm, pip, or winget in order
    cmd = info.get("npm") or info.get("pip") or info.get("winget")
    if not cmd:
        # GUI app with no CLI installer — just show the URL
        url = info.get("url")
        winget_cmd = info.get("winget")
        if url:
            print(f"  Download from: {url}")
            if winget_cmd:
                print(f"  Or use winget: {' '.join(winget_cmd)}")
        else:
            print(f"No known install method for {name}.")
        return False

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        # winget returns non-zero if already installed with no upgrade
        if "already installed" in output.lower() or "no available upgrade" in output.lower():
            print(f"{info['description']} is already installed.")
            return True
        print(f"Installation failed. Try manually: {' '.join(cmd)}")
        if output.strip():
            print(f"  {output.strip()}")
        return False

    if binary:
        if shutil.which(binary):
            print(f"{info['description']} installed successfully.")
            return True
        else:
            print(f"Installed but '{binary}' not found in PATH. Check your PATH.")
            return False
    else:
        print(f"{info['description']} installed successfully.")
        return True


# --- Integration Launchers ---

def cmd_run_codex(args):
    """Launch Codex CLI connected to NoeRelay."""
    config = load_config()
    model = args.model or config.get("model_raw", "axiovex-agni-raw")
    base_url = f"{config['base_url']}/v1"

    if not shutil.which("codex"):
        if not install_tool("codex"):
            sys.exit(1)

    codex = shutil.which("codex")
    cmd = [
        codex,
        "--model", model,
        "--base-url", base_url,
        "--api-key", config["api_key"],
    ]
    if args.yes:
        cmd.append("--yes")
    if args.extra:
        # Validate extra args to prevent path injection
        for arg in args.extra:
            if "\0" in arg or arg.startswith("-"):
                print(f"Invalid argument: {arg!r}")
                sys.exit(1)
        cmd.extend(args.extra)

    # Mask API key in output
    safe_cmd = [c if c != config["api_key"] else "***" for c in cmd]
    print(f"Launching: {' '.join(safe_cmd)}")
    subprocess.run(cmd)


def cmd_run_aider(args):
    """Launch Aider connected to NoeRelay."""
    config = load_config()
    model = args.model or config.get("model_raw", "axiovex-agni-raw")
    base_url = f"{config['base_url']}/v1"

    if not shutil.which("aider"):
        if not install_tool("aider"):
            sys.exit(1)

    aider = shutil.which("aider")
    env = os.environ.copy()
    env["OPENAI_API_BASE"] = base_url
    env["OPENAI_API_KEY"] = config["api_key"]

    cmd = [aider, "--model", f"openai/{model}", "--no-show-model-warnings"]
    if args.yes:
        cmd.append("--yes-always")
    if args.extra:
        for arg in args.extra:
            if "\0" in arg or arg.startswith("-"):
                print(f"Invalid argument: {arg!r}")
                sys.exit(1)
        cmd.extend(args.extra)

    safe_cmd = [c if c == config["api_key"] else c for c in cmd]
    print(f"Launching: {' '.join(safe_cmd)}")
    subprocess.run(cmd, env=env)


def cmd_run_cursor(args):
    """Print Cursor setup instructions."""
    config = load_config()
    base_url = f"{config['base_url']}/v1"
    model = config.get("model_raw", "axiovex-agni-raw")

    print("=== Cursor Setup ===\n")
    print("Add this to Cursor Settings > Models > Add Custom Model:\n")
    print(f"  Base URL:  {base_url}")
    masked_key = config["api_key"][:4] + "..." + config["api_key"][-4:] if len(config["api_key"]) > 8 else "***"
    print(f"  API Key:   {masked_key}")
    print(f"  Model ID:  {model}")
    print()
    print("Or add to .cursor/settings.json:")
    settings = {
        "cursor.general.customModels": [
            {
                "id": model,
                "name": "AXIOVEX Agni (Raw)",
                "provider": "openai",
                "baseUrl": base_url,
                "apiKey": config["api_key"],
            }
        ]
    }
    print(json.dumps(settings, indent=2))
    print()
    print("Then reload the Cursor window: Ctrl+Shift+P > Developer: Reload Window")


def cmd_run_opencode(args):
    """Launch OpenCode connected to NoeRelay."""
    config = load_config()
    model = args.model or config.get("model_raw", "axiovex-agni-raw")
    base_url = f"{config['base_url']}/v1"

    if not shutil.which("opencode"):
        if not install_tool("opencode"):
            sys.exit(1)

    opencode = shutil.which("opencode")
    env = os.environ.copy()
    env["OPENAI_API_BASE"] = base_url
    env["OPENAI_API_KEY"] = config["api_key"]

    cmd = [opencode, "--model", model]
    if args.extra:
        for arg in args.extra:
            if "\0" in arg or arg.startswith("-"):
                print(f"Invalid argument: {arg!r}")
                sys.exit(1)
        cmd.extend(args.extra)

    safe_cmd = [c if c == config["api_key"] else c for c in cmd]
    print(f"Launching: {' '.join(safe_cmd)}")
    subprocess.run(cmd, env=env)


def cmd_install(args):
    """Install a tool."""
    if not args.tool:
        print("Available tools: codex, aider, opencode, cursor, cursor-ide")
        sys.exit(0)
    if not install_tool(args.tool):
        sys.exit(1)


# --- Config ---

def cmd_config_show(args):
    """Show current configuration."""
    config = load_config()
    print(f"Config file: {CONFIG_PATH}")
    print()
    for key, value in config.items():
        if key == "api_key":
            value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        print(f"  {key}: {value}")


def cmd_config_set(args):
    """Set a configuration value."""
    config = load_config()
    key = args.key
    value = args.value
    if key not in DEFAULT_CONFIG:
        print(f"Unknown key: {key}. Valid keys: {', '.join(DEFAULT_CONFIG.keys())}")
        sys.exit(1)
    config[key] = value
    save_config(config)
    print(f"Set {key} = {value}")
    print(f"Saved to {CONFIG_PATH}")


# --- Setup (scaffold aider integration in a project) ---


AIDER_PS1 = '''# Start Aider via NoeRelay orchestration.
# Usage: pwsh -NoProfile -File scripts/aider.ps1 [extra aider args...]
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot
try {
    $NoerelayScript = Join-Path $PSScriptRoot 'noerelay.py'
    if (-not (Test-Path $NoerelayScript)) {
        Write-Error "noerelay.py not found at $NoerelayScript"
        exit 1
    }
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $python) {
        Write-Error 'Python is not on PATH.'
        exit 1
    }
    & $python $NoerelayScript run aider @args
    exit $LASTEXITCODE
} finally { Pop-Location }
'''

AIDER_CMD = '''@echo off
REM Start Aider via NoeRelay orchestration.
REM Usage: scripts\\aider.cmd [extra aider args...]
setlocal

where python >nul 2>nul
if errorlevel 1 (
    echo Python is not on PATH.
    exit /b 1
)

python "%~dp0noerelay.py" run aider %*

endlocal & exit /b %ERRORLEVEL%
'''

AIDER_CONF_YML = '''read:
  - CONVENTIONS.md
  - .noerelay/GAPS.md
'''

AIDER_MODEL_METADATA = '''{
  "openai/axiovex-agni": {
    "context_window": 131072,
    "cost_per_token": 0
  }
}
'''

GITIGNORE_ADDITIONS = '''
# Aider (keep config files tracked)
.aider*
!.aider.model.metadata.json
!.aider.conf.yml
'''

def cmd_gaps(args):
    """Generate or update .noerelay/GAPS.md via the AEE engine.

    This is a thin wrapper that delegates to `aee gaps` for backward compatibility.
    The gap register is now managed by the applied-epistemic-engineering package.
    """
    target = os.path.abspath(args.dir or ".")
    matrix_path = os.path.join(target, ".noerelay", "verification-matrix.md")
    evidence_dir = os.path.join(target, "evidence")
    gaps_path = os.path.join(target, ".noerelay", "GAPS.md")

    if not os.path.exists(matrix_path):
        print(f"Error: {matrix_path} not found.")
        print("Cannot generate gaps without a verification matrix.")
        sys.exit(1)

    from pathlib import Path
    from .sdd import generate_gaps
    register = generate_gaps(Path(target), args.close)
    print(f"Gap register written to {gaps_path}")
    print(f"Open: {register.open_count} | Closed: {register.closed_count}")



def cmd_resume(args):
    """Assess current project state for resuming work."""
    target = os.path.abspath(args.dir or ".")

    if not os.path.isdir(target):
        print(f"Error: {target} is not a directory.")
        sys.exit(1)

    print(f"=== NoeRelay Resume: {os.path.basename(target)} ===\n")

    # 1. Read docs/STATE.md
    state_path = os.path.join(target, "docs", "STATE.md")
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Extract key sections
        print("--- State ---")
        for line in content.splitlines():
            if line.startswith("##") or line.startswith("- ") or line.startswith("Updated:"):
                print(f"  {line}")
        print()
    else:
        print("--- State ---")
        print("  No docs/STATE.md found. Project may not be initialized.")
        print()

    # 2. Read .noerelay/GAPS.md (just the count and open items)
    gaps_path = os.path.join(target, ".noerelay", "GAPS.md")
    if os.path.exists(gaps_path):
        with open(gaps_path, "r", encoding="utf-8") as f:
            gaps_content = f.read()
        open_gaps = [l for l in gaps_content.splitlines() if l.startswith("| GAP-") and "closed" not in l.lower() and "resolved" not in l.lower()]
        print(f"--- Gaps ---")
        print(f"  {len(open_gaps)} open gaps")
        for g in open_gaps[:5]:
            print(f"  {g.strip()}")
        if len(open_gaps) > 5:
            print(f"  ... and {len(open_gaps) - 5} more")
        print()

    # 3. Check for active feature folders
    specify_dir = os.path.join(target, ".specify", "features")
    if os.path.isdir(specify_dir):
        features = [d for d in os.listdir(specify_dir) if os.path.isdir(os.path.join(specify_dir, d))]
        if features:
            print("--- Active Features ---")
            for feat in sorted(features):
                feat_dir = os.path.join(specify_dir, feat)
                files = os.listdir(feat_dir)
                phase = "unknown"
                if "spec.md" in files and "plan.md" in files and "tasks.md" in files:
                    phase = "tasks"
                elif "spec.md" in files and "plan.md" in files:
                    phase = "plan"
                elif "spec.md" in files:
                    phase = "specify"
                print(f"  {feat} (phase: {phase})")
            print()

    # 4. Check for .specify/memory/constitution.md
    const_path = os.path.join(target, ".specify", "memory", "constitution.md")
    if os.path.exists(const_path):
        print("--- Constitution ---")
        with open(const_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("## "):
                    print(f"  {line.strip()}")
        print()

    # 5. Next action (from STATE.md)
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            content = f.read()
        in_next = False
        print("--- Next Action ---")
        for line in content.splitlines():
            if line.startswith("## Next action"):
                in_next = True
                continue
            if in_next:
                if line.startswith("## "):
                    break
                if line.strip():
                    print(f"  {line.strip()}")
        print()

    print("=== End Resume ===")
    print("Start aider with: pwsh -NoProfile -File scripts/aider.ps1")


def cmd_setup(args):
    """Scaffold noerelay aider integration in a project directory."""
    target = os.path.abspath(args.dir or ".")

    if not os.path.isdir(target):
        print(f"Error: {target} is not a directory.")
        sys.exit(1)

    scripts_dir = os.path.join(target, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    noerelay_dir = os.path.join(target, ".noerelay")
    os.makedirs(noerelay_dir, exist_ok=True)

    files_to_write = {
        os.path.join(scripts_dir, "aider.ps1"): AIDER_PS1,
        os.path.join(scripts_dir, "aider.cmd"): AIDER_CMD,
        os.path.join(target, ".aider.conf.yml"): AIDER_CONF_YML,
        os.path.join(target, ".aider.model.metadata.json"): AIDER_MODEL_METADATA,
    }

    created = []
    skipped = []
    for path, content in files_to_write.items():
        if os.path.exists(path) and not args.force:
            skipped.append(path)
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(path)

    # Append to .gitignore if it exists
    gitignore_path = os.path.join(target, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            existing = f.read()
        if ".aider*" not in existing:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(GITIGNORE_ADDITIONS)
            created.append(gitignore_path + " (appended)")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(GITIGNORE_ADDITIONS.lstrip())
        created.append(gitignore_path)

    print(f"=== NoeRelay Aider Setup ===")
    print(f"Target: {target}")
    print()
    if created:
        print("Created/updated:")
        for f in created:
            print(f"  + {f}")
    if skipped:
        print("Skipped (already exists, use --force to overwrite):")
        for f in skipped:
            print(f"  = {f}")
    print()
    print("To start an aider session:")
    print(f"  pwsh -NoProfile -File {os.path.join(scripts_dir, 'aider.ps1')}")
    print(f"  or: {os.path.join(scripts_dir, 'aider.cmd')}")
    print()
    print("In the aider prompt, type /noerelay to see available commands.")


# --- Adopt (pull an existing project into the spec-kit + noerelay workflow) ---


CONSTITUTION_MD = '''# Project Constitution

> Living document. Update as the project evolves. Keep entries short and testable.

## Principles

1. **Spec before code.** Every feature starts from a spec, then a plan, then tasks.
2. **Evidence over assertion.** Claims about behavior are backed by a test or a run receipt.
3. **Small, reversible steps.** Prefer changes that are easy to review and roll back.
4. **Document state.** `docs/STATE.md` always reflects where the project stands.

## Conventions

- Feature work lives under `.specify/features/<feature>/` with `spec.md`, `plan.md`, `tasks.md`.
- Open gaps are tracked in `.noerelay/GAPS.md`.
- The verification matrix lives at `.noerelay/verification-matrix.md`.

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
|      |          |           |
'''

STATE_MD = '''# Project State

> Keep this current. `noerelay resume` reads it.

## Summary

- **Project:** (name)
- **Status:** adopted
- **Updated:** (date)

## Next action

- (what to do next)

## Active features

- (none yet)

## Open gaps

- (none yet)
'''

FEATURE_SPEC_TEMPLATE = '''# Spec: {feature}

## Problem

(what problem does this solve?)

## Goals

- (goal 1)

## Non-goals

- (explicitly out of scope)

## Requirements

1. (requirement 1)

## Acceptance criteria

- [ ] (observable, testable criterion)
'''

FEATURE_PLAN_TEMPLATE = '''# Plan: {feature}

## Approach

(how we will build this)

## Components

- (component 1)

## Risks

- (risk 1)
'''

FEATURE_TASKS_TEMPLATE = '''# Tasks: {feature}

- [ ] 1. (task 1)
- [ ] 2. (task 2)
'''

GAPS_MD = '''# Gap Register

> Managed by `noerelay gaps` (delegates to `aee gaps`).

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
'''

VERIFICATION_MATRIX_MD = '''# Verification Matrix

> Maps requirements to evidence. `noerelay gaps` reads this.

| Requirement | Evidence | Status |
|-------------|----------|--------|
'''


def _write_file(path: str, content: str, force: bool, created: list, skipped: list):
    """Write a file unless it exists (and force is not set)."""
    if os.path.exists(path) and not force:
        skipped.append(path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    created.append(path)


def cmd_adopt(args):
    """Adopt an existing project into the spec-kit + noerelay workflow.

    Scaffolds the full structure in one shot:
      - .specify/ (constitution, features/, templates)
      - docs/STATE.md
      - .noerelay/ (gap register + verification matrix)
      - aider integration (scripts/aider.ps1, .aider.conf.yml, ...)

    Idempotent and non-destructive: existing files are skipped unless --force.
    Optionally registers the project on the gateway with --onboard.
    """
    target = os.path.abspath(args.dir or ".")
    if not os.path.isdir(target):
        print(f"Error: {target} is not a directory.")
        sys.exit(1)

    project_name = args.name or os.path.basename(target)
    created, skipped = [], []

    # 1. spec-kit structure
    _write_file(os.path.join(target, ".specify", "memory", "constitution.md"),
                CONSTITUTION_MD, args.force, created, skipped)
    os.makedirs(os.path.join(target, ".specify", "features"), exist_ok=True)
    _write_file(os.path.join(target, ".specify", "templates", "spec.md"),
                FEATURE_SPEC_TEMPLATE.format(feature="<feature>"), args.force, created, skipped)
    _write_file(os.path.join(target, ".specify", "templates", "plan.md"),
                FEATURE_PLAN_TEMPLATE.format(feature="<feature>"), args.force, created, skipped)
    _write_file(os.path.join(target, ".specify", "templates", "tasks.md"),
                FEATURE_TASKS_TEMPLATE.format(feature="<feature>"), args.force, created, skipped)

    # 2. docs
    _write_file(os.path.join(target, "docs", "STATE.md"), STATE_MD, args.force, created, skipped)

    # 3. noerelay managed docs (gap register + verification matrix)
    _write_file(os.path.join(target, ".noerelay", "GAPS.md"), GAPS_MD, args.force, created, skipped)
    _write_file(os.path.join(target, ".noerelay", "verification-matrix.md"),
                VERIFICATION_MATRIX_MD, args.force, created, skipped)

    # 4. aider integration (same files as `setup`)
    scripts_dir = os.path.join(target, "scripts")
    _write_file(os.path.join(scripts_dir, "aider.ps1"), AIDER_PS1, args.force, created, skipped)
    _write_file(os.path.join(scripts_dir, "aider.cmd"), AIDER_CMD, args.force, created, skipped)
    _write_file(os.path.join(target, ".aider.conf.yml"), AIDER_CONF_YML, args.force, created, skipped)
    _write_file(os.path.join(target, ".aider.model.metadata.json"),
                AIDER_MODEL_METADATA, args.force, created, skipped)

    # 5. .gitignore additions
    gitignore_path = os.path.join(target, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            existing = f.read()
        if ".aider*" not in existing:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(GITIGNORE_ADDITIONS)
            created.append(gitignore_path + " (appended)")
    else:
        _write_file(gitignore_path, GITIGNORE_ADDITIONS.lstrip(), args.force, created, skipped)

    # 6. Optional: register on the gateway
    onboarded = False
    if args.onboard:
        try:
            config = load_config()
            project_id = args.project or config.get("project_id", "default")
            body = {
                "project_id": project_id,
                "project_name": project_name,
                "description": args.description or "",
            }
            api_request(config, "POST", "/v1/noerelay/projects/onboard", body)
            onboarded = True
        except Exception as e:
            print(f"\n[warn] Could not onboard on gateway: {e}")

    print(f"=== NoeRelay Adopt: {project_name} ===")
    print(f"Target: {target}\n")
    if created:
        print("Created:")
        for f in created:
            print(f"  + {os.path.relpath(f, target)}")
    if skipped:
        print("\nSkipped (already exists, use --force to overwrite):")
        for f in skipped:
            print(f"  = {os.path.relpath(f, target)}")
    if onboarded:
        print("\nRegistered on gateway.")
    print("\nNext steps:")
    print("  1. Edit .specify/memory/constitution.md for your project's principles.")
    print("  2. Create a feature: .specify/features/<feature>/ (copy from .specify/templates/).")
    print(f"  3. Start an aider session: pwsh -NoProfile -File {os.path.join(scripts_dir, 'aider.ps1')}")
    print("  4. Check state anytime: noerelay resume --dir " + os.path.relpath(target))


# --- Update (refresh noerelay + its dependencies) ---


def _pip_cmd() -> list:
    """Return the best available pip invocation for the current interpreter."""
    import sys
    return [sys.executable, "-m", "pip"]


def _is_editable_install() -> bool:
    """True if noerelay is installed in editable (development) mode."""
    try:
        import noerelay
        path = getattr(noerelay, "__file__", "") or ""
        return path.startswith(os.path.expanduser("~")) or "site-packages" not in path.replace("\\", "/")
    except Exception:
        return False


def _build_update_commands(args) -> list:
    """Build the ordered list of shell commands to update noerelay + deps.

    Pure function (no side effects) so it can be unit-tested. Returns a list of
    (label, argv) tuples.
    """
    pip = _pip_cmd()
    extras = args.extras or "full"
    commands = []

    if args.editable:
        # Development / editable install: refresh the source tree, then reinstall.
        commands.append(("git pull", ["git", "pull", "--ff-only"]))
        commands.append((
            "pip install -e .[{}]".format(extras),
            pip + ["install", "-U", "-e", ".[{}]".format(extras)],
        ))
    else:
        # Standard install: upgrade the published package + its extras.
        commands.append((
            "pip install -U noerelay[{}]".format(extras),
            pip + ["install", "-U", "noerelay[{}]".format(extras)],
        ))

    # Always refresh the core dependencies to their latest compatible versions.
    commands.append((
        "pip install -U (core deps)",
        pip + ["install", "-U", "pip", "setuptools", "wheel"],
    ))

    return commands


def cmd_update(args):
    """Update noerelay and its dependencies.

    - Standard install: `pip install -U noerelay[<extras>]`.
    - Editable/dev install (`--editable`): `git pull` then `pip install -e .[<extras>]`.
    - `--dry-run` prints the commands without running them.
    """
    commands = _build_update_commands(args)

    print("=== NoeRelay Update ===")
    mode = "editable (dev)" if args.editable else "standard"
    print(f"Mode:    {mode}")
    print(f"Extras:  {args.extras or 'full'}")
    print()

    if args.dry_run:
        print("Dry run — commands that would be executed:")
        for label, argv in commands:
            print(f"  $ {' '.join(argv)}   # {label}")
        print("\nRe-run without --dry-run to apply.")
        return

    for label, argv in commands:
        print(f"→ {label}")
        print(f"  $ {' '.join(argv)}")
        try:
            proc = subprocess.run(argv, check=False)
        except FileNotFoundError as e:
            print(f"  [error] Could not run: {e}")
            sys.exit(1)
        if proc.returncode != 0:
            print(f"  [error] Command failed (exit {proc.returncode}). Aborting.")
            sys.exit(proc.returncode)

    print("\nUpdate complete.")
    print("Verify with: noerelay status")


# --- Provisioning / local LLM stack ---

def cmd_detect(args):
    """Detect the local system (OS, CPU, RAM, GPUs, backend)."""
    from .system_info import detect_system

    system = detect_system()
    print("=== NoeRelay System Detection ===")
    for line in system.summary_lines():
        print("  " + line)
    if args.json:
        import dataclasses
        print()
        print(json.dumps(dataclasses.asdict(system), indent=2, default=str))


def cmd_provision(args):
    """Auto-provision the local LLM stack for this machine."""
    from pathlib import Path
    from .system_info import detect_system
    from .provision import make_plan

    system = detect_system()
    install_dir = Path(args.install_dir) if args.install_dir else None
    models_dir = Path(args.models_dir) if args.models_dir else None
    plan = make_plan(
        system,
        install_dir=install_dir,
        models_dir=models_dir,
        model_key=args.model,
        host=args.host,
        port=args.port,
        ctx_size=args.ctx_size,
        parallel=args.parallel,
    )

    print("=== NoeRelay Provision Plan ===")
    for line in plan.summary_lines():
        print("  " + line)

    if args.dry_run:
        print("\n[dry-run] No files written. Re-run without --dry-run to install.")
        return

    from .installer import provision as do_provision

    do_provision(
        install_dir=install_dir,
        models_dir=models_dir,
        model_key=args.model,
        host=args.host,
        port=args.port,
        ctx_size=args.ctx_size,
        parallel=args.parallel,
        skip_download=args.skip_download,
        skip_venv=args.skip_venv,
    )


def cmd_doctor(args):
    """Diagnose the local LLM stack: config, server reachability, CLI."""
    config = load_config()
    base = config["base_url"]
    print("=== NoeRelay Doctor ===")
    print(f"Config base_url: {base}")
    print(f"Config model:    {config.get('model')}")

    # 1) Server reachable?
    try:
        req = urllib.request.Request(f"{base}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            health = json.loads(resp.read().decode())
        print(f"[ok] Server reachable: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"[FAIL] Server unreachable at {base}: {e}")

    # 2) OpenAI-compatible /v1/models?
    try:
        req = urllib.request.Request(f"{base}/v1/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            models = json.loads(resp.read().decode())
        ids = [m.get("id") for m in models.get("data", [])]
        print(f"[ok] /v1/models: {ids}")
    except Exception as e:
        print(f"[FAIL] /v1/models: {e}")

    # 3) A quick chat completion?
    if args.chat:
        try:
            body = {
                "model": config.get("model", "local"),
                "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
                "max_tokens": 16,
            }
            data = json.dumps(body).encode()
            req = urllib.request.Request(
                f"{base}/v1/chat/completions",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                out = json.loads(resp.read().decode())
            text = out.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"[ok] chat completion: {text!r}")
        except Exception as e:
            print(f"[FAIL] chat completion: {e}")


# --- Local LLM lifecycle (llm verb) + HF tooling (hf verb) ---


def _print_local_models(as_json: bool = False) -> None:
    """Print the offline supported local-model catalog (NR-LLM-001)."""
    from .models import supported_models

    rows = supported_models()
    if as_json:
        print(json.dumps(rows, indent=2))
        return
    print("Supported local models (offline catalog):")
    print(f"  {'KEY':<22} {'TIER':<6} {'QUANT':<9} {'SIZE':>6} {'VRAM':>6} {'RAM':>5}  NAME")
    for r in rows:
        mark = "*" if r.get("default") else " "
        print(
            f"  {mark}{r['key']:<21} {r['tier'] or '-':<6} {r['quant']:<9} "
            f"{r['size_gb']:>5.1f}G {r['min_vram_gb']:>5.1f}G {r['min_ram_gb']:>4.0f}G  {r['name']}"
        )
    print("\n  * = provision default; tier: fast (default routing) | hard (escalation only)")


def _llm_common_args(p) -> None:
    p.add_argument("--dir", "-d", default=None,
                   help="Install dir (default: $NOERELAY_LLM_HOME or ~/noerelay-llm)")


def cmd_llm(args):
    """Manage the local llama-server lifecycle (start/stop/status/schedule)."""
    from . import lifecycle
    from .llama_config import LlamaConfigError

    action = args.llm_action
    if not action:
        print("usage: noerelay llm <start|stop|status|schedule|unschedule> [--dir DIR]")
        return

    if action == "start":
        try:
            res = lifecycle.start_server(
                args.dir, wait=args.wait, timeout=args.timeout
            )
        except (lifecycle.LifecycleError, LlamaConfigError) as e:
            print(f"[FAIL] {e}")
            sys.exit(1)
        print(f"[ok] started llama-server (pid {res['pid']})")
        print(f"     base_url: {res['base_url']}")
        print(f"     log:      {res['log']}")
        if args.wait:
            print(f"     ready:    {res.get('ready', False)}")
        return

    if action == "stop":
        res = lifecycle.stop_server(args.dir)
        if res.get("stopped"):
            print(f"[ok] stopped llama-server (pid {res.get('pid')})")
        else:
            print(f"[ok] not running ({res.get('reason', 'no pid')})")
        return

    if action == "status":
        res = lifecycle.server_status(args.dir)
        print("Local llama-server status:")
        print(f"  install_dir:   {res['install_dir']}")
        print(f"  pid:           {res['pid']}")
        print(f"  process_alive: {res['process_alive']}")
        print(f"  base_url:      {res['base_url']}")
        print(f"  api_reachable: {res['api_reachable']}")
        return

    if action == "schedule":
        try:
            res = lifecycle.schedule_task(args.dir, task_name=args.task_name)
        except lifecycle.LifecycleError as e:
            print(f"[FAIL] {e}")
            sys.exit(1)
        print(f"[ok] scheduled logon task: {res.get('task_name')}")
        print(f"     platform: {res.get('platform')}  trigger: {res.get('trigger')}")
        return

    if action == "unschedule":
        res = lifecycle.unschedule_task(args.dir, task_name=args.task_name)
        print(f"[ok] unscheduled (platform {res.get('platform')})")
        if res.get("detail"):
            print(f"     {res['detail']}")
        return


def cmd_hf(args):
    """Hugging Face tooling: search / download / complete (NR-LLM-006)."""
    from pathlib import Path
    from . import hf

    action = args.hf_action
    if not action:
        print("usage: noerelay hf <search|download|complete> [options]")
        return

    if action == "search":
        try:
            results = hf.search_hf(args.query, limit=args.limit, gguf_only=not args.all)
        except RuntimeError as e:
            print(f"[FAIL] {e}")
            sys.exit(1)
        hf.print_search_results(results)
        return

    if action == "download":
        dest = Path(args.dest).expanduser() if args.dest else Path.home() / "noerelay-llm" / "models"
        try:
            final = hf.download_gguf(
                args.repo,
                args.filename or "",
                dest,
                quant=args.quant or "",
                progress=not args.no_progress,
            )
        except RuntimeError as e:
            print(f"[FAIL] {e}")
            sys.exit(1)
        print(f"[ok] downloaded: {final}")
        return

    if action == "complete":
        hf.print_completions(hf.complete(args.token or ""))
        return


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        prog="noerelay",
        description="NoeRelay CLI — manage the NoeRelay gateway",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    subparsers.add_parser("status", help="Check gateway health")
    subparsers.add_parser("mcp", help="Serve the NoeRelay Docker MCP integration over stdio")
    p_agent = subparsers.add_parser("agent", help="Run a bounded agent with Docker tools and automatic SDD")
    p_agent.add_argument("prompt")
    p_agent.add_argument("--project", default="noerelay-agent")
    p_agent.add_argument("--max-steps", type=int, default=4)
    p_agent.add_argument("--escalate", action="store_true")

    # models
    p_models = subparsers.add_parser(
        "models",
        help="List available models (gateway, or --local for the offline catalog)",
    )
    p_models.add_argument("--local", "-l", action="store_true",
                          help="Show the offline supported local model catalog (no gateway needed)")
    p_models.add_argument("--json", "-j", action="store_true",
                          help="JSON output (with --local)")

    # costs
    subparsers.add_parser("costs", help="Show cost report")

    # audit
    p_audit = subparsers.add_parser("audit", help="Check project state")
    p_audit.add_argument("--project", "-p", help="Project ID (default: from config)")

    # onboard
    p_onboard = subparsers.add_parser("onboard", help="Initialize a new project")
    p_onboard.add_argument("--project", "-p", help="Project ID")
    p_onboard.add_argument("--name", "-n", help="Project display name")
    p_onboard.add_argument("--description", "-d", help="Project description")

    # chat
    p_chat = subparsers.add_parser("chat", help="One-shot chat completion")
    p_chat.add_argument("prompt", help="Prompt to send")
    p_chat.add_argument("--system", "-s", help="System prompt")
    p_chat.add_argument("--model", "-m", help="Model ID (default: model_raw)")
    p_chat.add_argument("--max-tokens", "-t", type=int, help="Max tokens (default: 1024)")

    # receipt
    p_receipt = subparsers.add_parser("receipt", help="Get run receipt")
    p_receipt.add_argument("run_id", help="Run ID")

    # install
    p_install = subparsers.add_parser("install", help="Install a CLI tool")
    p_install.add_argument("tool", nargs="?", help="Tool to install: codex, aider, opencode")

    # run (integrations)
    p_run = subparsers.add_parser("run", help="Launch an integration")
    run_sub = p_run.add_subparsers(dest="integration", help="Integration to launch")

    p_codex = run_sub.add_parser("codex", help="Launch Codex CLI")
    p_codex.add_argument("--model", "-m", help="Model ID")
    p_codex.add_argument("--yes", "-y", action="store_true", help="Auto-approve")
    p_codex.add_argument("extra", nargs="*", help="Extra args for codex")

    p_aider = run_sub.add_parser("aider", help="Launch Aider")
    p_aider.add_argument("--model", "-m", help="Model ID")
    p_aider.add_argument("--yes", "-y", action="store_true", help="Auto-approve")
    p_aider.add_argument("extra", nargs="*", help="Extra args for aider")

    p_cursor = run_sub.add_parser("cursor", help="Print Cursor setup")
    p_cursor.add_argument("--model", "-m", help="Model ID")

    p_opencode = run_sub.add_parser("opencode", help="Launch OpenCode")
    p_opencode.add_argument("--model", "-m", help="Model ID")
    p_opencode.add_argument("extra", nargs="*", help="Extra args for opencode")

    # setup
    p_setup = subparsers.add_parser("setup", help="Scaffold noerelay aider integration in a project")
    p_setup.add_argument("--dir", "-d", help="Target project directory (default: current)")
    p_setup.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")

    # adopt
    p_adopt = subparsers.add_parser(
        "adopt",
        help="Adopt an existing project into the spec-kit + noerelay workflow (one-shot)",
    )
    p_adopt.add_argument("--dir", "-d", help="Target project directory (default: current)")
    p_adopt.add_argument("--name", "-n", help="Project display name (default: directory name)")
    p_adopt.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")
    p_adopt.add_argument("--onboard", "-o", action="store_true",
                         help="Also register the project on the gateway")
    p_adopt.add_argument("--project", "-p", help="Project ID for onboarding (default: from config)")
    p_adopt.add_argument("--description", help="Project description for onboarding")

    # update
    p_update = subparsers.add_parser(
        "update",
        help="Update noerelay and its dependencies",
    )
    p_update.add_argument("--editable", "-e", action="store_true",
                          help="Treat as an editable/dev install (git pull + pip install -e .)")
    p_update.add_argument("--extras", default="full",
                          help="Extra dependency set to install: ui, models, full (default: full)")
    p_update.add_argument("--dry-run", "-n", action="store_true",
                          help="Print the commands without running them")

    # resume
    p_resume = subparsers.add_parser("resume", help="Assess project state for resuming work")
    p_resume.add_argument("--dir", "-d", help="Target project directory (default: current)")

    # gaps
    p_gaps = subparsers.add_parser("gaps", help="Generate/update .noerelay/GAPS.md gap register")
    p_gaps.add_argument("--dir", "-d", help="Target project directory (default: current)")
    p_gaps.add_argument("--close", "-c", help="Mark a gap as closed (e.g., GAP-001)")

    # config
    p_config = subparsers.add_parser("config", help="Manage configuration")
    config_sub = p_config.add_subparsers(dest="config_action", help="Config action")
    config_sub.add_parser("show", help="Show current config")
    p_set = config_sub.add_parser("set", help="Set a config value")
    p_set.add_argument("key", help="Config key")
    p_set.add_argument("value", help="Config value")

    # detect
    p_detect = subparsers.add_parser("detect", help="Detect local system (OS, CPU, RAM, GPUs, backend)")
    p_detect.add_argument("--json", "-j", action="store_true", help="Also print machine-readable JSON")

    # provision
    p_prov = subparsers.add_parser("provision", help="Auto-provision the local LLM stack for this machine")
    p_prov.add_argument("--install-dir", help="Install directory (default: ~/noerelay-llm)")
    p_prov.add_argument("--models-dir", help="Models directory (default: <install-dir>/models)")
    p_prov.add_argument("--model", "-m", help="Force a model key (e.g. qwen2.5-7b)")
    p_prov.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    p_prov.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    p_prov.add_argument("--ctx-size", type=int, help="Context size (default: auto)")
    p_prov.add_argument("--parallel", type=int, default=1, help="Parallel slots (default: 1)")
    p_prov.add_argument("--dry-run", action="store_true", help="Show the plan without installing")
    p_prov.add_argument("--skip-download", action="store_true", help="Skip llama.cpp/model downloads")
    p_prov.add_argument("--skip-venv", action="store_true", help="Skip venv/CLI setup")

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Diagnose the local LLM stack")
    p_doctor.add_argument("--chat", action="store_true", help="Also run a quick chat completion")

    # llm (local llama-server lifecycle — NR-LLM-004)
    p_llm = subparsers.add_parser(
        "llm",
        help="Manage the local llama-server (start/stop/status/schedule)",
    )
    llm_sub = p_llm.add_subparsers(dest="llm_action", help="LLM action")

    p_llm_start = llm_sub.add_parser("start", help="Start the local llama-server (detached)")
    _llm_common_args(p_llm_start)
    p_llm_start.add_argument("--wait", "-w", action="store_true",
                             help="Wait for /health before returning")
    p_llm_start.add_argument("--timeout", type=int, default=180,
                             help="Ready-wait timeout in seconds (default: 180)")

    p_llm_stop = llm_sub.add_parser("stop", help="Stop the local llama-server")
    _llm_common_args(p_llm_stop)

    p_llm_status = llm_sub.add_parser("status", help="Show local server process + API status")
    _llm_common_args(p_llm_status)

    p_llm_sched = llm_sub.add_parser(
        "schedule", help="Register a logon scheduled task (native, no PowerShell)")
    _llm_common_args(p_llm_sched)
    p_llm_sched.add_argument("--task-name", default="NoeRelay LLM Server",
                             help="Scheduled task name (default: NoeRelay LLM Server)")

    p_llm_unsched = llm_sub.add_parser("unschedule", help="Remove the logon scheduled task")
    _llm_common_args(p_llm_unsched)
    p_llm_unsched.add_argument("--task-name", default="NoeRelay LLM Server",
                               help="Scheduled task name (default: NoeRelay LLM Server)")

    # hf (Hugging Face tooling — NR-LLM-006)
    p_hf = subparsers.add_parser(
        "hf",
        help="Hugging Face tooling (search / download / complete)",
    )
    hf_sub = p_hf.add_subparsers(dest="hf_action", help="HF action")

    p_hf_search = hf_sub.add_parser("search", help="Search Hugging Face for GGUF model repos")
    p_hf_search.add_argument("query", help="Search query (e.g. gpt-oss-20b)")
    p_hf_search.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    p_hf_search.add_argument("--all", action="store_true",
                             help="Include non-GGUF repos")

    p_hf_dl = hf_sub.add_parser("download", help="Download a GGUF (progress + resume)")
    p_hf_dl.add_argument("repo", help="HF repo id (e.g. unsloth/gpt-oss-20b-GGUF)")
    p_hf_dl.add_argument("filename", nargs="?", default=None,
                         help="Exact file name (default: best match for --quant)")
    p_hf_dl.add_argument("--quant", "-q", default=None,
                         help="Quant filter when picking the file (e.g. Q4_K_M)")
    p_hf_dl.add_argument("--dest", "-d", default=None,
                         help="Destination directory (default: ~/noerelay-llm/models)")
    p_hf_dl.add_argument("--no-progress", action="store_true", help="Disable progress output")

    p_hf_complete = hf_sub.add_parser(
        "complete", help="Offline completions for model/quant tokens (tab-completion hook)")
    p_hf_complete.add_argument("token", nargs="?", default="",
                               help="Token prefix to complete (e.g. gpt-oss, Q4_)")

    # req (requirement + release-test management over the append-only contract)
    p_req = subparsers.add_parser(
        "req",
        help="Manage requirements and release tests (coverage contract)",
    )
    req_sub = p_req.add_subparsers(dest="req_action", help="Req action")

    p_req_list = req_sub.add_parser("list", help="List requirements with coverage status")
    p_req_list.add_argument("--root", "-r", help="Repo root (default: auto-detect from cwd)")
    p_req_list.add_argument("--verbose", "-v", action="store_true", help="List skipped non-envelope files")

    p_req_show = req_sub.add_parser("show", help="Show one requirement with evidence")
    p_req_show.add_argument("requirement_id", help="Requirement ID (e.g. NR-LLM-001)")
    p_req_show.add_argument("--root", "-r", help="Repo root (default: auto-detect)")

    p_req_tests = req_sub.add_parser("tests", help="List release tests with evidence status")
    p_req_tests.add_argument("--root", "-r", help="Repo root (default: auto-detect)")

    p_req_add = req_sub.add_parser("add", help="Append a new requirement (append-only)")
    p_req_add.add_argument("requirement_id", help="New requirement ID (NR-<AREA>-NNN)")
    p_req_add.add_argument("text", help="Requirement text")
    p_req_add.add_argument("acceptance", help="Acceptance outcome")
    p_req_add.add_argument("--packages", "-p", help="Comma-separated work packages (e.g. LLM-01)")
    p_req_add.add_argument("--tests", "-t", help="Comma-separated release test IDs (e.g. T-LLM-007)")
    p_req_add.add_argument("--section", "-s", help="Section heading in requirements.md (default: Phase 2 additions)")
    p_req_add.add_argument("--gate", "-g", help="Gate ID to add the requirement to (e.g. G9)")
    p_req_add.add_argument("--gate-desc", help="Gate description when creating a new gate")
    p_req_add.add_argument("--root", "-r", help="Repo root (default: auto-detect)")

    p_req_test = req_sub.add_parser("test", help="Append a release test to an existing requirement")
    p_req_test.add_argument("requirement_id", help="Existing requirement ID")
    p_req_test.add_argument("test_id", help="New release test ID (T-<AREA>-NNN)")
    p_req_test.add_argument("--gate", "-g", help="Gate ID to add the test to")
    p_req_test.add_argument("--root", "-r", help="Repo root (default: auto-detect)")

    p_req_cov = req_sub.add_parser("coverage", help="Coverage report (mirrors xtask evidence coverage)")
    p_req_cov.add_argument("--root", "-r", help="Repo root (default: auto-detect)")
    p_req_cov.add_argument("--strict", action="store_true", help="Exit 1 if any requirement is not covered")
    p_req_cov.add_argument("--verbose", "-v", action="store_true", help="Print per-requirement detail")

    p_req_gate = req_sub.add_parser("gate", help="Check one gate (mirrors xtask evidence gate)")
    p_req_gate.add_argument("gate_id", help="Gate ID (e.g. G9)")
    p_req_gate.add_argument("--root", "-r", help="Repo root (default: auto-detect)")
    p_req_gate.add_argument("--strict", action="store_true", help="Exit 1 if the gate fails")

    p_req_rec = req_sub.add_parser("record", help="Run a command and record an evidence envelope")
    p_req_rec.add_argument("--work-package-id", "-w", required=True, help="Work package ID (e.g. LLM-01)")
    p_req_rec.add_argument("--test-id", "-t", required=True, help="Release test ID (e.g. T-LLM-001)")
    # NOTE: dest must NOT be "command" — that collides with the top-level
    # subparsers dest and would clobber args.command after parsing.
    p_req_rec.add_argument("--command", "-c", dest="record_command", required=True,
                           help="Command to run (executed from the repo root)")
    p_req_rec.add_argument("--requirements", "-q", required=True, help="Comma-separated requirement IDs this evidence covers")
    p_req_rec.add_argument("--profile", default="single-region-org-v1-local-test", help="Environment profile")
    p_req_rec.add_argument("--runner", default="ROLE-RUST", help="Runner identity")
    p_req_rec.add_argument("--verifier", help="Independent verifier identity (optional)")
    p_req_rec.add_argument("--evidence-dir", default="evidence", help="Evidence directory (default: evidence)")
    p_req_rec.add_argument("--root", "-r", help="Repo root (default: auto-detect)")

    p_req_regen = req_sub.add_parser("regenerate", help="Regenerate .specify/features/ from the manifest")
    p_req_regen.add_argument("--root", "-r", help="Repo root (default: auto-detect)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "mcp":
        from .mcp_stdio import main as mcp_main
        mcp_main()
    elif args.command == "agent":
        from .mcp_stdio import local_config
        result = api_request(local_config(), "POST", "/v1/noerelay/agent", {
            "prompt": args.prompt, "project": args.project,
            "max_steps": args.max_steps, "escalate": args.escalate,
        })
        print(json.dumps(result, indent=2))
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "models":
        cmd_models(args)
    elif args.command == "costs":
        cmd_costs(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "onboard":
        cmd_onboard(args)
    elif args.command == "chat":
        cmd_chat(args)
    elif args.command == "receipt":
        cmd_receipt(args)
    elif args.command == "install":
        cmd_install(args)
    elif args.command == "setup":
        cmd_setup(args)
    elif args.command == "adopt":
        cmd_adopt(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "resume":
        cmd_resume(args)
    elif args.command == "gaps":
        cmd_gaps(args)
    elif args.command == "detect":
        cmd_detect(args)
    elif args.command == "provision":
        cmd_provision(args)
    elif args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "llm":
        cmd_llm(args)
    elif args.command == "hf":
        cmd_hf(args)
    elif args.command == "req":
        from . import reqtest
        if not args.req_action:
            p_req.print_help()
            sys.exit(0)
        _req_handlers = {
            "list": reqtest.cmd_req_list,
            "show": reqtest.cmd_req_show,
            "tests": reqtest.cmd_req_tests,
            "add": reqtest.cmd_req_add,
            "test": reqtest.cmd_req_test,
            "coverage": reqtest.cmd_req_coverage,
            "gate": reqtest.cmd_req_gate,
            "record": reqtest.cmd_req_record,
            "regenerate": reqtest.cmd_req_regenerate,
        }
        sys.exit(_req_handlers[args.req_action](args))
    elif args.command == "run":
        if not args.integration:
            p_run.print_help()
            sys.exit(0)
        if args.integration == "codex":
            cmd_run_codex(args)
        elif args.integration == "aider":
            cmd_run_aider(args)
        elif args.integration == "cursor":
            cmd_run_cursor(args)
        elif args.integration == "opencode":
            cmd_run_opencode(args)
    elif args.command == "config":
        if not args.config_action:
            p_config.print_help()
            sys.exit(0)
        if args.config_action == "show":
            cmd_config_show(args)
        elif args.config_action == "set":
            cmd_config_set(args)


if __name__ == "__main__":
    main()
