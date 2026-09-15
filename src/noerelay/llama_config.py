"""
Master YAML configuration for the llama.cpp server (NR-LLM-005).

A single ``llama.yaml`` carries **all** llama-server settings matching the
reference ``start-llama-server`` argument set:

    -m <model> --host --port --n-gpu-layers --split-mode --tensor-split
    --ctx-size --parallel --batch-size --ubatch-size --flash-attn
    --cache-type-k --cache-type-v --no-mtp --no-reasoning-preserve --metrics

The provisioner generates the server invocation from this file
(:func:`server_args_from_config`), and schema validation rejects unknown
keys (:func:`validate_llama_config`).

The core package stays stdlib-only: when ``pyyaml`` is installed it is used;
otherwise a built-in mini-parser handles the subset of YAML this file uses
(nested mappings, scalars, inline and block lists, comments).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

#: Current schema version written into ``llama.yaml``.
SCHEMA_VERSION = 1

#: Top-level keys allowed in the master config.
TOP_KEYS: Dict[str, type] = {
    "version": int,
    "server": dict,
}

#: Keys allowed under ``server:`` and their expected types.
SERVER_KEYS: Dict[str, type] = {
    "model": str,             # absolute path to the GGUF file
    "model_key": str,         # catalog key (alternative to model)
    "host": str,
    "port": int,
    "n_gpu_layers": int,
    "split_mode": str,        # none | layer | row
    "tensor_split": str,      # e.g. "10,15"
    "ctx_size": int,
    "parallel": int,
    "batch_size": int,
    "ubatch_size": int,
    "flash_attn": str,        # auto | on | off
    "cache_type_k": str,      # e.g. q4_0
    "cache_type_v": str,
    "no_mtp": bool,
    "no_reasoning_preserve": bool,
    "metrics": bool,
    "extra_args": list,       # verbatim extra CLI args
}

#: Valid values for enumerated keys.
_ENUMS: Dict[str, Tuple[str, ...]] = {
    "split_mode": ("none", "layer", "row"),
    "flash_attn": ("auto", "on", "off"),
}

#: Reference defaults (match the operator's C:\LLM config.json /
#: start-llama-server.ps1 argument set).
DEFAULT_SERVER: Dict[str, Any] = {
    "model": "",
    "model_key": "",
    "host": "127.0.0.1",
    "port": 8080,
    "n_gpu_layers": 999,
    "split_mode": "none",
    "tensor_split": "",
    "ctx_size": 131072,
    "parallel": 1,
    "batch_size": 512,
    "ubatch_size": 256,
    "flash_attn": "auto",
    "cache_type_k": "q4_0",
    "cache_type_v": "q4_0",
    "no_mtp": False,
    "no_reasoning_preserve": True,
    "metrics": True,
    "extra_args": [],
}


class LlamaConfigError(ValueError):
    """Raised when the master config fails schema validation."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_llama_config(cfg: Any) -> Dict[str, Any]:
    """Validate *cfg* against the master schema; return the merged config.

    Unknown keys are rejected (NR-LLM-005).  Missing keys take the reference
    defaults.  Raises :class:`LlamaConfigError` on any schema violation.
    """
    if not isinstance(cfg, dict):
        raise LlamaConfigError(f"top level must be a mapping, got {type(cfg).__name__}")

    problems: List[str] = []
    for key in cfg:
        if key not in TOP_KEYS:
            problems.append(f"unknown top-level key {key!r}")
    if problems:
        raise LlamaConfigError("; ".join(problems))

    version = cfg.get("version", SCHEMA_VERSION)
    if not isinstance(version, int) or version < 1:
        raise LlamaConfigError(f"'version' must be a positive integer, got {version!r}")

    raw_server = cfg.get("server", {})
    if raw_server is None:
        raw_server = {}
    if not isinstance(raw_server, dict):
        raise LlamaConfigError(f"'server' must be a mapping, got {type(raw_server).__name__}")

    for key in raw_server:
        if key not in SERVER_KEYS:
            problems.append(f"unknown server key {key!r}")
    if problems:
        raise LlamaConfigError("; ".join(problems))

    merged: Dict[str, Any] = dict(DEFAULT_SERVER)
    merged.update(raw_server)

    for key, typ in SERVER_KEYS.items():
        value = merged.get(key)
        if value is None:
            continue
        if typ is bool:
            if not isinstance(value, bool):
                raise LlamaConfigError(f"server.{key} must be a boolean, got {value!r}")
        elif typ is int:
            if isinstance(value, bool) or not isinstance(value, int):
                raise LlamaConfigError(f"server.{key} must be an integer, got {value!r}")
        elif typ is str:
            if not isinstance(value, str):
                raise LlamaConfigError(f"server.{key} must be a string, got {value!r}")
        elif typ is list:
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise LlamaConfigError(f"server.{key} must be a list of strings, got {value!r}")

    for key, allowed in _ENUMS.items():
        value = merged.get(key)
        if isinstance(value, str) and value not in allowed:
            raise LlamaConfigError(
                f"server.{key} must be one of {list(allowed)}, got {value!r}"
            )

    if merged.get("tensor_split"):
        parts = str(merged["tensor_split"]).split(",")
        if not all(p.strip().isdigit() and int(p) > 0 for p in parts):
            raise LlamaConfigError(
                f"server.tensor_split must be positive comma-separated ints, got {merged['tensor_split']!r}"
            )

    return {"version": version, "server": merged}


# ---------------------------------------------------------------------------
# Server argument generation
# ---------------------------------------------------------------------------


def server_args_from_config(cfg: Dict[str, Any], model_path: Optional[str] = None) -> List[str]:
    """Generate the llama-server CLI arguments from a validated config.

    The output matches the reference ``start-llama-server`` argument set
    (NR-LLM-005).  *model_path* overrides ``server.model`` when given.
    """
    server = cfg["server"] if isinstance(cfg, dict) and "server" in cfg else dict(DEFAULT_SERVER, **cfg)
    model = model_path or server.get("model") or ""
    if not model:
        raise LlamaConfigError("no model path: set server.model or pass model_path")

    args: List[str] = ["-m", model]
    args += ["--host", str(server["host"]), "--port", str(server["port"])]

    # Always emitted (explicit 0 for CPU-only hosts; llama.cpp defaults to 999).
    args += ["--n-gpu-layers", str(int(server.get("n_gpu_layers", 0)))]

    split_mode = str(server.get("split_mode", "none"))
    if split_mode in ("layer", "row"):
        args += ["--split-mode", split_mode]
        tensor_split = str(server.get("tensor_split", ""))
        if tensor_split:
            args += ["--tensor-split", tensor_split]

    args += [
        "--ctx-size", str(int(server["ctx_size"])),
        "--parallel", str(int(server["parallel"])),
        "--batch-size", str(int(server["batch_size"])),
        "--ubatch-size", str(int(server["ubatch_size"])),
    ]

    flash_attn = str(server.get("flash_attn", "auto"))
    if flash_attn:
        args += ["--flash-attn", flash_attn]

    cache_k = str(server.get("cache_type_k", ""))
    if cache_k:
        args += ["--cache-type-k", cache_k]
    cache_v = str(server.get("cache_type_v", ""))
    if cache_v:
        args += ["--cache-type-v", cache_v]

    if server.get("no_mtp"):
        args.append("--no-mtp")
    if server.get("no_reasoning_preserve"):
        args.append("--no-reasoning-preserve")
    if server.get("metrics", True):
        args.append("--metrics")

    extra = server.get("extra_args") or []
    args += [str(a) for a in extra]
    return args


# ---------------------------------------------------------------------------
# YAML loading (pyyaml when present, mini-parser fallback)
# ---------------------------------------------------------------------------


def load_llama_config(text: str) -> Dict[str, Any]:
    """Parse and validate a master-config YAML document."""
    data = _yaml_load(text)
    return validate_llama_config(data)


def _yaml_load(text: str) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError:
        return _mini_yaml_load(text)
    try:
        return yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        raise LlamaConfigError(f"YAML parse error: {exc}") from exc


def _strip_comment(line: str) -> str:
    in_s = in_d = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "#" and not in_s and not in_d:
            if i == 0 or line[i - 1] in " \t":
                return line[:i]
    return line


def _parse_scalar(tok: str) -> Any:
    tok = tok.strip()
    if tok == "":
        return None
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ("'", '"'):
        return tok[1:-1]
    low = tok.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~", "none"):
        return None
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    try:
        return float(tok)
    except ValueError:
        return tok


def _mini_yaml_load(text: str) -> Any:
    """Parse the YAML subset used by llama.yaml (stdlib fallback)."""
    entries: List[Tuple[int, str]] = []
    for raw in text.splitlines():
        line = _strip_comment(raw.rstrip())
        if not line.strip():
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise LlamaConfigError("tabs are not allowed for YAML indentation")
        indent = len(line) - len(line.lstrip(" "))
        entries.append((indent, line.strip()))
    if not entries:
        return {}
    value, idx = _parse_node(entries, 0, entries[0][0])
    if idx != len(entries):
        raise LlamaConfigError(f"unparsed YAML content near {entries[idx][1]!r}")
    return value


def _parse_node(entries: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[Any, int]:
    if entries[idx][1].startswith("- ") or entries[idx][1] == "-":
        return _parse_list(entries, idx, indent)
    return _parse_mapping(entries, idx, indent)


def _parse_mapping(entries: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[Dict[str, Any], int]:
    out: Dict[str, Any] = {}
    while idx < len(entries):
        ind, content = entries[idx]
        if ind < indent or content.startswith("- ") or content == "-":
            break
        if ind > indent:
            raise LlamaConfigError(f"bad indentation near {content!r}")
        if ":" not in content:
            raise LlamaConfigError(f"expected 'key: value' near {content!r}")
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if not key:
            raise LlamaConfigError(f"empty key near {content!r}")
        if rest == "":
            if idx + 1 < len(entries) and entries[idx + 1][0] > ind:
                value, idx = _parse_node(entries, idx + 1, entries[idx + 1][0])
                out[key] = value
            else:
                out[key] = None
                idx += 1
        else:
            if rest.startswith("[") and rest.endswith("]"):
                inner = rest[1:-1].strip()
                out[key] = [_parse_scalar(t) for t in inner.split(",")] if inner else []
            else:
                out[key] = _parse_scalar(rest)
            idx += 1
    return out, idx


def _parse_list(entries: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[List[Any], int]:
    out: List[Any] = []
    while idx < len(entries):
        ind, content = entries[idx]
        if ind != indent or not (content.startswith("- ") or content == "-"):
            break
        out.append(_parse_scalar(content[2:] if content.startswith("- ") else ""))
        idx += 1
    return out, idx


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_llama_config(cfg: Dict[str, Any]) -> str:
    """Render a validated config as llama.yaml text (stable key order)."""
    server = cfg["server"]
    lines = [
        "# NoeRelay master llama-server configuration (schema v1, NR-LLM-005).",
        "# All llama-server settings live here; the provisioner generates the",
        "# server invocation from this file.",
        f"version: {int(cfg.get('version', SCHEMA_VERSION))}",
        "server:",
        # Single-quoted strings: double quotes would make Windows backslash
        # paths (C:\Models\...) invalid YAML escapes under PyYAML.
        f"  model: '{server.get('model', '')}'",
        f"  model_key: '{server.get('model_key', '')}'",
        f"  host: {server.get('host', '127.0.0.1')}",
        f"  port: {int(server.get('port', 8080))}",
        f"  n_gpu_layers: {int(server.get('n_gpu_layers', 999))}",
        f"  split_mode: {server.get('split_mode', 'none')}",
        f"  tensor_split: '{server.get('tensor_split', '')}'",
        f"  ctx_size: {int(server.get('ctx_size', 131072))}",
        f"  parallel: {int(server.get('parallel', 1))}",
        f"  batch_size: {int(server.get('batch_size', 512))}",
        f"  ubatch_size: {int(server.get('ubatch_size', 256))}",
        f"  flash_attn: {server.get('flash_attn', 'auto')}",
        f"  cache_type_k: {server.get('cache_type_k', 'q4_0')}",
        f"  cache_type_v: {server.get('cache_type_v', 'q4_0')}",
        f"  no_mtp: {str(bool(server.get('no_mtp', True))).lower()}",
        f"  no_reasoning_preserve: {str(bool(server.get('no_reasoning_preserve', True))).lower()}",
        f"  metrics: {str(bool(server.get('metrics', True))).lower()}",
    ]
    extra = server.get("extra_args") or []
    if extra:
        lines.append("  extra_args:")
        lines += [f"    - {a}" for a in extra]
    return "\n".join(lines) + "\n"
