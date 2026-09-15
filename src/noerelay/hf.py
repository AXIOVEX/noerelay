"""
Hugging Face model operations for the noerelay CLI (NR-LLM-006).

* **search** — find GGUF repos/models on the Hub (``huggingface_hub`` when
  installed, stdlib JSON-API fallback otherwise).
* **download** — fetch a GGUF file with progress and resume (HTTP Range),
  stdlib-only.
* **autocomplete** — shell-style suggestions for model identifiers and quant
  names; catalog entries are suggested offline (no network round-trip).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import MODEL_CATALOG, models_by_tier

HF_API = "https://huggingface.co/api"
USER_AGENT = "noerelay/0.2 (+local)"

#: Quant names offered by the autocomplete, most common first.
KNOWN_QUANTS = [
    "Q2_K", "Q3_K_S", "Q3_K_M", "Q3_K_L",
    "Q4_0", "Q4_1", "Q4_K_S", "Q4_K_M", "Q4_K_L",
    "Q5_0", "Q5_1", "Q5_K_S", "Q5_K_M", "Q5_K_L",
    "Q6_K", "Q6_K_L",
    "Q8_0", "F16", "BF16", "F32",
    "IQ1_S", "IQ1_M", "IQ2_XXS", "IQ2_XS", "IQ2_S", "IQ2_M",
    "IQ3_XXS", "IQ3_XS", "IQ3_S", "IQ3_M",
    "IQ4_XS", "IQ4_NL",
]


# ---------------------------------------------------------------------------
# Autocomplete (offline catalog + known quants)
# ---------------------------------------------------------------------------


def catalog_completions(prefix: str = "") -> List[str]:
    """Offline completions for model keys / filenames / repo ids.

    No network access — sourced from the bundled catalog (NR-LLM-006).
    """
    prefix = (prefix or "").lower()
    out: List[str] = []
    seen = set()
    for m in MODEL_CATALOG:
        for cand in (m.key, m.filename or f"{m.key}.gguf", m.repo_id, m.quant):
            c = cand.lower()
            if c != prefix and c.startswith(prefix) and c not in seen:
                seen.add(c)
                out.append(cand)
    return out[:40]


def quant_completions(prefix: str = "") -> List[str]:
    """Offline completions for quantization names."""
    prefix = (prefix or "").upper()
    return [q for q in KNOWN_QUANTS if q.startswith(prefix)][:40]


def complete(token: str = "") -> List[str]:
    """Suggest identifiers for the given token.

    Heuristic: tokens containing ``/`` or ending in ``.gguf`` are treated as
    repo/file identifiers; short all-caps-ish tokens as quants.
    """
    if re.fullmatch(r"[A-Z0-9_]{0,8}", token or ""):
        return quant_completions(token)
    return catalog_completions(token)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_hf(query: str, limit: int = 20, gguf_only: bool = True) -> List[Dict[str, Any]]:
    """Search Hugging Face for model repos matching *query*.

    Prefers GGUF repos (inference-ready).  Uses ``huggingface_hub`` when
    available, otherwise the public JSON API (stdlib).
    """
    try:
        from huggingface_hub import HfApi  # type: ignore
        api = HfApi()
        models = api.list_models(search=query, limit=limit, sort="downloads")
        results = [
            {
                "repo_id": m.id,
                "downloads": getattr(m, "downloads", 0),
                "likes": getattr(m, "likes", 0),
                "gguf": "gguf" in (m.id or "").lower(),
            }
            for m in models
        ]
    except ImportError:
        params: Dict[str, str] = {"search": query, "limit": str(limit), "sort": "downloads"}
        url = f"{HF_API}/models?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError(f"HF search failed (offline?): {exc}") from None
        results = [
            {
                "repo_id": d.get("id", ""),
                "downloads": d.get("downloads", 0),
                "likes": d.get("likes", 0),
                "gguf": "gguf" in (d.get("id") or "").lower(),
            }
            for d in data
        ]
    if gguf_only:
        gguf = [r for r in results if r.get("gguf")]
        if gguf:
            return gguf[:limit]
    return results[:limit]


def list_repo_files(repo_id: str) -> List[str]:
    """List files in a HF repo (GGUFs first)."""
    try:
        from huggingface_hub import HfApi  # type: ignore
        files = HfApi().list_repo_files(repo_id)
    except ImportError:
        url = f"{HF_API}/models/{urllib.parse.quote(repo_id)}/tree/main"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        files = [d.get("path", "") for d in data if d.get("type") == "file"]
    gguf = [f for f in files if f.lower().endswith(".gguf")]
    others = [f for f in files if f not in gguf]
    return gguf + others


def pick_gguf_file(repo_id: str, quant: str = "") -> Optional[str]:
    """Choose the best single-file GGUF in *repo_id* matching *quant*."""
    try:
        files = list_repo_files(repo_id)
    except Exception:  # noqa: BLE001
        return None
    cands = [f for f in files if f.lower().endswith(".gguf")]
    if quant:
        q = quant.lower()
        qmatch = [f for f in cands if q in f.lower()]
        if qmatch:
            cands = qmatch
    single = [f for f in cands if re.search(r"of-\d+", f) is None]
    pool = single or cands
    if not pool:
        return None

    def size_key(f: str) -> int:
        m = re.search(r"(\d+)[._-]gguf$", f, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    return sorted(pool, key=lambda f: (size_key(f), len(f)), reverse=True)[0]


# ---------------------------------------------------------------------------
# Download (progress + resume, stdlib)
# ---------------------------------------------------------------------------


def download_gguf(
    repo_id: str,
    filename: str,
    dest_dir: Path,
    quant: str = "",
    chunk_size: int = 1 << 20,
    progress: bool = True,
) -> Path:
    """Download a GGUF from *repo_id* with progress and resume.

    Resume uses HTTP Range: an existing partial ``<name>.part`` file is
    continued from its size.  Renames to the final name on completion.
    """
    if not filename:
        filename = pick_gguf_file(repo_id, quant) or ""
    if not filename:
        raise RuntimeError(f"no GGUF file found in {repo_id}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    final = dest_dir / filename
    if final.is_file():
        return final

    url = f"https://huggingface.co/{repo_id}/resolve/main/{urllib.parse.quote(filename)}"
    part = dest_dir / (filename + ".part")

    position = part.stat().st_size if part.is_file() else 0
    if position > 0 and progress:
        print(f"resuming {final.name} from {position // (1 << 20)} MiB", file=sys.stderr)

    headers = {"User-Agent": USER_AGENT}
    if position > 0:
        headers["Range"] = f"bytes={position}-"

    last_draw = 0.0
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            code = getattr(resp, "status", 200)
            if position > 0 and code == 200:
                # Server ignored Range — restart.
                position = 0
                part.write_bytes(b"")
            total_hdr = resp.headers.get("Content-Range") or resp.headers.get("Content-Length")
            total = None
            if total_hdr:
                m = re.search(r"/(\d+)$", str(total_hdr))
                if m:
                    total = int(m.group(1))
                elif str(total_hdr).isdigit():
                    total = position + int(total_hdr)
            mode = "ab" if position > 0 and code == 206 else "wb"
            if mode == "wb":
                position = 0
            with open(part, mode) as fh:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    fh.write(chunk)
                    position += len(chunk)
                    if progress:
                        now = time.time()
                        if now - last_draw >= 0.5:
                            last_draw = now
                            if total:
                                pct = 100.0 * position / total
                                print(
                                    f"\r  {final.name}: {position // (1 << 20)} / "
                                    f"{total // (1 << 20)} MiB ({pct:5.1f}%)",
                                    end="", file=sys.stderr,
                                )
                            else:
                                print(f"\r  {final.name}: {position // (1 << 20)} MiB",
                                      end="", file=sys.stderr)
        if progress:
            print(file=sys.stderr)
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(
            f"download interrupted at {position} bytes "
            f"(re-run to resume): {exc}"
        ) from None

    os.replace(part, final)
    return final


# ---------------------------------------------------------------------------
# CLI-facing helpers
# ---------------------------------------------------------------------------


def print_search_results(results: List[Dict[str, Any]]) -> None:
    if not results:
        print("No Hugging Face repos found.")
        return
    print(f"{'REPO':<52} {'DOWNLOADS':>10}  GGUF")
    for r in results:
        print(f"{r['repo_id']:<52} {r.get('downloads', 0):>10}  {'yes' if r.get('gguf') else 'no'}")


def print_completions(comps: List[str]) -> None:
    for c in comps:
        print(c)
