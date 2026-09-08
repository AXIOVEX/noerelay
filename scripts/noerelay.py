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
    config show         Show current configuration
    config set          Set configuration values
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


def api_request(config: dict, method: str, path: str, body: dict = None) -> dict:
    """Make an API request to the NoeRelay gateway."""
    url = f"{config['base_url']}{path}"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
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
    """List available models."""
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
        cmd.extend(args.extra)

    print(f"Launching: {' '.join(cmd)}")
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

    cmd = [aider, "--model", f"openai/{model}"]
    if args.yes:
        cmd.append("--yes-always")
    if args.extra:
        cmd.extend(args.extra)

    print(f"Launching: {' '.join(cmd)}")
    subprocess.run(cmd, env=env)


def cmd_run_cursor(args):
    """Print Cursor setup instructions."""
    config = load_config()
    base_url = f"{config['base_url']}/v1"
    model = config.get("model_raw", "axiovex-agni-raw")

    print("=== Cursor Setup ===\n")
    print("Add this to Cursor Settings > Models > Add Custom Model:\n")
    print(f"  Base URL:  {base_url}")
    print(f"  API Key:   {config['api_key']}")
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
        cmd.extend(args.extra)

    print(f"Launching: {' '.join(cmd)}")
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


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        prog="noerelay",
        description="NoeRelay CLI — manage the NoeRelay gateway",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    subparsers.add_parser("status", help="Check gateway health")

    # models
    subparsers.add_parser("models", help="List available models")

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

    # config
    p_config = subparsers.add_parser("config", help="Manage configuration")
    config_sub = p_config.add_subparsers(dest="config_action", help="Config action")
    config_sub.add_parser("show", help="Show current config")
    p_set = config_sub.add_parser("set", help="Set a config value")
    p_set.add_argument("key", help="Config key")
    p_set.add_argument("value", help="Config value")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "status":
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
