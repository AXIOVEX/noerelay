# Skill: macOS

## System Information
- **OS**: macOS (Darwin kernel)
- **Default shell**: zsh (Catalina+), bash 3.2 (legacy)
- **Package manager**: Homebrew (`brew`)
- **File system**: APFS (case-insensitive by default)
- **Architecture**: Apple Silicon (arm64) or Intel (x86_64)

## Key Differences from Linux

| Feature | macOS | Linux |
|---------|-------|-------|
| Kernel | Darwin (BSD) | Linux |
| Init system | launchd | systemd |
| Package manager | Homebrew / MacPorts | apt / dnf / pacman |
| Default shell | zsh | bash / zsh |
| File system | APFS | ext4 / btrfs / xfs |
| Case sensitivity | Case-insensitive (default) | Case-sensitive |
| `/home` | NOT used (uses `/Users`) | Used |
| `/usr/local` | Homebrew (Intel) | Local installs |
| `/opt/homebrew` | Homebrew (Apple Silicon) | N/A |
| `sudo` | Available | Available |
| `systemctl` | NOT available | Available |
| `journalctl` | NOT available | Available |
| `htop` | `brew install htop` | Usually pre-installed |
| `tmux` | `brew install tmux` | Usually pre-installed |
| `ripgrep` | `brew install ripgrep` | `apt install ripgrep` |
| `fd` | `brew install fd` | `apt install fd-find` |
| `fzf` | `brew install fzf` | `apt install fzf` |
| `jq` | `brew install jq` | `apt install jq` |
| `gh` | `brew install gh` | `apt install gh` |
| `docker` | Docker Desktop (app) | docker CLI |
| `git` | Pre-installed (Xcode CLT) | `apt install git` |
| `node` | `brew install node` | `apt install nodejs` |
| `python` | `brew install python` | Pre-installed |
| `rust` | `curl https://sh.rustup.rs \| sh` | Same |
| `go` | `brew install go` | `apt install golang` |

## Homebrew

### Installation
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Usage
```bash
# Search
brew search package

# Install
brew install package
brew install --cask package  # GUI apps

# Update
brew update
brew upgrade
brew upgrade --greedy  # All packages

# List
brew list
brew list --greedy

# Info
brew info package

# Uninstall
brew uninstall package
brew uninstall --cask package

# Cleanup
brew cleanup
brew autoremove
```

### Common packages
```bash
brew install git
brew install node
brew install python
brew install rust
brew install go
brew install docker
brew install kubectl
brew install helm
brew install gh
brew install jq
brew install ripgrep
brew install fd
brew install fzf
brew install tmux
brew install htop
brew install wget
brew install curl  # Pre-installed
brew install openssl
brew install sqlite
brew install postgresql
brew install redis
```

## System Services (launchd)

### List services
```bash
# User services
launchctl list

# System services
sudo launchctl list

# Specific service
launchctl print gui/$(id -u)/com.example.service
```

### Manage services
```bash
# Load (start)
launchctl load ~/Library/LaunchAgents/com.example.service.plist

# Unload (stop)
launchctl unload ~/Library/LaunchAgents/com.example.service.plist

# Start/Stop
launchctl start com.example.service
launchctl stop com.example.service

# Kickstart (restart)
launchctl kickstart -k gui/$(id -u)/com.example.service
```

### Create a LaunchAgent
```xml
<!-- ~/Library/LaunchAgents/com.example.service.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.example.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/my-service</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/my-service.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/my-service-error.log</string>
</dict>
</plist>
```

## File System

### Key directories
```
/Users/<username>/          # Home directory
/Users/<username>/Desktop/  # Desktop
/Users/<username>/Documents/ # Documents
/Users/<username>/Downloads/ # Downloads
/Users/<username>/Library/  # User library (app data, caches)
/usr/local/                 # Local installs (Intel Homebrew)
/opt/homebrew/              # Homebrew (Apple Silicon)
/private/var/               # System data (symlinked from /var)
/tmp/                       # Temporary files
/Volumes/                   # Mounted volumes
```

### Hidden files
```bash
# Show hidden files in Finder:
# Cmd+Shift+. (period)

# In terminal:
ls -la
```

### Case insensitivity
```bash
# Default APFS is case-insensitive:
ls FILE.txt  # Works even if file is file.txt
# This can cause issues with git repos!
```

## Networking

### Check network
```bash
# IP addresses
ifconfig
ipconfig getifaddr en0  # Primary IP

# DNS
scutil --dns
dig example.com
nslookup example.com

# Ports
lsof -i :8080
netstat -an | grep 8080

# Ping
ping example.com

# Traceroute
traceroute example.com
```

### Firewall
```bash
# Check status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Enable
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Allow app
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/MyApp.app
```

## Development Tools

### Xcode Command Line Tools
```bash
# Install (required for git, clang, etc.)
xcode-select --install

# Check
xcode-select -p
```

### Docker
```bash
# Docker Desktop (GUI app)
# Or use colima (lighter):
brew install colima docker
colima start
docker context use colima
```

### Node.js
```bash
brew install node
# Or with nvm:
brew install nvm
mkdir ~/.nvm
source ~/.nvm/nvm.sh
nvm install --lts
```

### Python
```bash
brew install python
python3 --version
pip3 install package
# Or with pyenv:
brew install pyenv
```

### Rust
```bash
curl https://sh.rustup.rs -sSf | sh
source $HOME/.cargo/env
rustc --version
cargo --version
```

### Go
```bash
brew install go
go version
```

## Process Management

### List processes
```bash
ps aux
ps aux | grep "process"
top  # Built-in
htop  # brew install htop
```

### Kill processes
```bash
kill PID
kill -9 PID
pkill "process"
pkill -9 "process"
```

### Background processes
```bash
command &
jobs
fg %1
bg %1
disown
```

## System Information

### Hardware
```bash
# CPU
sysctl -n machdep.cpu.brand_string
system_profiler SPHardwareDataType

# Memory
sysctl hw.memsize  # Bytes
system_profiler SPHardwareDataType | grep "Memory"

# Disk
df -h
diskutil list
system_profiler SPDiskDataType

# GPU
system_profiler SPDisplaysDataType
```

### Software
```bash
# macOS version
sw_vers

# Kernel
uname -a

# Architecture
uname -m  # arm64 or x86_64
```

## Common Gotchas

### 1. Gatekeeper
```bash
# Allow apps from anywhere:
# System Settings > Privacy & Security > Allow apps from anywhere
# Or:
sudo spctl --master-disable
```

### 2. SIP (System Integrity Protection)
```bash
# Check status
csrutil status

# Disable (requires Recovery Mode)
csrutil disable
```

### 3. PATH issues
```bash
# Apple Silicon Homebrew is in /opt/homebrew
# Intel Homebrew is in /usr/local
echo $PATH
# Add to ~/.zshrc:
export PATH="/opt/homebrew/bin:$PATH"  # Apple Silicon
# Or:
eval "$(brew shellenv)"
```

### 4. `sudo` and PATH
```bash
# sudo resets PATH
sudo env PATH="$PATH" command
# Or use full path:
sudo /usr/local/bin/command
```

### 5. File permissions
```bash
# macOS is more restrictive
chmod +x script.sh
chmod 755 script.sh  # rwxr-xr-x
```

### 6. Time Machine
```bash
# Check status
tmutil status
tmutil destinationinfo

# Exclude paths
tmutil addexclusion /path/to/exclude
```
