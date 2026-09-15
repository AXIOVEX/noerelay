' LLM Watchdog launcher (windowless).
'
' The scheduled task "LLM Watchdog" runs this via:  wscript.exe //B <this file>
'   - //B (batch mode) keeps the wscript process itself windowless.
'   - WindowStyle 0 (below) starts the PowerShell watchdog with no console,
'     so the once-per-minute tick never flashes a window on the desktop.
'
' It resolves llama-watchdog.ps1 relative to this file, so the task action
' does not need to embed the repo path twice.

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

ps1 = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "llama-watchdog.ps1")
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & ps1 & """", 0, False
