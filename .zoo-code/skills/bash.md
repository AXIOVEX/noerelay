# Skill: Bash (macOS / Linux)

## Key Differences from PowerShell

| Feature | Bash | PowerShell |
|---------|------|------------|
| Variable prefix | `$var` | `$var` |
| Command substitution | `$(cmd)` or `` `cmd` `` | `$(cmd)` or `& cmd` |
| Exit code | `$?` | `$LASTEXITCODE` |
| Chaining | `&&`, `||`, `;` | `&&`, `||`, `;` (PS7) / `;` (PS5) |
| Pipes | `cmd1 \| cmd2` | `cmd1 \| cmd2` |
| Here-docs | `<<EOF` | `@'...'@` |
| Arrays | `arr=(a b c)` | `@("a","b","c")` |
| Conditionals | `if [ ... ]; then` | `if (...) { }` |
| Loops | `for x in ...; do` | `foreach ($x in ...) { }` |
| Functions | `func() { }` | `function func { }` |
| Comments | `#` | `#` |
| String interpolation | `"hello $name"` | `"hello $name"` |
| Test | `[ -f file ]` | `Test-Path file` |
| Grep | `grep` | `Select-String` |
| Cat | `cat` | `Get-Content` |
| LS | `ls` | `Get-ChildItem` |
| RM | `rm` | `Remove-Item` |
| CP | `cp` | `Copy-Item` |
| MV | `mv` | `Move-Item` |
| MKDIR | `mkdir -p` | `New-Item -ItemType Directory` |
| Echo | `echo` | `Write-Host` / `Write-Output` |
| Which | `which` / `command -v` | `Get-Command` |
| Env | `env` / `export` | `$env:` / `Set-Item env:` |
| Pwd | `pwd` | `Get-Location` / `$PWD` |
| CD | `cd` | `Set-Location` / `cd` |
| Kill | `kill PID` | `Stop-Process -Id PID` |
| PS | `ps aux` | `Get-Process` |
| Find | `find . -name "*.rs"` | `Get-ChildItem -Recurse -Filter "*.rs"` |
| AWK | `awk` | `ForEach-Object` / `Select-Object` |
| SED | `sed` | `-replace` / `Get-Content` + `Set-Content` |
| TAIL | `tail -f` | `Get-Content -Wait` |
| HEAD | `head -n` | `Get-Content -TotalCount` |
| WGET | `wget` | `Invoke-WebRequest` / `curl` |
| CURL | `curl` | `curl` (PS7) / `Invoke-RestMethod` |
| TAR | `tar` | `tar` (PS7) / `Compress-Archive` |
| ZIP | `zip` | `Compress-Archive` |
| UNZIP | `unzip` | `Expand-Archive` |
| DIFF | `diff` | `Compare-Object` |
| SORT | `sort` | `Sort-Object` |
| UNIQUE | `uniq` | `Select-Object -Unique` |
| WC | `wc -l` | `(Get-Content file).Count` |
| DATE | `date` | `Get-Date` |
| SLEEP | `sleep 5` | `Start-Sleep -Seconds 5` |
| MKNOD | `mknod` | N/A |
| CHMOD | `chmod +x` | `icacls` (Windows) / N/A |
| CHOWN | `chown` | `icacls` (Windows) / N/A |
| DF | `df -h` | `Get-PSDrive` |
| DU | `du -sh` | `Get-ChildItem -Recurse \| Measure-Object` |
| FREE | `free -h` | N/A (use `Get-Counter`) |
| TOP | `top` / `htop` | `Get-Process \| Sort-Object CPU` |
| NETSTAT | `netstat` | `Get-NetTCPConnection` |
| IFCONFIG | `ifconfig` / `ip` | `Get-NetIPAddress` |
| PING | `ping` | `Test-Connection` |
| NSLOOKUP | `nslookup` / `dig` | `Resolve-DnsName` |
| SSH | `ssh` | `ssh` |
| SCP | `scp` | `scp` |
| GIT | `git` | `git` |
| DOCKER | `docker` | `docker` |
| KUBECTL | `kubectl` | `kubectl` |
| NPM | `npm` | `npm` |
| CARGO | `cargo` | `cargo` |
| PYTHON | `python3` | `python` / `python3` |
| NODE | `node` | `node` |
| RUSTC | `rustc` | `rustc` |
| MAKE | `make` | `make` |
| CMAKE | `cmake` | `cmake` |

## Essential Bash Patterns

### Variables
```bash
# Set
MY_VAR="value"
export MY_VAR="value"  # Export to environment

# Read
echo $MY_VAR
echo "${MY_VAR}"  # Quoted for safety

# Default value
VALUE="${MY_VAR:-default}"

# Required (error if unset)
: "${MY_VAR:?MY_VAR is required}"
```

### Conditionals
```bash
# File tests
if [ -f "file.txt" ]; then
    echo "Regular file"
elif [ -d "file.txt" ]; then
    echo "Directory"
elif [ -e "file.txt" ]; then
    echo "Exists (other)"
fi

# String tests
if [ "$var" = "value" ]; then
    echo "Equal"
fi

if [[ "$var" =~ ^[0-9]+$ ]]; then
    echo "Is number"
fi

# Numeric tests
if [ "$num" -gt 10 ]; then
    echo "Greater than 10"
fi

# Logical
if [ -f "a" ] && [ -f "b" ]; then
    echo "Both exist"
fi

if [ -f "a" ] || [ -f "b" ]; then
    echo "At least one exists"
fi
```

### Loops
```bash
# For loop (list)
for item in a b c; do
    echo "$item"
done

# For loop (C-style)
for ((i=0; i<10; i++)); do
    echo "$i"
done

# While loop
while [ condition ]; do
    echo "looping"
done

# Read lines
while IFS= read -r line; do
    echo "$line"
done < file.txt

# Process substitution
while read -r line; do
    echo "$line"
done < <(command)
```

### Functions
```bash
my_function() {
    local arg1="$1"
    local arg2="${2:-default}"
    
    echo "Processing $arg1"
    return 0
}

my_function "value"
```

### Command substitution
```bash
# Preferred
result=$(command)

# Legacy (avoid)
result=`command`

# Nested
result=$(echo "$(inner_command)")
```

### Pipes and redirection
```bash
# Pipe
cmd1 | cmd2

# Tee (output to both screen and file)
cmd | tee output.txt

# Redirect
cmd > output.txt        # Overwrite
cmd >> output.txt       # Append
cmd 2> error.txt        # stderr only
cmd 2>&1 > output.txt   # Both to file (order matters!)
cmd > output.txt 2>&1   # Both to file (preferred)

# Here-doc
cat <<EOF
Line 1
Line 2
$variable
EOF

# Here-string (no expansion)
cat <<'EOF'
$variable (literal)
EOF
```

### Error handling
```bash
# Check exit code
command
if [ $? -ne 0 ]; then
    echo "Failed"
fi

# Or with &&
command && echo "Success" || echo "Failed"

# Set -e (exit on error)
set -e

# Set -u (error on undefined variable)
set -u

# Set -o pipefail (pipe fails if any command fails)
set -o pipefail

# Combined (strict mode)
set -euo pipefail
```

### Working with files
```bash
# Read
content=$(cat file.txt)
lines=$(wc -l < file.txt)

# Write
echo "content" > file.txt
echo "more" >> file.txt

# Copy
cp src dst
cp -r src_dir dst_dir

# Move
mv src dst

# Delete
rm file.txt
rm -rf dir/

# Create directory
mkdir -p nested/dir

# List
ls -la
ls -lh
find . -name "*.rs" -type f
```

### Text processing
```bash
# Grep
grep "pattern" file.txt
grep -r "pattern" .
grep -i "pattern" file.txt  # Case insensitive
grep -n "pattern" file.txt  # Line numbers
grep -v "pattern" file.txt  # Invert

# Sed
sed 's/old/new/g' file.txt
sed -i 's/old/new/g' file.txt  # In-place (macOS: sed -i '' 's/old/new/g')

# AWK
awk '{print $1}' file.txt
awk -F',' '{print $2}' csv_file.csv

# Sort
sort file.txt
sort -u file.txt  # Unique
sort -r file.txt  # Reverse
sort -n file.txt  # Numeric

# Head/Tail
head -n 10 file.txt
tail -n 10 file.txt
tail -f file.txt  # Follow

# Cut
cut -d',' -f1,3 csv_file.csv

# Tr
tr 'a-z' 'A-Z' < file.txt
tr -d '\n' < file.txt  # Remove newlines

# WC
wc -l file.txt  # Lines
wc -c file.txt  # Bytes
wc -w file.txt  # Words
```

### HTTP
```bash
# Curl
curl -s http://api.example.com
curl -s -X POST -H "Content-Type: application/json" -d '{"key":"value"}' http://api.example.com
curl -s -H "Authorization: Bearer $TOKEN" http://api.example.com

# With output to file
curl -s -o output.json http://api.example.com/data

# Wget
wget -q -O output.json http://api.example.com/data
```

### JSON
```bash
# With jq (preferred)
echo '{"name":"test"}' | jq '.name'
cat data.json | jq '.items[]'
cat data.json | jq '.items[] | select(.status == "active")'

# With python (fallback)
python3 -c "import json,sys; print(json.load(sys.stdin)['name'])" < data.json
```

### Process management
```bash
# List
ps aux | grep "process"
pgrep "process"

# Kill
kill PID
kill -9 PID
pkill "process"

# Background
command &
jobs
fg %1
bg %1

# Wait
wait
wait PID
```

### Environment
```bash
# List
env
printenv
printenv MY_VAR

# Set
export MY_VAR="value"

# Unset
unset MY_VAR

# .env files
set -a
source .env
set +a
```

### Git
```bash
git status
git log --oneline -10
git diff
git add .
git commit -m "message"
git push
git pull
git checkout -b new-branch
git merge main
git rebase main
git stash
git stash pop
```

### Docker
```bash
docker compose up -d
docker compose down
docker compose logs -f
docker compose build
docker ps
docker images
docker exec -it container bash
```

## macOS vs Linux Differences

### Package managers
```bash
# macOS
brew install package

# Linux (Debian/Ubuntu)
sudo apt install package

# Linux (RHEL/Fedora)
sudo dnf install package
```

### Default shell
```bash
# macOS: /bin/zsh (default since Catalina), /bin/bash (3.2, old!)
# Linux: /bin/bash (4.x/5.x) or /bin/zsh

# Use bash explicitly:
bash script.sh
# Or shebang:
#!/usr/bin/env bash
```

### Path differences
```bash
# macOS
/usr/local/bin
/opt/homebrew/bin  # Apple Silicon
~/Library/

# Linux
/usr/bin
/usr/local/bin
~/.config/
```

### Service management
```bash
# macOS
launchctl list
launchctl start service

# Linux (systemd)
systemctl start service
systemctl status service
journalctl -u service
```

## Common Gotchas

### 1. Bash 3.2 on macOS
```bash
# macOS ships with bash 3.2 (GPLv3 issues)
# Install newer bash:
brew install bash
# Use: /opt/homebrew/bin/bash script.sh
# Or: bash -v  # Check version
```

### 2. `sed -i` differs
```bash
# macOS:
sed -i '' 's/old/new/g' file.txt

# Linux:
sed -i 's/old/new/g' file.txt
```

### 3. `read` with spaces
```bash
# IFS= prevents word splitting
while IFS= read -r line; do
    echo "$line"
done < file.txt
```

### 4. Quoting
```bash
# Always quote variables
echo "$var"  # Correct
echo $var    # Dangerous (word splitting, globbing)

# Nested quotes
echo "He said \"hello\""
echo 'It'"'"'"s'  # Escape single quote in single-quoted string
```

### 5. Array indexing
```bash
# Bash arrays are 0-indexed
arr=(a b c)
echo "${arr[0]}"  # a
echo "${#arr[@]}"  # 3 (length)

# Iterate
for item in "${arr[@]}"; do
    echo "$item"
done
```
