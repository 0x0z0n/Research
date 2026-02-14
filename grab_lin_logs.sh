#!/bin/bash

# ==============================================================================
# LOG EXFILTRATOR & THREAT HUNTING COLLECTOR
# Description: Collects logs, config, and system state, compresses them, 
#              and hosts them via a temporary HTTP server.
# Author: Gemini
# ==============================================================================

# --- Configuration ---
PORT=8080
EXPORT_DIR="/tmp/log_export_$(date +%s)"
ARCHIVE_NAME="loot_$(hostname)_$(date +%Y%m%d).tar.gz"
FINAL_PATH="$(pwd)/$ARCHIVE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Error Handling (The "Try/Catch" Mechanism) ---

# Trap interrupts (CTRL+C) and Exit signals to ensure cleanup happens
cleanup() {
    local err=$?
    echo -e "\n${YELLOW}[*] Cleaning up temporary files...${NC}"
    if [ -d "$EXPORT_DIR" ]; then
        rm -rf "$EXPORT_DIR"
    fi
    
    if [ $err -ne 0 ]; then
        echo -e "${RED}[!] Script exited with error code $err${NC}"
    else
        echo -e "${GREEN}[+] Done.${NC}"
    fi
}
trap cleanup EXIT INT TERM

# Function to safely execute commands (Try)
try_copy() {
    local src="$1"
    local dest="$2"
    
    if [ -e "$src" ]; then
        # Create parent directory structure in destination
        local parent_dir
        parent_dir=$(dirname "$src")
        # Remove leading slash for relative structure inside export dir
        local rel_parent="${parent_dir#/}"
        
        mkdir -p "$dest/$rel_parent"
        
        # Suppress errors, just try to copy
        cp -r "$src" "$dest/$rel_parent" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo -e "    ${GREEN}[OK]${NC} Copied: $src"
        else
            echo -e "    ${RED}[FAIL]${NC} Permission denied or locked: $src"
        fi
    fi
}

# --- Main Logic ---

echo -e "${YELLOW}====================================================${NC}"
echo -e "${YELLOW}   LINUX LOG COLLECTOR & EXFILTRATOR    ${NC}"
echo -e "${YELLOW}====================================================${NC}"

# 1. Root Check
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Error: Please run as root (sudo) to access /var/log${NC}"
    exit 1
fi

# 2. Prepare Staging
echo -e "${GREEN}[+] Creating staging directory: $EXPORT_DIR${NC}"
mkdir -p "$EXPORT_DIR"

# 3. System State Collection (Live volatile data)
echo -e "${GREEN}[+] Collecting System State (Processes, Network, Users)...${NC}"
mkdir -p "$EXPORT_DIR/system_info"

# Using OR (||) to catch missing commands
ss -tulpn > "$EXPORT_DIR/system_info/network_connections.txt" 2>/dev/null || netstat -tulpn > "$EXPORT_DIR/system_info/network_connections.txt" 2>/dev/null
ps auxww > "$EXPORT_DIR/system_info/running_processes.txt"
last -a > "$EXPORT_DIR/system_info/login_history.txt"
who -a > "$EXPORT_DIR/system_info/current_users.txt"
cat /etc/passwd > "$EXPORT_DIR/system_info/passwd_backup.txt"
crontab -l > "$EXPORT_DIR/system_info/root_crontab.txt" 2>/dev/null

# 4. Log Collection Strategy
echo -e "${GREEN}[+] Sweeping for Logs...${NC}"

# A. The Core /var/log directory (Recursive, but exclude huge rotated .gz files)
# We find files in /var/log, ignore .gz, .1, .2 (old logs) to save space, unless you want them.
echo -e "${YELLOW}    [*] Recursively copying /var/log (skipping compressed archives)...${NC}"
find /var/log -type f -not -name "*.gz" -not -name "*.xz" -not -name "*.1" | while read -r file; do
    try_copy "$file" "$EXPORT_DIR"
done

# B. Specific App Locations (If they exist outside /var/log)
APP_LOGS=(
    "/opt/extensiontool/logs"
    "/var/www/html"
    "/home/*/.bash_history" # Attempt to grab user histories
    "/root/.bash_history"
    "/etc/nginx"            # Grab config too
    "/etc/apache2"
)

for path in "${APP_LOGS[@]}"; do
    # Handle wildcards in paths
    for p in $path; do
        try_copy "$p" "$EXPORT_DIR"
    done
done

# 5. Compression
echo -e "${GREEN}[+] Compressing artifacts...${NC}"
cd "$EXPORT_DIR" || exit
tar -czf "$FINAL_PATH" .
echo -e "${GREEN}[+] Archive created at: $FINAL_PATH${NC}"

# 6. Serving via HTTP
echo -e "${GREEN}[+] Starting Web Server...${NC}"

# Get IP Address (Try hostname -I, fallback to ip addr)
IP=$(hostname -I | awk '{print $1}' 2>/dev/null)
if [ -z "$IP" ]; then
    IP="0.0.0.0"
fi

echo -e "${YELLOW}====================================================${NC}"
echo -e "${YELLOW} DOWNLOAD LINK: http://$IP:$PORT/$(basename "$FINAL_PATH")${NC}"
echo -e "${YELLOW} Press CTRL+C to stop the server and cleanup.${NC}"
echo -e "${YELLOW}====================================================${NC}"

# Move to the directory containing the archive to serve it
cd "$(dirname "$FINAL_PATH")" || exit

# Try Python 3, fallback to Python 2, fallback to failure message
if command -v python3 &>/dev/null; then
    python3 -m http.server "$PORT"
elif command -v python2 &>/dev/null; then
    python2 -m SimpleHTTPServer "$PORT"
else
    echo -e "${RED}[!] Python not found. Cannot start web server automatically.${NC}"
    echo -e "    You can download the file manually from: $FINAL_PATH"
fi
