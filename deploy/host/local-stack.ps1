#Requires -Version 5.1
param([ValidateSet('start','stop','restart','status')][string]$Action = 'status')
$ErrorActionPreference = 'Stop'
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$State = Join-Path $Root '.noerelay\runtime'
New-Item -ItemType Directory -Force -Path $State | Out-Null
Push-Location $Root
try {
    if ($Action -in @('stop','restart')) {
        Set-Content -LiteralPath (Join-Path $State 'STOPPED') -Value 'Manual stop; start clears this flag.'
        docker compose --env-file .env.docker stop
        if ($LASTEXITCODE) { throw 'Docker stop failed' }
        & 'C:\LLM\stop-llama-server.ps1'
        try { Invoke-RestMethod 'http://127.0.0.1:8082/shutdown' -Method Post -TimeoutSec 5 | Out-Null } catch { }
        for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
            try { Invoke-RestMethod 'http://127.0.0.1:8082/health' -TimeoutSec 1 | Out-Null; Start-Sleep -Milliseconds 200 }
            catch { break }
        }
        # Docker CLI can leave its MCP plugin child alive on Windows.
        Get-CimInstance Win32_Process -Filter "Name = 'docker-mcp.exe'" |
            Where-Object { $_.CommandLine -match 'gateway run --profile ai_coding --transport streaming --host 127\.0\.0\.1 --port 8811(?:\s|$)' } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
    }
    if ($Action -in @('start','restart')) {
        Remove-Item -LiteralPath (Join-Path $State 'STOPPED') -ErrorAction SilentlyContinue
        & 'C:\LLM\start-llama-server.ps1'
        docker compose --env-file .env.docker up -d --remove-orphans
        if ($LASTEXITCODE) { throw 'Docker startup failed' }
    }
    docker compose --env-file .env.docker ps -a
    foreach ($Endpoint in @('http://127.0.0.1:8080/ready','http://127.0.0.1:8081/health','http://127.0.0.1:8082/health')) {
        try { Write-Host "$Endpoint $(Invoke-RestMethod $Endpoint -TimeoutSec 5 | ConvertTo-Json -Compress)" }
        catch { Write-Host "$Endpoint unavailable" }
    }
    if (Test-Path (Join-Path $State 'STOPPED')) { Write-Host 'Manually stopped; watchdog restart suppressed.' }
} finally { Pop-Location }
