# Skill: PowerShell 7+ (Cross-Platform)

## Key Differences from PowerShell 5.1

| Feature | PowerShell 5.1 | PowerShell 7+ |
|---------|---------------|---------------|
| Engine | .NET Framework 4.x | .NET 6/8 |
| Default encoding | System default | **UTF-8** |
| `&&` / `||` | NOT available | **Available** |
| `curl` alias | `Invoke-WebRequest` | **`curl.exe`** (real curl) |
| `tar` | NOT available | **Available** |
| TLS 1.2 | Must set manually | **Default** |
| `ForEach-Object` method | NOT available | **Available** (`.ForEach{}`) |
| `Where-Object` shorthand | NOT available | **Available** (`Where-Object Prop -eq 'x'`) |
| Ternary / null-coalescing | NOT available | **Available** (`? :`, `??`) |
| Cross-platform | Windows only | **Win/Mac/Linux** |
| `Get-ChildItem` | Windows paths | **Cross-platform paths** |
| `Join-Path` | Windows-style | **Cross-platform** |
| `Split-Path` | Windows-style | **Cross-platform** |
| `Get-PSDrive` | Shows Windows drives | **Shows all providers** |
| `Import-Module` | Windows module paths | **Cross-platform** |
| `Get-Command` | Windows cmdlets | **Cross-platform + external** |
| `#requires` | Version 3.0 | **Version 7.x** |
| `param()` | Same | Same |
| `function` | Same | Same |
| `class` | Available (PS 5+) | Same |
| `enum` | Available (PS 5+) | Same |
| `try/catch/finally` | Same | Same |
| `throw` | Same | Same |
| `$?` | Same | Same |
| `$LASTEXITCODE` | Same | Same |
| `$HOME` | NOT set (use `$env:USERPROFILE`) | **Set on all platforms** |
| `$PWD` | Same | Same |
| `$IsWindows` / `$IsLinux` / `$IsMacOS` | NOT available | **Available** |

## PowerShell 7+ New Features

### 1. `&&` and `||` operators
```powershell
# Chain commands (only run next if previous succeeded)
git status && git add . && git commit -m "fix"

# Logical OR
test1 || test2

# In conditionals
if ($condition1 && $condition2) { ... }
if ($condition1 || $condition2) { ... }
```

### 2. Ternary and null-coalescing operators
```powershell
# Ternary
$result = $condition ? "yes" : "no"

# Null-coalescing
$value = $maybeNull ?? "default"

# Chained null-coalescing
$value = $a ?? $b ?? "fallback"
```

### 3. `Where-Object` shorthand
```powershell
# Old (still works):
Get-Process | Where-Object { $_.CPU -gt 100 }

# New shorthand:
Get-Process | Where-Object CPU -gt 100
Get-Process | Where-Object Name -like "node*"
```

### 4. `.ForEach{}` and `.Where{}` methods
```powershell
# Method syntax on collections
$items.ForEach({ Write-Host $_ })
$items.Where({ $_.Status -eq "active" })

# Equivalent pipeline:
$items | ForEach-Object { Write-Host $_ }
$items | Where-Object { $_.Status -eq "active" }
```

### 5. `curl` is real curl
```powershell
# In PS 7+, "curl" maps to curl.exe
curl -s http://example.com
curl -X POST -H "Content-Type: application/json" -d '{"key":"value"}' http://api.example.com

# Invoke-RestMethod still available for PowerShell-native HTTP
Invoke-RestMethod -Uri "http://api.example.com" -Method Get
```

### 6. `tar` is available
```powershell
tar -czf archive.tar.gz ./folder
tar -xzf archive.tar.gz -C /destination
```

### 7. Platform detection
```powershell
$IsWindows  # $true on Windows
$IsLinux    # $true on Linux
$IsMacOS    # $true on macOS

# Cross-platform script:
if ($IsWindows) {
    $homeDir = $env:USERPROFILE
} else {
    $homeDir = $HOME
}
```

### 8. UTF-8 by default
```powershell
# No need to specify -Encoding UTF8 (it's the default)
Set-Content "file.txt" -Value $content
Get-Content "file.txt"

# Still can specify other encodings:
Get-Content "file.txt" -Encoding ASCII
```

### 9. Improved `ConvertFrom-Json`
```powershell
# -AsHashtable for hashtable output (instead of PSCustomObject)
$json = Get-Content "config.json" -Raw | ConvertFrom-Json -AsHashtable

# -Depth still available
$json = Get-Content "config.json" -Raw | ConvertFrom-Json -Depth 20
```

### 10. `Get-Content` improvements
```powershell
# -Wait for live tail (like tail -f)
Get-Content "log.txt" -Wait

# -Tail for last N lines
Get-Content "log.txt" -Tail 50

# -ReadCount for chunked reading
Get-Content "large.txt" -ReadCount 1000
```

## Cross-Platform Patterns

### File paths
```powershell
# Use Join-Path for cross-platform paths
$path = Join-Path $HOME "projects" "myapp"

# Use forward slashes (works on all platforms in PS 7+)
$path = "/home/user/projects"  # Linux/Mac
$path = "C:\Users\user\projects"  # Windows

# $PWD works everywhere
Get-ChildItem $PWD
```

### Environment variables
```powershell
# $HOME is set on all platforms in PS 7+
$homeDir = $HOME

# Platform-specific:
if ($IsWindows) {
    $tempDir = $env:TEMP
} else {
    $tempDir = $env:TMPDIR
}
```

### Process management
```powershell
# Cross-platform:
Get-Process | Where-Object Name -like "node*"
Stop-Process -Name "notepad" -Force  # Windows
Stop-Process -Name "code" -Force     # Cross-platform (VS Code)
```

### HTTP
```powershell
# Both work in PS 7+:
curl -s http://api.example.com
Invoke-RestMethod -Uri "http://api.example.com"
```

### JSON
```powershell
# Parse
$data = Get-Content "config.json" -Raw | ConvertFrom-Json

# Serialize
$object | ConvertTo-Json -Depth 10 | Set-Content "output.json"
```

## Common Patterns

### Run external commands
```powershell
# Capture output
$output = & git log --oneline -5 2>&1

# Check exit code
& npm install
if ($LASTEXITCODE -ne 0) { Write-Error "npm install failed" }

# With && chaining (PS 7+)
git add . && git commit -m "update" && git push
```

### Working with files
```powershell
# Read
$content = Get-Content "file.txt" -Raw
$lines = Get-Content "file.txt"

# Write
Set-Content "file.txt" -Value "content"
Add-Content "file.txt" -Value "more"

# Copy/Move/Delete
Copy-Item "src" "dst" -Force -Recurse
Move-Item "src" "dst" -Force
Remove-Item "file" -Force
Remove-Item "folder" -Recurse -Force
```

### Error handling
```powershell
try {
    $result = Invoke-RestMethod -Uri "http://api.example.com"
} catch [System.Net.Http.HttpRequestException] {
    Write-Error "HTTP error: $_"
} catch {
    Write-Error "Unexpected: $_"
} finally {
    Write-Host "Done"
}
```

### Functions
```powershell
function Get-ProjectStatus {
    param(
        [string]$Path = ".",
        [switch]$Verbose
    )
    
    Push-Location $Path
    try {
        $branch = & git branch --show-current 2>&1
        $status = & git status --short 2>&1
        Write-Host "Branch: $branch"
        if ($status) {
            Write-Host "Changes:"
            $status | ForEach-Object { Write-Host "  $_" }
        } else {
            Write-Host "Clean"
        }
    } finally {
        Pop-Location
    }
}
```

## Detection
```powershell
$PSVersionTable.PSVersion
# 7.x+ = PowerShell Core / PowerShell 7+
```
