#!/bin/bash

# ==============================================================================

# Linux Incident Response & Forensics Collector

# Author: z0n

# Description:

# Collects logs, persistence artifacts, system state, user activity,

# network information, Docker artifacts, and forensic evidence.

# ==============================================================================

set -euo pipefail

PORT=8080
TS=$(date +%s)
EXPORT_DIR="/tmp/ir_collect_${TS}"
ARCHIVE_NAME="forensics_$(hostname)*$(date +%Y%m%d*%H%M%S).tar.gz"
FINAL_PATH="$(pwd)/${ARCHIVE_NAME}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cleanup() {
echo -e "\n${YELLOW}[*] Cleaning temporary files...${NC}"
rm -rf "$EXPORT_DIR" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

msg() {
echo -e "${GREEN}[+]${NC} $1"
}

warn() {
echo -e "${YELLOW}[*]${NC} $1"
}

try_copy() {
local src="$1"

```
if [ -e "$src" ]; then
    local parent
    parent=$(dirname "$src")
    local rel="${parent#/}"

    mkdir -p "$EXPORT_DIR/files/$rel"
    cp -a "$src" "$EXPORT_DIR/files/$rel/" 2>/dev/null || true
fi
```

}

collect_cmd() {
local outfile="$1"
shift

```
{
    echo "===== $* ====="
    "$@" 2>&1
} > "$outfile" || true
```

}

if [ "$EUID" -ne 0 ]; then
echo -e "${RED}[!] Run as root${NC}"
exit 1
fi

mkdir -p "$EXPORT_DIR"/{system,network,users,persistence,logs,docker,timeline,hashes}

msg "Collecting basic system information"

collect_cmd "$EXPORT_DIR/system/date.txt" date
collect_cmd "$EXPORT_DIR/system/uname.txt" uname -a
collect_cmd "$EXPORT_DIR/system/uptime.txt" uptime
collect_cmd "$EXPORT_DIR/system/mount.txt" mount
collect_cmd "$EXPORT_DIR/system/lsmod.txt" lsmod
collect_cmd "$EXPORT_DIR/system/df.txt" df -h
collect_cmd "$EXPORT_DIR/system/free.txt" free -h
collect_cmd "$EXPORT_DIR/system/env.txt" env

msg "Collecting process information"

collect_cmd "$EXPORT_DIR/system/ps_auxfww.txt" ps auxfww
collect_cmd "$EXPORT_DIR/system/pstree.txt" pstree -pa
collect_cmd "$EXPORT_DIR/system/lsof.txt" lsof -nP

msg "Collecting network information"

collect_cmd "$EXPORT_DIR/network/ip_addr.txt" ip addr
collect_cmd "$EXPORT_DIR/network/ip_route.txt" ip route
collect_cmd "$EXPORT_DIR/network/arp.txt" arp -a
collect_cmd "$EXPORT_DIR/network/ss_tulpan.txt" ss -tulpan
collect_cmd "$EXPORT_DIR/network/ss_anp.txt" ss -anp

iptables-save > "$EXPORT_DIR/network/iptables.txt" 2>/dev/null || true
nft list ruleset > "$EXPORT_DIR/network/nftables.txt" 2>/dev/null || true

msg "Collecting user activity"

collect_cmd "$EXPORT_DIR/users/who.txt" who -a
collect_cmd "$EXPORT_DIR/users/w.txt" w
collect_cmd "$EXPORT_DIR/users/last.txt" last -a
collect_cmd "$EXPORT_DIR/users/lastlog.txt" lastlog
collect_cmd "$EXPORT_DIR/users/faillog.txt" faillog

cp /etc/passwd "$EXPORT_DIR/users/passwd" 2>/dev/null || true
cp /etc/group "$EXPORT_DIR/users/group" 2>/dev/null || true
cp /etc/shadow "$EXPORT_DIR/users/shadow" 2>/dev/null || true

msg "Collecting persistence artifacts"

try_copy /etc/crontab
try_copy /etc/cron.d
try_copy /etc/cron.daily
try_copy /etc/cron.hourly
try_copy /etc/cron.weekly
try_copy /etc/cron.monthly
try_copy /var/spool/cron
try_copy /etc/systemd
try_copy /usr/lib/systemd
try_copy /etc/rc.local
try_copy /etc/profile
try_copy /etc/profile.d
try_copy /etc/bash.bashrc
try_copy /etc/sudoers
try_copy /etc/sudoers.d

systemctl list-units --type=service > "$EXPORT_DIR/persistence/services.txt" 2>/dev/null || true
systemctl list-unit-files > "$EXPORT_DIR/persistence/unit_files.txt" 2>/dev/null || true
systemctl list-timers > "$EXPORT_DIR/persistence/timers.txt" 2>/dev/null || true

msg "Collecting user artifacts"

for userhome in /home/*; do
[ -d "$userhome" ] || continue

```
try_copy "$userhome/.bash_history"
try_copy "$userhome/.zsh_history"
try_copy "$userhome/.ssh"
try_copy "$userhome/.config"
try_copy "$userhome/.aws"
try_copy "$userhome/.azure"
try_copy "$userhome/.kube"
try_copy "$userhome/.terraform.d"
```

done

try_copy /root/.bash_history
try_copy /root/.zsh_history
try_copy /root/.ssh

msg "Collecting logs"

try_copy /var/log/auth.log
try_copy /var/log/syslog
try_copy /var/log/kern.log
try_copy /var/log/dmesg
try_copy /var/log/audit
try_copy /var/log/journal
try_copy /var/crash

find /var/log -type f | while read -r file; do
try_copy "$file"
done

journalctl --no-pager -a > "$EXPORT_DIR/logs/journal_all.txt" 2>/dev/null || true
journalctl -b > "$EXPORT_DIR/logs/journal_boot.txt" 2>/dev/null || true
journalctl --list-boots > "$EXPORT_DIR/logs/journal_boots.txt" 2>/dev/null || true

msg "Collecting Docker artifacts"

if command -v docker >/dev/null 2>&1; then
docker ps -a > "$EXPORT_DIR/docker/containers.txt" 2>/dev/null || true
docker images > "$EXPORT_DIR/docker/images.txt" 2>/dev/null || true

```
for c in $(docker ps -aq 2>/dev/null); do
    docker inspect "$c" > "$EXPORT_DIR/docker/${c}_inspect.json" 2>/dev/null || true
    docker logs "$c" > "$EXPORT_DIR/docker/${c}_logs.txt" 2>/dev/null || true
done
```

fi

msg "Collecting timeline data"

find / -xdev -type f -printf "%TY-%Tm-%Td %TH:%TM:%TS %p\n" 
> "$EXPORT_DIR/timeline/filesystem_timeline.txt" 2>/dev/null || true

find / -xdev -type f -mtime -30 
> "$EXPORT_DIR/timeline/recent_files_30d.txt" 2>/dev/null || true

find /tmp /var/tmp /dev/shm -type f 
> "$EXPORT_DIR/timeline/temp_files.txt" 2>/dev/null || true

msg "Generating hashes of common binaries"

find /bin /sbin /usr/bin /usr/sbin -type f 2>/dev/null | while read -r f; do
sha256sum "$f"
done > "$EXPORT_DIR/hashes/binaries_sha256.txt" 2>/dev/null || true

msg "Creating archive"

tar -czf "$FINAL_PATH" -C "$EXPORT_DIR" .

sha256sum "$FINAL_PATH" > "${FINAL_PATH}.sha256"

echo
echo "===================================================="
echo "Archive : $FINAL_PATH"
echo "SHA256  : ${FINAL_PATH}.sha256"
echo "===================================================="

IP=$(hostname -I 2>/dev/null | awk '{print $1}')

if command -v python3 >/dev/null 2>&1; then
echo
echo "Download URL:"
echo "http://${IP}:${PORT}/$(basename "$FINAL_PATH")"
echo
cd "$(dirname "$FINAL_PATH")"
python3 -m http.server "$PORT"
fi
