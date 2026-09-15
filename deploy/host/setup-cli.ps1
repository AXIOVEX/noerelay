param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$venv = Join-Path $repo '.noerelay/cli-venv'
& $Python -m venv $venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
$exe = Join-Path $venv 'Scripts/python.exe'
& $exe -m pip install -e $repo
if ($LASTEXITCODE -ne 0) { throw 'NoeRelay CLI installation failed' }
Write-Output "Activate: & '$venv/Scripts/Activate.ps1'"
Write-Output 'Then: noerelay client setup all; noerelay client run opencode'
