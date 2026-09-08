# Skill: Windows

## System Information
- **OS**: Windows 10/11
- **Default shell**: PowerShell 5.1 (Windows PowerShell)
- **Alternative shell**: PowerShell 7+ (cross-platform), CMD, WSL
- **File system**: NTFS (case-insensitive)
- **Package managers**: winget, Chocolatey, Scoop

## Package Managers

### winget (built-in Windows 11)
```powershell
# Search
winget search package

# Install
winget install package
winget install --id Publisher.Package

# Update
winget update
winget upgrade package

# List
winget list
winget list --upgrade-available

# Uninstall
winget uninstall package
```

### Chocolatey
```powershell
# Install Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force
[iwr] "https://community.chocolatey.org/install.ps1" | iex

# Usage
choco install package -y
choco upgrade package -y
choco uninstall package
choco list
choco search package
```

### Scoop
```powershell
# Install Scoop
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# Usage
scoop install package
scoop update *
scoop uninstall package
scoop list
scoop search package
```

## WSL (Windows Subsystem for Linux)

### Setup
```powershell
# Enable WSL (Admin PowerShell)
wsl --install
wsl --install -d Ubuntu-22.04

# List distributions
wsl --list --verbose

# Set default
wsl --set-default Ubuntu-22.04

# Run command in WSL
wsl -d Ubuntu-22.04 -- bash -c "command"
```

### File access
```powershell
# Access Windows files from WSL
\\wsl$\Ubuntu-22.04\home\user\
\\wsl.localhost\Ubuntu-22.04\home\user\

# Access WSL files from Windows
\\wsl$\Ubuntu-22.04\
# Or in File Explorer: \\wsl$\
```

### Performance note
```
# Running Linux apps on Windows filesystem is SLOW
# Run Windows apps on WSL filesystem is SLOW
# Best: Keep Linux projects in WSL filesystem, Windows projects in Windows filesystem
```

## PowerShell (Windows)

### PowerShell 5.1 (default)
```powershell
# See powershell5.md skill for details
# Key: No &&, curl = Invoke-WebRequest, UTF-8 not default
```

### PowerShell 7+ (if installed)
```powershell
# See powershell7.md skill for details
# Key: && available, curl = real curl, UTF-8 default
```

### CMD (legacy)
```cmd
:: Basic commands
dir
type file.txt
copy src dst
move src dst
del file.txt
rd /s /q dir\
mkdir newdir
cd path
echo text
set VAR=value
echo %VAR%

:: Process
tasklist
taskkill /PID 1234 /F
taskkill /IM process.exe /F

:: Network
ipconfig
ping example.com
tracert example.com
netstat -an
nslookup example.com

:: Services
sc query
sc start service
sc stop service
net start service
net stop service

:: Registry
reg query HKLM\SOFTWARE
reg add HKLM\SOFTWARE\MyApp /v Key /t REG_SZ /d Value
reg delete HKLM\SOFTWARE\MyApp /v Key /f
```

## File System

### Key directories
```
C:\Users\<username>\          # User home
C:\Users\<username>\Desktop\  # Desktop
C:\Users\<username>\Documents\ # Documents
C:\Users\<username>\Downloads\ # Downloads
C:\Users\<username>\AppData\  # App data (Roaming, Local, LocalLow)
C:\Program Files\             # System apps (64-bit)
C:\Program Files (x86)\       # 32-bit apps
C:\Windows\                   # System files
C:\Windows\System32\          # System binaries
C:\temp\                      # Temp (if created)
%TEMP%\                       # User temp (C:\Users\<username>\AppData\Local\Temp)
```

### File permissions (NTFS)
```powershell
# View permissions
icacls file.txt
Get-Acl file.txt

# Change permissions
icacls file.txt /grant username:R
icacls file.txt /grant username:F  # Full control
icacls file.txt /remove username

# Inheritance
icacls file.txt /inheritance:r  # Remove inherited permissions
```

### Long paths
```powershell
# Windows has 260 char path limit (can be extended)
# Enable long paths (Admin):
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or use \\?\ prefix
Get-Content "\\?\C:\very\long\path\to\file.txt"
```

### Case insensitivity
```powershell
# NTFS is case-insensitive by default
Get-Content FILE.TXT  # Works even if file is file.txt
# This can cause issues with git repos!
```

## Networking

### Check network
```powershell
# IP addresses
ipconfig
ipconfig /all

# DNS
nslookup example.com
Resolve-DnsName example.com

# Ports
Get-NetTCPConnection -LocalPort 8080
netstat -an | findstr 8080

# Ping
ping example.com
Test-Connection example.com

# Traceroute
tracert example.com

# Firewall
Get-NetFirewallRule
Get-NetFirewallRule -DisplayName "My Rule"
New-NetFirewallRule -DisplayName "Allow 8080" -Direction Inbound -LocalPort 8080 -Action Allow
```

### Proxy
```powershell
# Check
Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"

# Set (system)
Set-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" `
    -Name "ProxyEnable" -Value 1
Set-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" `
    -Name "ProxyServer" -Value "proxy:8080"

# Environment variables
$env:HTTP_PROXY = "http://proxy:8080"
$env:HTTPS_PROXY = "http://proxy:8080"
$env:NO_PROXY = "localhost,127.0.0.1"
```

## Process Management

### List processes
```powershell
Get-Process
Get-Process | Where-Object { $_.CPU -gt 100 }
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10

# Task Manager equivalent
Get-Process | Format-Table Name, CPU, WorkingSet, MainWindowTitle
```

### Kill processes
```powershell
Stop-Process -Name "notepad" -Force
Stop-Process -Id 12345 -Force
Get-Process -Name "chrome" | Stop-Process -Force
```

### Background processes
```powershell
# Start hidden
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "long_task.bat" -WindowStyle Hidden

# Start and get process object
$proc = Start-Process -FilePath "task.exe" -PassThru
$proc.WaitForExit()
$proc.ExitCode
```

## Services

### Manage services
```powershell
# List
Get-Service
Get-Service -Name "myService"
Get-Service | Where-Object { $_.Status -eq "Running" }

# Start/Stop
Start-Service -Name "myService"
Stop-Service -Name "myService"
Restart-Service -Name "myService"

# Set startup type
Set-Service -Name "myService" -StartupType Automatic
Set-Service -Name "myService" -StartupType Manual
Set-Service -Name "myService" -StartupType Disabled
```

### Create a service
```powershell
# Using sc.exe (Admin)
sc.exe create "MyService" binPath= "C:\path\to\service.exe" start= auto

# Or using New-Service (PowerShell)
New-Service -Name "MyService" -DisplayName "My Service" `
    -BinaryPathName "C:\path\to\service.exe" -StartupType Automatic
```

## Environment Variables

### User variables
```powershell
# Read
$env:PATH
$env:USERPROFILE
$env:TEMP

# Set (current session)
$env:MY_VAR = "value"

# Set (permanent - user)
[Environment]::SetEnvironmentVariable("MY_VAR", "value", "User")

# Set (permanent - system, Admin)
[Environment]::SetEnvironmentVariable("MY_VAR", "value", "Machine")

# Remove
Remove-Item env:MY_VAR
[Environment]::SetEnvironmentVariable("MY_VAR", $null, "User")
```

### PATH management
```powershell
# Add to PATH (current session)
$env:PATH = "$env:PATH;C:\new\path"

# Add to PATH (permanent - user)
[Environment]::SetEnvironmentVariable("PATH", 
    [Environment]::GetEnvironmentVariable("PATH", "User") + ";C:\new\path", "User")

# View PATH
$env:PATH -split ";"
```

## Development Tools

### Install common tools
```powershell
# Using winget
winget install Git.Git
winget install OpenJS.NodeJS
winget install Python.Python.3.12
winget install Rustlang.Rustup
winget install Golang.Go
winget install Docker.DockerDesktop
winget install PostgreSQL.PostgreSQL.16
winget install Redis.Redis
winget install PostgreSQL.PostgreSQL.16
winget install 7zip.7zip
winget install Git.Git
winget install GitHub.cli
winget install Microsoft.PowerShell.7
```

### Rust
```powershell
winget install Rustlang.Rustup
# Or:
winget install Rustlang.Rust
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
```

### Go
```powershell
winget install Golang.Go
$env:GOPATH = "$env:USERPROFILE\go"
$env:PATH = "$env:GOPATH\bin;$env:PATH"
```

### Node.js
```powershell
winget install OpenJS.NodeJS
# Or with nvm-windows:
winget install CoreyButler.NVMforWindows
nvm install latest
nvm use latest
```

### Docker
```powershell
winget install Docker.DockerDesktop
# Requires WSL 2 or Hyper-V
# After install, restart and open Docker Desktop
```

## Scheduled Tasks

### Create a task
```powershell
# Simple
$action = New-ScheduledTaskAction -Execute "C:\path\to\script.ps1"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "MyTask" -Action $action -Trigger $trigger

# Daily at 9am
$trigger = New-ScheduledTaskTrigger -Daily -At "9:00AM"
Register-ScheduledTask -TaskName "MyDailyTask" -Action $action -Trigger $trigger
```

### Manage tasks
```powershell
Get-ScheduledTask
Get-ScheduledTask -TaskName "MyTask"
Start-ScheduledTask -TaskName "MyTask"
Stop-ScheduledTask -TaskName "MyTask"
Unregister-ScheduledTask -TaskName "MyTask" -Confirm:$false
```

## Common Gotchas

### 1. Execution Policy
```powershell
# Check current policy
Get-ExecutionPolicy

# Allow scripts (current user)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Allow all (NOT recommended)
Set-ExecutionPolicy Unrestricted -Scope CurrentUser
```

### 2. PATH not updating
```powershell
# After adding to PATH, open new terminal
# Or refresh current session:
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + 
            [Environment]::GetEnvironmentVariable("PATH", "User")
```

### 3. Line endings
```powershell
# Windows uses CRLF (\r\n), Unix uses LF (\n)
# Git:
git config --global core.autocrlf true  # Windows
# Or in .gitattributes:
# *.sh text eol=lf
```

### 4. File locking
```powershell
# Windows locks files while they're open
# Can't delete/replace a file that's in use
# Solution: Close the process first
Get-Process | Where-Object { $_.Modules.FileName -like "*file*" } | Stop-Process
```

### 5. Admin privileges
```powershell
# Check if running as admin
([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Run as admin (from non-admin)
Start-Process powershell -Verb RunAs -ArgumentList "-Command", "your command"
```

### 6. Reserved names
```powershell
# These names can't be used for files:
# CON, PRN, AUX, NUL, COM1-COM9, LPT1-LPT9
# Workaround: Append a dot
New-Item "NUL."  # Creates a file named "NUL."
```

### 7. Long paths in PowerShell
```powershell
# Use \\?\ prefix for paths > 260 chars
Get-Content "\\?\C:\very\long\path\to\file.txt"
```
