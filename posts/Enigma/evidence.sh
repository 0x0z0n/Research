#!/bin/bash

# ==============================================================================
# LINUX FORENSIC EVIDENCE COLLECTOR
# Description: Collects volatile + non-volatile evidence with SHA256 hashing,
#              chain of custody metadata, and structured output for analysis.
# Usage:       sudo bash forensics_collector.sh [--no-serve] [--port PORT]
# Author:      z0n (extended for forensic integrity)
# ==============================================================================

# --- Argument Parsing ---
SERVE=true
PORT=8080
for arg in "$@"; do
    case $arg in
        --no-serve) SERVE=false ;;
        --port) PORT="$2"; shift ;;
    esac
done

# --- Configuration ---
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)
INVESTIGATOR="${SUDO_USER:-$(whoami)}"
CASE_ID="CASE_${HOSTNAME}_${TIMESTAMP}"
EXPORT_DIR="/tmp/${CASE_ID}"
ARCHIVE_NAME="${CASE_ID}.tar.gz"
FINAL_PATH="$(pwd)/$ARCHIVE_NAME"
MANIFEST="$EXPORT_DIR/MANIFEST.txt"
CHAIN_OF_CUSTODY="$EXPORT_DIR/CHAIN_OF_CUSTODY.txt"
ERROR_LOG="$EXPORT_DIR/collection_errors.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ==============================================================================
# HELPERS
# ==============================================================================

log()    { echo -e "${GREEN}[+]${NC} $*"; }
warn()   { echo -e "${YELLOW}[!]${NC} $*"; }
info()   { echo -e "${CYAN}[*]${NC} $*"; }
err()    { echo -e "${RED}[ERR]${NC} $*" | tee -a "$ERROR_LOG"; }
header() { echo -e "\n${BOLD}${CYAN}=== $* ===${NC}"; }

# Run a command, save output to a file, log errors
collect_cmd() {
    local label="$1"
    local outfile="$2"
    shift 2
    local cmd=("$@")

    mkdir -p "$(dirname "$outfile")"
    if "${cmd[@]}" > "$outfile" 2>>"$ERROR_LOG"; then
        echo -e "    ${GREEN}[OK]${NC}  $label"
    else
        echo -e "    ${RED}[ERR]${NC} $label (see collection_errors.txt)"
    fi
}

# Copy a file/dir with mirrored path layout, log its SHA256 to manifest
collect_file() {
    local src="$1"
    local label="${2:-$src}"

    if [ ! -e "$src" ]; then return; fi

    local rel="${src#/}"
    local dest_dir="$EXPORT_DIR/fs/$rel"
    local dest

    if [ -d "$src" ]; then
        mkdir -p "$dest_dir"
        cp -r "$src/." "$dest_dir/" 2>>"$ERROR_LOG"
        echo -e "    ${GREEN}[OK]${NC}  Dir: $label"
        # Hash individual files inside
        find "$dest_dir" -type f | while read -r f; do
            local orig_path="/${f#$EXPORT_DIR/fs/}"
            sha256sum "$f" | awk -v p="$orig_path" '{print $1 "  " p}' >> "$MANIFEST"
        done
    else
        mkdir -p "$(dirname "$dest_dir")"
        dest="$EXPORT_DIR/fs/$rel"
        mkdir -p "$(dirname "$dest")"
        if cp "$src" "$dest" 2>>"$ERROR_LOG"; then
            local hash
            hash=$(sha256sum "$dest" | awk '{print $1}')
            echo "$hash  $src" >> "$MANIFEST"
            echo -e "    ${GREEN}[OK]${NC}  $label"
        else
            echo -e "    ${RED}[FAIL]${NC} Permission denied: $label" | tee -a "$ERROR_LOG"
        fi
    fi
}

# Cleanup on exit
cleanup() {
    local err=$?
    echo ""
    warn "Cleaning up staging directory..."
    rm -rf "$EXPORT_DIR"
    [ $err -ne 0 ] && err "Script exited with code $err" || log "Done."
}
trap cleanup EXIT INT TERM

# ==============================================================================
# PRE-FLIGHT
# ==============================================================================

echo -e "${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║       LINUX FORENSIC EVIDENCE COLLECTOR         ║"
echo "  ║       Case: $CASE_ID  ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Must run as root to collect all artifacts. Exiting.${NC}"
    exit 1
fi

# Tool availability checks
for tool in sha256sum tar ss find awk sed; do
    command -v "$tool" &>/dev/null || warn "Tool not found: $tool (some collection may be incomplete)"
done

# Prep directories
mkdir -p "$EXPORT_DIR"/{volatile,fs,logs,memory,artifacts}
touch "$MANIFEST" "$CHAIN_OF_CUSTODY" "$ERROR_LOG"

# Chain of Custody header
cat > "$CHAIN_OF_CUSTODY" << EOF
================================================================================
CHAIN OF CUSTODY — FORENSIC EVIDENCE COLLECTION
================================================================================
Case ID:         $CASE_ID
Hostname:        $HOSTNAME
Collection Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
Investigator:    $INVESTIGATOR
OS:              $(uname -a)
Tool:            forensics_collector.sh
================================================================================
This document records the provenance of collected evidence.
All file hashes are SHA256 and recorded in MANIFEST.txt.
================================================================================
EOF

log "Staging directory: $EXPORT_DIR"
log "Case ID: $CASE_ID"

# ==============================================================================
# PHASE 1 — VOLATILE DATA (collect first, evaporates on reboot)
# ==============================================================================

header "PHASE 1: VOLATILE DATA"
info "Capturing live system state (collect before anything changes)..."

V="$EXPORT_DIR/volatile"

# System identity
collect_cmd "Hostname / uptime"        "$V/identity.txt"             bash -c "echo '=== hostname ===' && hostname -f; echo; echo '=== uptime ===' && uptime; echo; echo '=== date ===' && date -u"
collect_cmd "Kernel & OS info"         "$V/kernel.txt"               bash -c "uname -a; echo; cat /etc/os-release 2>/dev/null || cat /etc/issue"
collect_cmd "Logged-in users"          "$V/users_current.txt"        who -a
collect_cmd "Login history"            "$V/users_history.txt"        last -a -F
collect_cmd "Failed logins"            "$V/failed_logins.txt"        lastb -a -F
collect_cmd "Last commands (w)"        "$V/w_output.txt"             w

# Processes
collect_cmd "Process list (full)"      "$V/processes_full.txt"       ps auxwwef
collect_cmd "Process tree"             "$V/process_tree.txt"         pstree -p -a
collect_cmd "Open files (lsof)"        "$V/open_files.txt"           lsof -nP
collect_cmd "Deleted-but-open files"   "$V/deleted_open_files.txt"   lsof -nP +L1

# Network state
collect_cmd "Active connections (ss)"  "$V/network_ss.txt"           ss -tulpna
collect_cmd "Routing table"            "$V/routing.txt"              ip route show table all
collect_cmd "ARP table"                "$V/arp.txt"                  ip neigh show
collect_cmd "Network interfaces"       "$V/interfaces.txt"           ip a
collect_cmd "Firewall rules (iptables)""$V/iptables.txt"             iptables-save
collect_cmd "Firewall rules (nftables)""$V/nftables.txt"             nft list ruleset
collect_cmd "DNS resolvers"            "$V/resolv.txt"               cat /etc/resolv.conf
collect_cmd "Hosts file"               "$V/hosts.txt"                cat /etc/hosts

# Memory-mapped / loaded modules
collect_cmd "Loaded kernel modules"    "$V/lsmod.txt"                lsmod
collect_cmd "Kernel ring buffer"       "$V/dmesg.txt"                dmesg -T
collect_cmd "Mounted filesystems"      "$V/mounts.txt"               mount
collect_cmd "Disk usage"               "$V/df.txt"                   df -h

# Environment & scheduled tasks
collect_cmd "Environment variables"    "$V/env.txt"                  env
collect_cmd "Active crontabs"          "$V/crontab_root.txt"         crontab -l
collect_cmd "Systemd timers"           "$V/systemd_timers.txt"       systemctl list-timers --all
collect_cmd "Running systemd units"    "$V/systemd_services.txt"     systemctl list-units --type=service --state=running

# ==============================================================================
# PHASE 2 — USER ARTIFACTS
# ==============================================================================

header "PHASE 2: USER ARTIFACTS"

collect_cmd "All local users"          "$V/passwd.txt"               cat /etc/passwd
collect_cmd "Group memberships"        "$V/group.txt"                cat /etc/group
collect_cmd "Sudoers"                  "$V/sudoers.txt"              bash -c "cat /etc/sudoers; ls /etc/sudoers.d/ && cat /etc/sudoers.d/*"
collect_cmd "SSH authorized_keys (all users)" "$V/ssh_authorized_keys.txt" bash -c "
    grep -v '^#' /etc/passwd | cut -d: -f1,6 | while IFS=: read user home; do
        f=\"\$home/.ssh/authorized_keys\"
        [ -f \"\$f\" ] && echo \"=== \$user: \$f ===\" && cat \"\$f\"
    done"
collect_cmd "SSH known_hosts (all users)" "$V/ssh_known_hosts.txt"  bash -c "
    grep -v '^#' /etc/passwd | cut -d: -f1,6 | while IFS=: read user home; do
        f=\"\$home/.ssh/known_hosts\"
        [ -f \"\$f\" ] && echo \"=== \$user: \$f ===\" && cat \"\$f\"
    done"

# Shell histories for all users + root
log "Collecting shell histories..."
for history_file in /root/.bash_history /root/.zsh_history /root/.sh_history \
                    /home/*/.bash_history /home/*/.zsh_history /home/*/.sh_history; do
    for f in $history_file; do
        [ -f "$f" ] && collect_file "$f" "Shell history: $f"
    done
done

# ==============================================================================
# PHASE 3 — PERSISTENCE MECHANISMS
# ==============================================================================

header "PHASE 3: PERSISTENCE MECHANISMS"

collect_cmd "Cron directories"         "$V/cron_dirs.txt"            bash -c "
    for d in /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/cron.monthly; do
        echo \"=== \$d ===\"; ls -la \"\$d\" 2>/dev/null && cat \"\$d\"/* 2>/dev/null; echo
    done"
collect_cmd "All user crontabs"        "$V/cron_all_users.txt"       bash -c "
    for user in \$(cut -d: -f1 /etc/passwd); do
        out=\$(crontab -l -u \"\$user\" 2>/dev/null)
        [ -n \"\$out\" ] && echo \"=== \$user ===\" && echo \"\$out\"
    done"
collect_cmd "Systemd unit files (user-installed)" "$V/systemd_custom_units.txt" bash -c "
    find /etc/systemd /usr/local/lib/systemd /home -name '*.service' -o -name '*.timer' 2>/dev/null | xargs ls -la 2>/dev/null"
collect_cmd "RC / init scripts"        "$V/rc_scripts.txt"           bash -c "ls -la /etc/rc*.d/ 2>/dev/null; ls -la /etc/init.d/ 2>/dev/null"
collect_cmd "LD_PRELOAD / ldconfig"    "$V/ld_preload.txt"           bash -c "echo \$LD_PRELOAD; cat /etc/ld.so.preload 2>/dev/null; ldconfig -p | head -30"
collect_cmd "SUID/SGID binaries"       "$V/suid_sgid.txt"            find / -xdev \( -perm -4000 -o -perm -2000 \) -type f -ls
collect_cmd "World-writable files"     "$V/world_writable.txt"       find / -xdev -perm -o+w -type f -not -path '/proc/*' -not -path '/sys/*' -ls
collect_cmd "Recently modified files (/etc /usr /bin /sbin, 7d)" "$V/recently_modified.txt" \
    find /etc /usr /bin /sbin /lib /lib64 -xdev -type f -newer /etc/passwd -ls

# ==============================================================================
# PHASE 4 — LOG FILES
# ==============================================================================

header "PHASE 4: LOG COLLECTION"

info "Copying /var/log (skipping compressed rotations)..."
find /var/log -type f \( -not -name "*.gz" -not -name "*.xz" -not -name "*.bz2" \) | while read -r f; do
    collect_file "$f"
done

# Web server logs outside /var/log
for path in /var/www /opt /srv; do
    if [ -d "$path" ]; then
        find "$path" -type f -name "*.log" -o -name "access_log" -o -name "error_log" 2>/dev/null | while read -r f; do
            collect_file "$f" "App log: $f"
        done
    fi
done

# Journal (binary, export as text)
if command -v journalctl &>/dev/null; then
    collect_cmd "Systemd journal (all, plain)" "$V/journal_all.txt" journalctl --no-pager -o short-precise
fi

# ==============================================================================
# PHASE 5 — CONFIGURATION & INSTALLED SOFTWARE
# ==============================================================================

header "PHASE 5: CONFIGURATION & SOFTWARE"

collect_cmd "Installed packages (dpkg)"  "$V/packages_dpkg.txt"   dpkg -l
collect_cmd "Installed packages (rpm)"   "$V/packages_rpm.txt"    rpm -qa
collect_cmd "pip packages"               "$V/packages_pip.txt"    bash -c "pip3 list 2>/dev/null; pip list 2>/dev/null"
collect_cmd "Listening services detail"  "$V/services_listen.txt" ss -tlnp

# Key config files
for cfg in /etc/ssh/sshd_config /etc/nginx/nginx.conf /etc/apache2/apache2.conf \
           /etc/mysql/my.cnf /etc/php.ini /etc/environment /etc/profile \
           /etc/security/limits.conf /etc/pam.d/common-auth; do
    [ -f "$cfg" ] && collect_file "$cfg"
done

# Web application configs (look for DB passwords, secrets)
info "Searching for web app configs containing credentials..."
collect_cmd "Web config files (*.conf *.ini *.php *.env)" "$V/webapp_configs_list.txt" \
    find /var/www /opt /srv /home -maxdepth 8 \( -name "*.conf" -o -name "*.ini" -o -name "config.php" -o -name ".env" -o -name "config.yaml" -o -name "config.yml" \) -type f -ls

# /tmp and /dev/shm (common drop zones for malware)
collect_cmd "Files in /tmp"       "$V/tmp_contents.txt"    ls -laR /tmp
collect_cmd "Files in /dev/shm"   "$V/devshm_contents.txt" ls -laR /dev/shm

# ==============================================================================
# PHASE 6 — NETWORK TRAFFIC SAMPLE (if tcpdump available)
# ==============================================================================

header "PHASE 6: NETWORK CAPTURE (30s sample)"

if command -v tcpdump &>/dev/null; then
    PCAP="$EXPORT_DIR/artifacts/capture_30s.pcap"
    info "Capturing 30 seconds of traffic (all interfaces)..."
    tcpdump -i any -s 65535 -w "$PCAP" -G 30 -W 1 2>>"$ERROR_LOG" &
    TCPDUMP_PID=$!
    sleep 32
    kill $TCPDUMP_PID 2>/dev/null
    wait $TCPDUMP_PID 2>/dev/null
    if [ -f "$PCAP" ]; then
        hash=$(sha256sum "$PCAP" | awk '{print $1}')
        echo "$hash  capture_30s.pcap" >> "$MANIFEST"
        echo -e "    ${GREEN}[OK]${NC}  PCAP capture saved"
    fi
else
    warn "tcpdump not found — skipping packet capture"
fi

# ==============================================================================
# PHASE 7 — INTEGRITY & FINALIZATION
# ==============================================================================

header "PHASE 7: INTEGRITY & PACKAGING"

# Finalize chain of custody
cat >> "$CHAIN_OF_CUSTODY" << EOF

--- Collection Complete ---
End Time:        $(date -u '+%Y-%m-%d %H:%M:%S UTC')
Total artifacts: $(find "$EXPORT_DIR" -type f | wc -l)
Error count:     $(wc -l < "$ERROR_LOG")

--- Investigator Signature ---
Investigator:    $INVESTIGATOR
System user:     $(id)
EOF

# Hash the manifest itself (meta-integrity)
MANIFEST_HASH=$(sha256sum "$MANIFEST" | awk '{print $1}')
echo "" >> "$CHAIN_OF_CUSTODY"
echo "MANIFEST.txt SHA256: $MANIFEST_HASH" >> "$CHAIN_OF_CUSTODY"

log "Manifest written: $(wc -l < "$MANIFEST") files hashed"
log "Compressing archive..."

cd "$EXPORT_DIR" || exit 1
tar -czf "$FINAL_PATH" . 2>>"$ERROR_LOG"

ARCHIVE_HASH=$(sha256sum "$FINAL_PATH" | awk '{print $1}')
log "Archive created: $FINAL_PATH"
log "Archive SHA256:  $ARCHIVE_HASH"

# Write a companion .sha256 file beside the archive
echo "$ARCHIVE_HASH  $ARCHIVE_NAME" > "${FINAL_PATH}.sha256"

# ==============================================================================
# PHASE 8 — SERVE (optional)
# ==============================================================================

if [ "$SERVE" = true ]; then
    IP=$(hostname -I | awk '{print $1}' 2>/dev/null)
    [ -z "$IP" ] && IP="0.0.0.0"

    echo ""
    echo -e "${BOLD}${YELLOW}=====================================================${NC}"
    echo -e "${YELLOW}  DOWNLOAD:  http://$IP:$PORT/$ARCHIVE_NAME${NC}"
    echo -e "${YELLOW}  HASH FILE: http://$IP:$PORT/${ARCHIVE_NAME}.sha256${NC}"
    echo -e "${YELLOW}  Press CTRL+C to stop server and cleanup staging.${NC}"
    echo -e "${BOLD}${YELLOW}=====================================================${NC}"

    cd "$(dirname "$FINAL_PATH")" || exit

    if command -v python3 &>/dev/null; then
        python3 -m http.server "$PORT"
    elif command -v python2 &>/dev/null; then
        python2 -m SimpleHTTPServer "$PORT"
    else
        warn "Python not found. Retrieve manually: $FINAL_PATH"
    fi
else
    echo ""
    log "Archive: $FINAL_PATH"
    log "Hash:    ${FINAL_PATH}.sha256"
    log "Done. No web server started (--no-serve)."
fi
