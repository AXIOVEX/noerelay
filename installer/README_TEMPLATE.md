# NoeRelay Local LLM Stack

A self-contained, **cross-platform** local inference stack. It bundles the
**NoeRelay CLI**, a **`llama.cpp`** inference server, and a **GGUF model** into
one directory so the whole thing is easy to run, configure, optimize, and
remove.

Installed by the NoeRelay provisioner on __DATE__.

- **OS:** __OS__
- **Backend:** __BACKEND__
- **Build:** __BUILD__

> This README is for the **installed stack** (what you get after running
> `noerelay provision`). The NoeRelay *project* itself (the orchestration
> framework) is documented in the repository root `README.md`.

---

## Table of contents

1. [What's in the stack](#1-whats-in-the-stack)
2. [How it works](#2-how-it-works)
3. [Directory layout](#3-directory-layout)
4. [Getting started](#4-getting-started)
5. [Configuration](#5-configuration)
6. [Using the NoeRelay CLI](#6-using-the-noerelay-cli)
7. [Using the OpenAI-compatible API](#7-using-the-openai-compatible-api)
8. [Optimization guide](#8-optimization-guide)
9. [Model management](#9-model-management)
10. [Autostart](#10-autostart)
11. [Troubleshooting](#11-troubleshooting)
12. [Uninstall / rollback](#12-uninstall--rollback)

---

## 1. What's in the stack

| Component | What it is | Where |
|-----------|-----------|-------|
| **llama.cpp server** | The inference engine. Loads the GGUF model, offloads layers to the accelerator(s), and serves an OpenAI-compatible API. | `llama/` (build __BUILD__) |
| **GGUF model** | The quantized model weights (installed: __MODEL_NAME__). | `__MODEL__` |
| **NoeRelay CLI** | A Python command-line client that talks to the server. Lives in a virtualenv. | `venv/` + `bin/noerelay` |
| **Scripts** | Activate the venv, start/stop the server, register autostart. | `bin/` |
| **Config** | Machine-readable record of the install + the CLI's connection settings. | `config.json`, `~/.noerelay/config.json` |

The server exposes an **OpenAI-compatible API** at `__API_BASE__/v1`.
Anything that speaks the OpenAI chat-completions protocol (the NoeRelay CLI,
`curl`, the Python `openai` SDK, Aider, Open WebUI, etc.) can use it.

---

## 2. How it works

```
  Your app / CLI / SDK
  (noerelay CLI, curl, openai SDK, Aider, ...)
        |
        |  HTTP  POST /v1/chat/completions
        |         GET  /v1/models
        v
  +------------------------------------------------------+
  |  llama.cpp server   (__API_BASE__)                   |
  |  - loads the GGUF model                              |
  |  - offloads layers to the accelerator(s)             |
  |  - manages KV cache, slots, concurrency              |
  +------------------------------------------------------+
        |
        v
  +---------------------+   +---------------------+
  |  accelerator 0      |   |  accelerator 1       |
  |  (weight __SPLIT__) |   |                      |
  +---------------------+   +---------------------+
```

**Key ideas:**

- **Auto-detected backend.** The provisioner inspects the machine and picks the
  right llama.cpp build and offload strategy:
  - `cuda` — one or more NVIDIA GPUs (Windows / Linux).
  - `metal` — Apple Silicon (M1/M2/M3/M4) using the unified-memory Metal backend.
  - `cpu` — no accelerator; CPU-only inference.
- **Multi-GPU split (CUDA only).** With two or more NVIDIA GPUs, the model's
  transformer layers are divided across them by a relative weight
  (`--tensor-split __SPLIT__`). Each GPU holds a slice of the weights and they
  cooperate per forward pass. This is different from running two independent
  models. With a single GPU (or on Metal/CPU) there is no split.
- **Display GPU gets less (CUDA).** The GPU driving your monitors is given a
  smaller weight so the desktop compositor keeps headroom. The compute-only GPU
  takes the larger share.
- **OpenAI-compatible wire protocol.** The server speaks the standard
  `/v1/chat/completions` and `/v1/models` endpoints, so no client needs a
  llama.cpp-specific integration.
- **NoeRelay CLI is a thin client.** It reads `~/.noerelay/config.json` for the
  base URL + model, then POSTs to the server. It does not load the model itself.

> **Note on model names:** llama.cpp serves whichever model it was started with
> and ignores the `model` field in the request body. So the NoeRelay CLI's
> `model` value is effectively a label — it can be anything non-empty.

---

## 3. Directory layout

```
<install_dir>/
├── llama/                          # llama.cpp binaries + backend libs
│   ├── llama-server                #   the inference server
│   ├── llama-cli                   #   CLI (also used for --list-devices)
│   └── ...                         #   backend DLLs / .so / .dylib
├── venv/                           # Python virtualenv (noerelay CLI + deps)
├── models/                         # GGUF model files
│   └── <model>.gguf
├── bin/                            # OS-appropriate launchers
│   ├── noerelay                    #   CLI wrapper (activates venv)
│   ├── activate.{sh|bat}           #   activate the venv
│   ├── start-server.{sh|bat}       #   start the server (edit to tune)
│   ├── stop-server.{sh|bat}        #   stop the server
│   └── autostart.{sh|bat}          #   register autostart (see §10)
├── config.json                     # machine-readable install record
└── README.md                       # this file

~/.noerelay/
└── config.json                     # NoeRelay CLI connection settings
```

---

## 4. Getting started

### Prerequisites

- Python 3.9+ on `PATH` (the provisioner creates the virtualenv for you).
- **CUDA:** an up-to-date NVIDIA driver (all GPUs visible in Device Manager /
  `nvidia-smi`). On a dual-GPU box, connect your displays to the *display* GPU.
- **Metal:** Apple Silicon with a recent macOS.
- **CPU:** nothing special.

### Activate the environment

```bash
# macOS / Linux
source <install_dir>/bin/activate.sh

# Windows
<install_dir>\bin\activate.bat
```

Once active, the `noerelay` command is on your `PATH`.

### Start the server

```bash
# macOS / Linux
<install_dir>/bin/start-server.sh

# Windows
<install_dir>\bin\start-server.bat
```

The first load takes a few seconds (it reads the model into memory). When you
see `listening on __API_BASE__`, it's ready.

### Verify it's up

```bash
# List models
curl __API_BASE__/v1/models

# Watch the accelerator(s) while it runs
nvidia-smi -l 1        # CUDA
```

### Send a request

```bash
<install_dir>/bin/noerelay chat "Hello, are you running locally?"
```

### Stop the server

```bash
# macOS / Linux
<install_dir>/bin/stop-server.sh

# Windows
<install_dir>\bin\stop-server.bat
```

---

## 5. Configuration

There are **two config files** with different jobs.

### 5a. NoeRelay CLI settings — `~/.noerelay/config.json`

Controls what the CLI connects to.

```json
{
  "base_url": "__API_BASE__",
  "api_key": "noerelay-local",
  "model": "__MODEL_NAME__",
  "model_raw": "__MODEL_NAME__",
  "project_id": "default"
}
```

| Key | Meaning |
|-----|---------|
| `base_url` | Server address (no trailing `/v1`). Must match the server's `--host`/`--port`. |
| `api_key` | Any non-empty string (llama.cpp ignores it). |
| `model` / `model_raw` | Label sent in requests. Ignored by llama.cpp; keep it stable. |
| `project_id` | NoeRelay project identifier. |

**Change it three ways:**

```bash
# a) via the CLI
<install_dir>/bin/noerelay config show
<install_dir>/bin/noerelay config set base_url __API_BASE__

# b) edit the JSON file directly

# c) environment variables (override the file)
export NOERELAY_BASE_URL="__API_BASE__"
export NOERELAY_API_KEY="noerelay-local"
```

### 5b. LLM server settings — `bin/start-server.{sh|bat}`

The server's runtime knobs live in the **start script** (the `config.json` in
the install dir is just a record, not read by the server). The provisioner
generates it with the detected values:

```
-m <model> --host 127.0.0.1 --port 8080 --ctx-size __CTX__ --parallel __PARALLEL__
-ngl __NGUPLAYER__ [--split-mode layer --tensor-split __SPLIT__]
```

| Flag | Meaning |
|------|---------|
| `-m <model>` | Path to the GGUF file. |
| `--host` | Bind address. `127.0.0.1` = local only. Use `0.0.0.0` for LAN (then firewall it). |
| `--port` | Port (default 8080). |
| `-ngl __NGUPLAYER__` | Layers to offload to the accelerator (999 = "all", 0 = CPU-only). |
| `--split-mode layer` | Split by layer across GPUs (CUDA multi-GPU only). |
| `--tensor-split __SPLIT__` | Relative weight per GPU, in CUDA order (multi-GPU only). |
| `--ctx-size __CTX__` | Context window (tokens). |
| `--parallel __PARALLEL__` | Concurrent request slots. |

**After editing, restart the server** (stop then start).

> If you change `--port`, also update `base_url` in `~/.noerelay/config.json`.

---

## 6. Using the NoeRelay CLI

`<install_dir>/bin/noerelay <command> [options]`

| Command | Purpose |
|---------|---------|
| `chat "prompt" [-s system] [-m model] [-t max_tokens]` | One-shot chat completion |
| `status` | Check gateway health |
| `models` | List available models |
| `costs` | Show cost report |
| `audit [-p project]` | Check project state |
| `onboard [-p id] [-n name] [-d desc]` | Initialize a project |
| `receipt <run_id>` | Get a run receipt |
| `config show` / `config set <key> <value>` | Manage CLI config |
| `run codex\|aider\|cursor\|opencode` | Launch an integration |
| `install codex\|aider\|opencode` | Install a CLI tool |
| `setup [-d dir] [-f]` | Scaffold the aider integration in a project |
| `resume [-d dir]` | Assess project state for resuming |
| `gaps [-d dir] [-c GAP-001]` | Manage the gap register |
| `detect` | Detect this machine (OS, CPU, RAM, GPUs, backend) |
| `provision [--dry-run]` | Auto-provision the local LLM stack |
| `doctor [--chat]` | Diagnose the local LLM stack |

Examples:

```bash
<install_dir>/bin/noerelay chat "Explain KV cache in one paragraph."
<install_dir>/bin/noerelay chat "Write a Python fib function." -s "You are a terse expert." -t 400
<install_dir>/bin/noerelay models
<install_dir>/bin/noerelay config set model __MODEL_NAME__
<install_dir>/bin/noerelay detect
<install_dir>/bin/noerelay doctor --chat
```

> **Scope note:** `chat`, `models`, `detect`, `provision`, `doctor`, and the
> OpenAI-compatible endpoints work against the llama.cpp server directly. The
> NoeRelay-*specific* commands (`status`, `audit`, `onboard`, `receipt`,
> `costs`) target the full NoeRelay gateway (`/v1/noerelay/...`), which is a
> separate service — they will not work against a bare llama.cpp server.

---

## 7. Using the OpenAI-compatible API

Base URL: `__API_BASE__/v1`

### List models

```bash
curl __API_BASE__/v1/models
```

### Chat completion (curl)

```bash
curl __API_BASE__/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
        "model": "__MODEL_NAME__",
        "messages": [{"role": "user", "content": "Say hello."}],
        "max_tokens": 100
      }'
```

### Python `openai` SDK

```python
from openai import OpenAI

client = OpenAI(base_url="__API_BASE__/v1", api_key="local")
resp = client.chat.completions.create(
    model="__MODEL_NAME__",
    messages=[{"role": "user", "content": "Say hello."}],
    max_tokens=100,
)
print(resp.choices[0].message.content)
```

### Aider / Open WebUI / other tools

Point them at `__API_BASE__/v1` with any non-empty API key and model name
`__MODEL_NAME__`.

---

## 8. Optimization guide

Tune in this order. After each change, restart the server and watch the
accelerator plus the server's timing lines (`prompt eval … t/s`,
`eval … t/s`).

### 8.1 GPU allocation (`--tensor-split`, CUDA multi-GPU only)

The split is a **relative weight**, not gigabytes. The provisioner recommends
one automatically (VRAM-proportional, display GPU reduced 20%). Start there,
then nudge:

| Try | When |
|-----|------|
| `__SPLIT__` | Current recommendation |
| shift weight to the idle GPU | If one GPU is at ~100% and the other is idle |
| reduce the display GPU's weight | If the display GPU is tight |

**Rules of thumb:**
- Never fill a GPU completely. Leave ~1–2 GB headroom for the backend + KV cache.
- The display GPU should keep extra headroom for the compositor.
- If one GPU is at ~100% and the other is idle, shift weight toward the idle one.

### 8.2 Context length (`--ctx-size`)

KV-cache memory grows with context and is the usual limiting factor once the
weights fit. Test in this order:

```
4096 -> 8192 -> 16384
```

- Use the **largest stable** value for your typical prompts.
- Don't assume the model's advertised max context is practical here.
- If you see OOM or the model fails to load, drop `--ctx-size`.

### 8.3 Concurrency (`--parallel`)

- `--parallel 1` is best for a personal server (lowest latency, one request at
  a time).
- `--parallel 2` only after single-request is stable. Each extra slot adds KV
  cache memory and can reduce responsiveness.

### 8.4 Quantization

- **Q4_K_M** is the sweet spot for quality/size (what the default model uses).
- If you need more memory headroom, a **Q3** or **IQ3** quant is smaller but
  lower quality.
- If you have memory to spare, **Q5_K_M** / **Q6_K** are higher quality but
  larger.

### 8.5 KV cache type

llama.cpp can quantize the KV cache to save memory (at a small quality cost).
Add `--cache-type-k q8_0 --cache-type-v q8_0` to the start script if you want
to fit a larger context in the same memory.

### 8.6 Monitoring

```bash
nvidia-smi -l 1                 # CUDA: live GPU memory + utilization
curl __API_BASE__/metrics       # Prometheus metrics (if --metrics)
```

Watch for:
- **Accelerator memory** near the total → reduce ctx or shift the split.
- **One GPU idle** while the other is busy → rebalance the split.
- **Generation t/s** → your headline throughput.

---

## 9. Model management

### Switch models

1. Download a new GGUF into the models dir (any filename, e.g.
   `mistral-24b.gguf`).
2. Edit `bin/start-server.{sh|bat}` → set the `-m` path to the new file.
3. Restart the server.
4. (Optional) update `model` in `~/.noerelay/config.json`.

### Re-run the provisioner to pick a different model

```bash
noerelay provision --model mistral-24b
```

The provisioner will download the new model and regenerate the scripts. It
**adopts** an existing model file in the models dir instead of re-downloading
if one is already there.

### Verify a model file

```bash
<install_dir>/llama/llama-cli -m "<models_dir>/your-model.gguf" --list-devices
```

---

## 10. Autostart

Start the server automatically at login.

### Windows (Scheduled Task)

```bat
:: Run from an ELEVATED (Administrator) prompt
<install_dir>\bin\autostart.bat
```

This registers a **NoeRelayLLM** task that runs the start script at logon.
Manage it with `Get-ScheduledTask -TaskName NoeRelayLLM`,
`Disable-ScheduledTask`, `Enable-ScheduledTask`, or
`Unregister-ScheduledTask -TaskName NoeRelayLLM -Confirm:$false`.

> An interactive (logon) task is used deliberately because the display GPU
> drives the displays; an early-boot background task may not have it ready.

### macOS (LaunchAgent)

```bash
<install_dir>/bin/autostart.sh
```

This installs a `com.noerelay.llm` LaunchAgent that runs the start script at
login. Remove it with
`launchctl unload ~/Library/LaunchAgents/com.noerelay.llm.plist`.

### Linux (systemd user service)

Create `~/.config/systemd/user/noerelay-llm.service`:

```ini
[Unit]
Description=NoeRelay local LLM server

[Service]
ExecStart=<install_dir>/bin/start-server.sh
Restart=on-failure

[Install]
WantedBy=default.target
```

Then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now noerelay-llm
```

---

## 11. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `llama-server` not found | Re-run `noerelay provision`; check `llama/`. |
| Model fails to load | Lower `--ctx-size`; check the file is a valid single-file GGUF; check disk space. |
| Only one GPU used (CUDA) | Confirm both GPUs are visible: `llama/llama-cli --list-devices`. Check `--tensor-split` has two values. |
| Compute GPU shows display activity | A monitor is plugged into it. Move both cables to the display GPU and reboot. |
| Port 8080 already in use | Another process is on 8080. Change `--port` (and `base_url`), or stop the other process. |
| CLI can't reach server | Is the server running? Does `base_url` match `--host`/`--port`? Test with `curl __API_BASE__/v1/models`. |
| Slow generation | Reduce `--ctx-size`; ensure the split uses both GPUs; close memory-hungry apps. |
| `CUDA error` / no devices | Update the NVIDIA driver; confirm the build's CUDA matches. |
| Metal: slow / OOM | Reduce `--ctx-size`; close other GPU apps; unified memory is shared with the CPU. |
| Autostart won't register | Windows: run the `.bat` as **Administrator**. macOS: check `~/Library/LaunchAgents`. |

### Useful diagnostics

```bash
<install_dir>/bin/noerelay doctor --chat      # end-to-end health check
<install_dir>/llama/llama-cli --list-devices  # which accelerators does llama.cpp see?
nvidia-smi                                    # CUDA: driver + per-GPU memory
curl __API_BASE__/v1/models                   # is the API up?
```

---

## 12. Uninstall / rollback

### Stop the server

```bash
# macOS / Linux
<install_dir>/bin/stop-server.sh

# Windows
<install_dir>\bin\stop-server.bat
```

### Remove autostart (if registered)

```bat
:: Windows
Unregister-ScheduledTask -TaskName NoeRelayLLM -Confirm:$false
```

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/com.noerelay.llm.plist
rm ~/Library/LaunchAgents/com.noerelay.llm.plist
```

```bash
# Linux
systemctl --user disable --now noerelay-llm
rm ~/.config/systemd/user/noerelay-llm.service
```

### Remove the stack

```bash
rm -rf <install_dir>
rm -rf <models_dir>
rm -rf ~/.noerelay    # optional: CLI config
```

### Roll back to another local server (e.g. Ollama)

If you later run a different local server, point your apps back at its address
and set the NoeRelay CLI `base_url` accordingly:

```bash
<install_dir>/bin/noerelay config set base_url http://127.0.0.1:11434
```

---

## Quick reference

| Task | Command |
|------|---------|
| Activate env | `source <install_dir>/bin/activate.sh` (or `activate.bat`) |
| Start server | `<install_dir>/bin/start-server.sh` (or `.bat`) |
| Stop server | `<install_dir>/bin/stop-server.sh` (or `.bat`) |
| Chat | `<install_dir>/bin/noerelay chat "…"` |
| List models | `curl __API_BASE__/v1/models` |
| Watch GPUs | `nvidia-smi -l 1` |
| Detect system | `<install_dir>/bin/noerelay detect` |
| Diagnose | `<install_dir>/bin/noerelay doctor --chat` |
| Show CLI config | `<install_dir>/bin/noerelay config show` |
| Set CLI config | `<install_dir>/bin/noerelay config set <key> <value>` |
| Autostart | `<install_dir>/bin/autostart.{sh|bat}` (Windows: as admin) |
| Reinstall / change model | `noerelay provision --model <key>` |
