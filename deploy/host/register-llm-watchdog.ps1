#Requires -Version 5.1
<#
.SYNOPSIS
    Registers the "LLM Watchdog" scheduled task (runs every 1 minute).

.DESCRIPTION
    The watchdog keeps the session llama-server alive. It is idempotent
    (-Force), so re-running this is safe.
#>
$ErrorActionPreference = "Stop"

$wd = Join-Path $PSScriptRoot "llama-watchdog.ps1"
if (-not (Test-Path $wd)) { throw "watchdog script not found: $wd" }

$launcher = Join-Path $PSScriptRoot "llama-watchdog-launch.vbs"
if (-not (Test-Path $launcher)) { throw "watchdog launcher not found: $launcher" }

# Launch through wscript.exe //B + a VBS hidden-window runner so the
# once-per-minute tick never flashes a console window on the desktop.
$action    = New-ScheduledTaskAction -Execute "wscript.exe" `
    -Argument ('//B "{0}"' -f $launcher)
$trigger   = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0)

Register-ScheduledTask -TaskName "LLM Watchdog" -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings `
    -Description "Keeps the session llama-server (127.0.0.1:8081) alive; respects C:\LLM\MAINTENANCE" `
    -Force | Out-Null

Write-Host "LLM Watchdog registered."
Get-ScheduledTask -TaskName "LLM Watchdog" | Select-Object TaskName, State | Format-Table
