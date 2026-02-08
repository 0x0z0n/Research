#!/bin/bash
# Professional Listener Audit Script

echo "[+] Current Listening Services:"
sudo ss -tulpn | grep LISTEN

echo -e "\n[+] Checking for suspicious 'container' processes..."
if pgrep -x "containerd" > /dev/null; then
    echo "[-] WARNING: Docker/Containerd is running but idle. Suggest: sudo systemctl stop docker"
fi

echo -e "\n[+] Checking for KDEConnect (External Risk)..."
if ss -tulpn | grep -q ":1716"; then
    echo "[-] WARNING: KDEConnect is exposed. Suggest: systemctl --user stop kdeconnect"
fi
