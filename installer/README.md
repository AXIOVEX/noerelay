# NoeRelay Unified Installer

A polished, interactive installer that sets up the **complete** local AI stack
on Windows in one place — the NoeRelay CLI, a dual-GPU `llama.cpp` inference
server, and a GGUF model — all bundled together.

## What it installs

Everything lands in a single directory (default `C:\LLM`) so the whole stack
is self-contained and easy to move or remove:

```
C:\LLM\
├── llama\                  # llama.cpp binaries + CUDA runtime DLLs
├── noerelay\               # bundled NoeRelay CLI package (stdlib-only)
├── noerelay.cmd            # CLI launcher
├── start-llama-server.ps1  # start the inference server
├── stop-llama-server.ps1   # stop the inference server
├── create-scheduled-task.ps1 / .cmd   # optional logon autostart
├── config.json             # machine-readable install config
└── README.md
C:\Models\                  # GGUF model files
```

## Requirements

* Windows 10/11
* Python 3.9+
* `rich`, `requests`, `huggingface_hub`

```powershell
pip install rich requests huggingface_hub
```

## Usage

```powershell
# Interactive (recommended)
python installer/installer.py

# Non-interactive, all defaults
python installer/installer.py --yes

# Pick a different model
python installer/installer.py --model mistral-24b

# Custom locations / options
python installer/installer.py --install-dir D:\LLM --models-dir D:\Models `
    --port 8080 --ctx 16384 --no-scheduled-task
```

### CLI flags

| Flag | Description |
|------|-------------|
| `--yes`, `-y` | Non-interactive; accept all defaults |
| `--model KEY` | Model key from the catalog (see below) |
| `--install-dir PATH` | Install directory (default `C:\LLM`) |
| `--models-dir PATH` | Model directory (default `C:\Models`) |
| `--port N` | Server port (default `8080`) |
| `--ctx N` | Context size (default `16384`) |
| `--split A,B` | Tensor-split (default: auto-recommended from GPUs) |
| `--no-scheduled-task` | Skip registering the logon Scheduled Task |
| `--no-noerelay` | Skip bundling the NoeRelay CLI |
| `--noerelay-src PATH` | Point at a specific noerelay package source |
| `--skip-download` | Skip llama.cpp + model downloads |
| `--skip-verify` | Skip the verification smoke test |

## Model catalog

| Key | Model | ~Size | Notes |
|-----|-------|-------|-------|
| `qwen3.8-27b` | Qwen3.8 27B (Q4_K_M) | 15.3 GB | **Default** — strong all-rounder |
| `qwen3-32b` | Qwen3 32B (Q4_K_M) | 20 GB | Larger, higher quality |
| `qwen2.5-32b` | Qwen2.5 32B Instruct (Q4_K_M) | 20 GB | Good tool-use |
| `mistral-24b` | Mistral Small 24B (Q4_K_M) | 14.5 GB | Fast, efficient |
| `deepseek-r1-32b` | DeepSeek-R1 Distill Qwen 32B (Q4_K_M) | 20 GB | Reasoning-focused |
| `llama-3.3-70b` | Llama 3.3 70B (Q4_K_M) | 42 GB | Exceeds 28 GB VRAM (CPU offload) |

In interactive mode you can also choose **`c`** to enter a custom
HuggingFace repo + quantization.

## How it works

1. **Preflight** — checks OS, Python, `nvidia-smi`, disk space, admin rights,
   and locates the NoeRelay package source.
2. **GPU detection** — reads `nvidia-smi` and recommends a tensor-split
   proportional to VRAM, reducing the display-driving GPU by 20% to leave
   headroom for the desktop compositor.
3. **Model selection** — catalog with a default, or a custom HF repo.
4. **llama.cpp build** — downloads a pinned, self-contained CUDA build
   (executables + CUDA runtime DLLs) with live progress bars.
5. **Model download** — fetches the chosen GGUF via `huggingface_hub`. If a
   single `.gguf` already exists in the models dir, it is adopted instead of
   re-downloaded.
6. **NoeRelay bundling** — copies the stdlib-only NoeRelay CLI into the
   install dir and creates a `noerelay.cmd` launcher.
7. **Scripts + config** — writes the start/stop scripts, scheduled-task
   scripts, `config.json`, and a `README.md`, and points
   `~/.noerelay/config.json` at the local server.
8. **Scheduled task** — registers a logon task (requires admin; otherwise
   prints the command to run manually).
9. **Verification** — enumerates CUDA devices and runs a short-lived API
   smoke test against `/v1/models`.

## After install

```powershell
# Start the server
powershell -File C:\LLM\start-llama-server.ps1

# Use the NoeRelay CLI
C:\LLM\noerelay.cmd chat "Hello"

# Point apps at the OpenAI-compatible API
#   Base URL: http://127.0.0.1:8080/v1
#   API key:  any non-empty string
#   Model:    qwen3.8-27b
```

## Notes

* The server binds to `127.0.0.1` by default — it is **not** exposed to the
  network. Change `--host` in the start script only if you need LAN access,
  and then restrict it with Windows Firewall.
* The pinned llama.cpp build uses **CUDA 13.3**, required for Blackwell GPUs
  (e.g. RTX 5060 Ti).
* To remove the whole stack, delete `C:\LLM` and `C:\Models`.
