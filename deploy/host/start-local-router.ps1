#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$State = Join-Path $Root '.noerelay\runtime'
New-Item -ItemType Directory -Force -Path $State | Out-Null
if (Test-Path (Join-Path $State 'STOPPED')) { exit 0 }
try {
    Invoke-RestMethod 'http://127.0.0.1:8082/health' -TimeoutSec 2 | Out-Null
} catch {
    $Resolved = docker compose --project-directory $Root --env-file (Join-Path $Root '.env.docker') config --format json | ConvertFrom-Json
    if ($LASTEXITCODE) { throw 'Cannot resolve local service configuration' }
    $env:LITELLM_MASTER_KEY = $Resolved.services.litellm.environment.LITELLM_MASTER_KEY
    $env:NOERELAY_API_KEY = $Resolved.services.noerelay.environment.NOERELAY_API_KEY
    $env:OPEN_TERMINAL_API_KEY = $Resolved.services.'open-terminal'.environment.OPEN_TERMINAL_API_KEY
    Start-Process -FilePath (Get-Command python.exe).Source -ArgumentList @(
        ('"' + (Join-Path $Root 'deploy\host\local-model-plane.py') + '"')
    ) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $State 'rtk.jsonl') -RedirectStandardError (Join-Path $State 'rtk.stderr.log')
    $Ready = $false
    for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
        try { Invoke-RestMethod 'http://127.0.0.1:8082/health' -TimeoutSec 2 | Out-Null; $Ready = $true; break }
        catch { Start-Sleep -Seconds 1 }
    }
    if (-not $Ready) { throw 'RTK/SDD/Docker MCP startup failed; see .noerelay/runtime/rtk.stderr.log' }
}
if (-not (Get-Process llama-server -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath 'C:\LLM\llama\llama-server.exe' -ArgumentList @(
        '--models-preset', ('"' + (Join-Path $Root 'deploy\host\local-models.ini') + '"'),
        '--models-max', '1', '--host', '127.0.0.1', '--port', '8081'
    ) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $State 'router.stdout.log') -RedirectStandardError (Join-Path $State 'router.stderr.log')
}
