#Requires -Version 5.1
<#
.SYNOPSIS
    LLM Watchdog — keeps the session llama-server (127.0.0.1:8081) alive.

.DESCRIPTION
    Runs as a Windows scheduled task (every 1 minute). If the server is down
    AND we are not in maintenance mode, it restarts the server via the
    sanctioned C:\LLM\start-llama-server.ps1 (never a raw PID kill).

    Maintenance mode: the T-LLM-003 benchmark orchestrator writes C:\LLM\MAINTENANCE
    (a Unix timestamp) before it stops the server for exclusive GPU access.
    While that flag is fresh (< 90 min), the watchdog stays quiet. If the flag
    goes stale (orchestrator hard-killed), the watchdog revives the server.

    This is the OS-level last line of defense so the agent session's inference
    backend is always restored even if the orchestrator process dies.
#>
$ErrorActionPreference = "SilentlyContinue"

$Flag      = "C:\LLM\MAINTENANCE"
$Health    = "http://127.0.0.1:8081/health"
$Start     = "C:\LLM\start-llama-server.ps1"
$MaxMaintMin = 90

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (Test-Path (Join-Path $RepoRoot '.noerelay\runtime\STOPPED')) { exit 0 }

# 1) Maintenance mode? (set by the benchmark orchestrator)
if (Test-Path $Flag) {
    $stale = $true
    try {
        $ts  = [double]((Get-Content $Flag -Raw).Trim())
        $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        $stale = (($now - $ts) -gt ($MaxMaintMin * 60))
    } catch { $stale = $true }
    if (-not $stale) { exit 0 }   # active maintenance: stay quiet
}

# 2) Already healthy?
try {
    $r = Invoke-WebRequest -Uri $Health -UseBasicParsing -TimeoutSec 5
    $adapter = Invoke-WebRequest -Uri 'http://127.0.0.1:8082/health' -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -eq 200 -and $adapter.StatusCode -eq 200) { exit 0 }
} catch { }

# 3) Server process already running (maybe still loading)? Don't double-start.
# The sanctioned starter independently checks both processes, including a missing adapter.

# 4) Down and no process -> restart via the sanctioned start script (detached).
try {
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$Start`"" `
        -WindowStyle Hidden
} catch { }
exit 0
