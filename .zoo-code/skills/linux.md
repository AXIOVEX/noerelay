# Skill: Linux

## System Information
- **OS**: Linux (various distributions)
- **Default shell**: bash (most), zsh (some)
- **Package managers**: apt (Debian/Ubuntu), dnf (RHEL/Fedora), pacman (Arch), zypper (SUSE)
- **File system**: ext4 (most), btrfs, xfs
- **Init system**: systemd (most), sysvinit (legacy)

## Distributions

### Debian/Ubuntu
```bash
# Package management
sudo apt update
sudo apt install package
sudo apt remove package
sudo apt autoremove
sudo apt upgrade
sudo apt full-upgrade

# Search
apt search package
apt show package

# Services
sudo systemctl start service
sudo systemctl stop service
sudo systemctl enable service
sudo systemctl status service
journalctl -u service -f

# Users
sudo useradd -m username
sudo usermod -aG sudo username
sudo deluser username
```

### RHEL/Fedora
```bash
# Package management
sudo dnf update
sudo dnf install package
sudo dnf remove package
sudo dnf autoremove

# Search
dnf search package
dnf info package

# Services (same as Debian)
sudo systemctl start service
journalctl -u service -f
```

### Arch
```bash
# Package management
sudo pacman -Syu  # Update
sudo pacman -S package  # Install
sudo pacman -Rns package  # Remove + deps
sudo pacman -Qs package  # Search

# AUR (community packages)
yay -S package  # With yay
paru -S package  # With paru
```

## systemd

### Service management
```bash
# Start/Stop/Restart
sudo systemctl start service
sudo systemctl stop service
sudo systemctl restart service

# Enable/Disable (boot)
sudo systemctl enable service
sudo systemctl disable service

# Status
sudo systemctl status service

# Logs
journalctl -u service -f  # Follow
journalctl -u service --since "1 hour ago"
journalctl -u service -n 50  # Last 50 lines

# List
systemctl list-units --type=service
systemctl list-units --state=failed
```

### Create a service
```ini
# /etc/systemd/system/myservice.service
[Unit]
Description=My Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/myservice
ExecStart=/opt/myservice/bin/server
Restart=on-failure
RestartSec=5
Environment=MY_VAR=value

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable myservice
sudo systemctl start myservice
```

### Timers (cron alternative)
```ini
# /etc/systemd/system/mytimer.timer
[Unit]
Description=Run mytask hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

## File System

### Key directories
```
/home/<username>/      # User home
/etc/                  # Configuration
/var/                  # Variable data (logs, spool, etc.)
/var/log/             # Logs
/var/lib/             # State data
/usr/                 # User commands and data
/usr/bin/             # Commands
/usr/local/           # Local installs
/opt/                 # Third-party software
/tmp/                 # Temporary files
/dev/                 # Device files
/proc/                # Process information
/sys/                 # Kernel information
/boot/                # Boot files
```

### File permissions
```bash
# Read
ls -la
stat file

# Change
chmod +x script.sh
chmod 755 script.sh  # rwxr-xr-x
chmod 644 file.txt   # rw-r--r--
chown user:group file
chgrp group file

# Special bits
chmod u+s binary     # SetUID
chmod g+s directory  # SetGID
chmod +t directory   # Sticky bit
```

### Find files
```bash
# By name
find / -name "filename"
find . -name "*.rs" -type f

# By content
grep -r "pattern" /path/

# By size
find . -size +100M

# By time
find . -mtime -7  # Modified in last 7 days
find . -newer reference_file

# Execute
find . -name "*.tmp" -delete
find . -name "*.log" -exec rm {} \;
```

## Networking

### Check network
```bash
# IP addresses
ip addr
ip a

# Routes
ip route

# DNS
cat /etc/resolv.conf
dig example.com
nslookup example.com
getent hosts example.com

# Ports
ss -tlnp  # Listening TCP
ss -ulnp  # Listening UDP
lsof -i :8080
netstat -tlnp

# Ping
ping example.com
ping -c 4 example.com

# Traceroute
traceroute example.com
tracepath example.com

# Curl
curl -s http://example.com
```

### Firewall (ufw - Ubuntu)
```bash
sudo ufw status
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 8080/tcp
sudo ufw deny 80
sudo ufw delete allow 80
```

### Firewall (firewalld - RHEL)
```bash
sudo firewall-cmd --state
sudo firewall-cmd --list-all
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```

## Process Management

### List processes
```bash
ps aux
ps aux | grep "process"
ps -ef
top
htop  # Install: sudo apt install htop
```

### Kill processes
```bash
kill PID
kill -9 PID
pkill "process"
pkill -9 "process"
killall "process"
```

### Resource usage
```bash
# CPU
top -p PID
pidstat -p PID 1

# Memory
ps -o pid,rss,cmd -p PID
cat /proc/PID/status | grep Vm

# I/O
iotop -p PID
pidstat -d -p PID 1
```

## Package Management (General)

### Check installed
```bash
# Debian
dpkg -l | grep package
apt list --installed | grep package

# RHEL
rpm -qa | grep package
dnf list installed | grep package

# Arch
pacman -Qs package
```

### File ownership
```bash
# Which package owns a file?
dpkg -S /path/to/file  # Debian
rpm -qf /path/to/file  # RHEL
pacman -Qo /path/to/file  # Arch
```

## Development Tools

### Install common tools
```bash
# Debian/Ubuntu
sudo apt install git curl wget build-essential gcc g++ make cmake
sudo apt install nodejs npm
sudo apt install python3 python3-pip python3-venv
sudo apt install jq ripgrep fd-find fzf tmux htop
sudo apt install docker.io docker-compose
sudo apt install postgresql postgresql-client
sudo apt install redis-server
sudo apt install nginx
sudo apt install openssl

# RHEL/Fedora
sudo dnf install git curl wget gcc gcc-c++ make cmake
sudo dnf install nodejs npm
sudo dnf install python3 python3-pip
sudo dnf install jq ripgrep findutils fzf tmux htop
sudo dnf install docker docker-compose
sudo dnf install postgresql-server postgresql
sudo dnf install redis
sudo dnf install nginx
sudo dnf install openssl
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
# Debian
sudo apt install golang
# Or from source:
wget https://go.dev/dl/go1.21.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
```

### Node.js
```bash
# Using nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install --lts
```

### Python
```bash
python3 --version
pip3 install package
python3 -m venv venv
source venv/bin/activate
```

## Docker

### Install
```bash
# Debian/Ubuntu
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker

# RHEL
sudo dnf install docker docker-compose
sudo usermod -aG docker $USER
```

### Usage
```bash
docker compose up -d
docker compose down
docker compose logs -f
docker compose build
docker ps
docker images
docker exec -it container bash
docker network ls
docker volume ls
```

## Logs

### System logs
```bash
# journalctl (systemd)
journalctl -f  # Follow
journalctl -u service
journalctl --since "2024-01-01"
journalctl -p err  # Errors only
journalctl -k  # Kernel

# Traditional
cat /var/log/syslog  # Debian
cat /var/log/messages  # RHEL
tail -f /var/log/syslog
```

## Common Gotchas

### 1. `sudo` and environment
```bash
# sudo may reset PATH
sudo env PATH="$PATH" command
# Or use full paths
```

### 2. SELinux (RHEL)
```bash
# Check status
getenforce

# Temporarily disable
sudo setenforce 0

# Permanent (NOT recommended)
sudo sed -i 's/SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config
sudo reboot

# Allow specific access
sudo semanage port -a -t http_port_t -p tcp 8080
```

### 3. AppArmor (Ubuntu)
```bash
# Check status
sudo aa-status

# Profile for app
sudo aa-complain /path/to/app
```

### 4. File system case sensitivity
```bash
# Linux is case-sensitive (unlike macOS default)
ls FILE.txt  # Will fail if file is file.txt
```

### 5. `/etc/hosts`
```bash
# Add local entries
echo "127.0.0.1 myapp.local" | sudo tee -a /etc/hosts
```

### 6. Time zones
```bash
# Check
timedatectl

# Set
sudo timedatectl set-timezone America/New_York
```

### 7. Swap
```bash
# Check
free -h
swapon --show

# Create swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
