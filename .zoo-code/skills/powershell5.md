# Skill: PowerShell 5.1 (Windows PowerShell)

## Critical Differences from PowerShell 7

| Feature | PowerShell 5.1 | PowerShell 7+ |
|---------|---------------|---------------|
| Engine | .NET Framework 4.x | .NET 6/8 (cross-platform) |
| Default encoding | System default (often Windows-1252) | UTF-8 |
| `&&` / `;` chaining | `;` only (no `&&`) | Both `&&` and `;` |
| `Get-Command` | Windows-only cmdlets | Cross-platform |
| `ConvertFrom-Json` | Returns PSCustomObject (no arrays for single items) | Same, but better |
| `Invoke-RestMethod` | Uses .NET Framework HttpClient | Uses .NET HttpClient |
| TLS 1.2 | Must set `[Net.ServicePointManager]::SecurityProtocol` | Default |
| `foreach` statement | `foreach ($x in $y) {}` | Same |
| `foreach` operator | `$y.ForEach({})` NOT available | `$y.ForEach({})` available |
| `Where-Object` | `Where-Object { $_.Prop -eq 'x' }` | Same, plus `Where-Object Prop -eq 'x'` |
| `Join-Path` | Works | Works |
| `Test-Path` | Works | Works |
| `Select-String` | Works | Works |
| `ConvertTo-Json` | `-Depth` parameter required for nested | Same |
| `Get-Content` | `-Raw` available | Same |
| `Set-Content` | Appends with `-Append` | Same |
| `Out-File` | `-Encoding` parameter | Same, default UTF-8 |
| `Write-Host` | Works | Works |
| `Read-Host` | Works | Works |
| `Start-Process` | Works | Works |
| `Get-Process` | Works | Works |
| `Stop-Process` | Works | Works |
| `Get-Service` | Works | Works |
| `Get-ChildItem` | Works | Works |
| `New-Item` | Works | Works |
| `Remove-Item` | Works | Works |
| `Copy-Item` | Works | Works |
| `Move-Item` | Works | Works |
| `Rename-Item` | Works | Works |
| `Compress-Archive` | Available (PS 5.0+) | Same |
| `Expand-Archive` | Available (PS 5.0+) | Same |
| `Invoke-WebRequest` | Uses IE engine (Win) | Uses .NET HttpClient |
| `curl` alias | Maps to `Invoke-WebRequest` (NOT real curl) | Maps to `curl.exe` (real curl) |
| `tar` | NOT available natively | Available (maps to bsdtar) |
| `zip` | NOT available | NOT available (use Compress-Archive) |

## PowerShell 5.1 Gotchas

### 1. No `&&` operator
```powershell
# WRONG (PS 5.1):
git status && git push

# CORRECT (PS 5.1):
git status; if ($LASTEXITCODE -eq 0) { git push }
# Or simply:
git status; git push
```

### 2. `curl` is NOT curl
```powershell
# In PS 5.1, "curl" is an alias for Invoke-WebRequest
# This will FAIL or behave unexpectedly:
curl -s http://example.com

# CORRECT:
Invoke-RestMethod -Uri "http://example.com" -Method Get
# Or use the real curl:
curl.exe -s http://example.com
```

### 3. Encoding issues
```powershell
# PS 5.1 defaults to system encoding (Windows-1252 on English Windows)
# Always specify UTF-8:
Set-Content -Path "file.txt" -Value $content -Encoding UTF8
Get-Content -Path "file.txt" -Encoding UTF8
Out-File -FilePath "file.txt" -InputObject $content -Encoding UTF8
```

### 4. TLS 1.2 must be set manually
```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
```

### 5. `ConvertTo-Json` depth
```powershell
# PS 5.1 truncates nested objects without -Depth
$object | ConvertTo-Json -Depth 10
```

### 6. String interpolation
```powershell
# Use double quotes for interpolation
"Hello $name"
# Escape literal dollar signs
"Cost: \`$5"
# Single quotes = no interpolation
'Hello $name'  # literal
```

### 7. Pipeline and objects
```powershell
# Everything is objects, not text
Get-Process | Where-Object { $_.CPU -gt 100 } | Sort-Object CPU -Descending | Select-Object Name, CPU

# Access properties
(Get-Process -Name "notepad").MainWindowTitle

# Method calls on objects
"hello world".ToUpper()
"hello".Replace("h", "H")
```

### 8. Error handling
```powershell
# $LASTEXITCODE for external commands
& git status
if ($LASTEXITCODE -ne 0) { Write-Error "git failed" }

# try/catch for PowerShell errors
try {
    Invoke-RestMethod -Uri "http://api.example.com"
} catch {
    Write-Error "Request failed: $_"
}

# -ErrorAction
Get-Content "missing.txt" -ErrorAction SilentlyContinue
```

### 9. Working with files
```powershell
# Read all lines
$lines = Get-Content "file.txt"

# Read raw
$raw = Get-Content "file.txt" -Raw

# Write
Set-Content "file.txt" -Value "line1`nline2"

# Append
Add-Content "file.txt" -Value "new line"

# Copy
Copy-Item "src.txt" "dst.txt" -Force

# Move
Move-Item "src.txt" "dst.txt" -Force

# Delete
Remove-Item "file.txt" -Force
Remove-Item "folder\" -Recurse -Force

# Create directory
New-Item -ItemType Directory -Path "new/folder" -Force
```

### 10. Environment variables
```powershell
# Read
$env:PATH
$env:HOME  # NOT set on Windows; use $env:USERPROFILE

# Write
$env:MY_VAR = "value"

# Remove
Remove-Item env:MY_VAR
```

### 11. Process management
```powershell
# Start background process
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "long_task.bat" -WindowStyle Hidden

# Get running processes
Get-Process | Where-Object { $_.ProcessName -like "node*" }

# Stop process
Stop-Process -Name "notepad" -Force
Stop-Process -Id 12345 -Force
```

### 12. JSON handling
```powershell
# Parse
$json = Get-Content "config.json" -Raw | ConvertFrom-Json
$json.property
$json.array[0]

# Serialize
$object | ConvertTo-Json -Depth 10 | Set-Content "output.json"
```

### 13. HTTP requests
```powershell
# GET
$response = Invoke-RestMethod -Uri "http://api.example.com/data" -Method Get

# POST with JSON body
$body = @{ name = "test" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://api.example.com/data" -Method Post -Body $body -ContentType "application/json"

# With headers
$headers = @{ "Authorization" = "Bearer $token" }
$response = Invoke-RestMethod -Uri "http://api.example.com/data" -Headers $headers

# Get full response (including headers)
$fullResponse = Invoke-WebRequest -Uri "http://api.example.com/data"
$fullResponse.StatusCode
$fullResponse.Headers
$fullResponse.Content
```

### 14. Scheduling / waiting
```powershell
# Sleep
Start-Sleep -Seconds 5
Start-Sleep -Milliseconds 500

# Wait for process
$proc = Start-Process -FilePath "task.exe" -PassThru
$proc.WaitForExit()
$proc.ExitCode
```

### 15. Common patterns
```powershell
# Run command and capture output
$output = & git log --oneline -5 2>&1
$output | ForEach-Object { Write-Host $_ }

# Conditional execution
if (Test-Path "file.txt") {
    Write-Host "Exists"
} else {
    Write-Host "Missing"
}

# Loop
foreach ($file in Get-ChildItem "*.rs") {
    Write-Host $file.Name
}

# 1..10 | ForEach-Object { Write-Host $_ }
```

## Detection
```powershell
# Check PS version
$PSVersionTable.PSVersion
# 5.1.x = Windows PowerShell
# 7.x+ = PowerShell Core
```
