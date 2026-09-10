# Start Aider against the local OpenAI-compatible endpoint.
# Usage: pwsh -NoProfile -File scripts/aider.ps1 [extra aider args...]
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot
try {
    $AiderModel = 'openai/axiovex-agni-raw'
    $AiderApiBase = 'http://localhost:8080/v1'
    $AiderApiKey = 'noerelay-local-development-key-0001'

    # Aider lives in the system Python (Scoop), not the project venv.
    $systemPython = 'C:\\Users\\trist\\scoop\\apps\\python312\\current\\python.exe'
    if (-not (Test-Path $systemPython)) {
        $systemPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    }
    if (-not $systemPython) {
        Write-Error 'Python is not on PATH.'
        exit 1
    }

    $wrapper = Join-Path $PSScriptRoot 'aider_noerelay.py'
    & $systemPython $wrapper --model $AiderModel --openai-api-base $AiderApiBase --openai-api-key $AiderApiKey --no-show-model-warnings @args
    exit $LASTEXITCODE
} finally { Pop-Location }
