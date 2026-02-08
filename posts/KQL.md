# Initial Access

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Spearphishing Attachment**

This query detects the execution of malicious attachments delivered via email, focusing on suspicious processes spawned by email clients or opening of files with common phishing extensions.

```kql
// Detect execution of suspicious attachments from email clients
DeviceProcessEvents
| where InitiatingProcessFileName in~ ("outlook.exe", "thunderbird.exe", "winmail.exe")
    // Add other email client executables relevant to your environment
| where FileName endswith ".exe" or FileName endswith ".dll" or FileName endswith ".scr" or FileName endswith ".hta"
    // Modify the list of extensions based on common malicious attachment types
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName, InitiatingProcessCommandLine
| order by Timestamp desc
```

---

2. **Drive-by Compromise**

This query detects the execution of scripts or downloads initiated by web browsers, which may indicate a drive-by compromise.

```kql
// Detect execution of scripts or downloads initiated by web browsers
DeviceProcessEvents
| where InitiatingProcessFileName in~ ("chrome.exe", "firefox.exe", "iexplore.exe", "edge.exe", "safari.exe")
    // Add or remove browsers as necessary
| where FileName endswith ".exe" or FileName endswith ".dll" or FileName endswith ".js" or FileName endswith ".vbs"
    // Include file types that could be maliciously downloaded
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName, InitiatingProcessCommandLine, 
InitiatingProcessParentFileName
| order by Timestamp desc
```

---

3. **Exploit Public-Facing Application**

This query detects suspicious processes or commands executed by public-facing applications, which may indicate exploitation attempts.

```kql
// Detect suspicious commands executed by public-facing applications
DeviceProcessEvents
| where InitiatingProcessFileName in~ ("w3wp.exe", "httpd.exe", "nginx.exe", "tomcat.exe")
    // Add other public-facing application processes as needed
| where ProcessCommandLine has_any ("cmd.exe", "powershell.exe", "whoami", "net user", "nslookup")
    // Include commands that are uncommon for these applications to execute
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName, InitiatingProcessCommandLine
| order by Timestamp desc
```

---

4. **External Remote Services**

This query identifies successful remote desktop or SSH connections from external IP addresses, which may indicate unauthorized access.

```kql
// Detect successful remote connections from external IPs
DeviceLogonEvents
| where LogonType == "RemoteInteractive"
| where RemoteIP != "127.0.0.1" and RemoteIP != "::1"  // Exclude localhost
| where isnotempty(RemoteIP)
| extend RemoteIPType = iff(ipv4_is_private(RemoteIP), "Private", "Public")
| where RemoteIPType == "Public"
| summarize LogonCount = count() by AccountName, RemoteIP, DeviceName
| order by LogonCount desc
```

---

5. **Valid Accounts**

This query detects the creation of new user accounts or addition of users to privileged groups, which may indicate the use of valid accounts for initial access.

```kql
// Detect creation of new user accounts or privilege escalation
DeviceEvents
| where ActionType in ("UserAccountCreated", "UserAddedToGroup")
| extend ParsedFields = parse_json(AdditionalFields)
| extend GroupName = tostring(ParsedFields.TargetGroupName)
| where ActionType == "UserAddedToGroup" and GroupName in ("Admin", "Remote Desktop Users", "Domain Admins")
    // Adjust group names based on your environment
| project Timestamp, DeviceName, ActionType, AccountName, InitiatingProcessAccountName, GroupName
| order by Timestamp desc
```

# Execution

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Detect files with known malware hashes**
   ```kql
   // Edit the list of known bad hashes to match the malware you are searching for
   DeviceFileEvents
   | where SHA256 in ("known_hash_1", "known_hash_2", "known_hash_3")
   | project DeviceName, SHA256, FileName, FolderPath, Timestamp
   ```

2. **Detect unusual file executions**
   ```kql
   // Customize "Temp" and "AppData" if malware is known to execute from other directories
   DeviceProcessEvents
   | where ProcessCommandLine contains ".exe" and (InitiatingProcessFolderPath contains "Temp" or InitiatingProcessFolderPath contains "AppData")
   | project DeviceName, ProcessCommandLine, InitiatingProcessFolderPath, Timestamp
   ```

3. **Identify PowerShell script executions**
   ```kql
   // Add specific PowerShell commands you expect attackers to use, if known
   DeviceProcessEvents
   | where ProcessCommandLine contains "powershell"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```

4. **Detect suspicious WMI activity**
   ```kql
   // Modify if specific WMI commands are of interest (e.g., suspicious processes)
   DeviceProcessEvents
   | where ProcessCommandLine contains "wmic"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```


# Persistence

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Detect changes to registry run keys**
   ```kql
   // Adjust the registry key paths to match other areas of interest (e.g., software persistence locations)
   DeviceRegistryEvents
   | where InitiatingProcessFolderPath endswith "Run"
   | project DeviceName, InitiatingProcessFolderPath, RegistryValueName, Timestamp
   ```

2. **Identify new services**
   ```kql
   // Customize if attackers typically use different commands to create services
   DeviceProcessEvents
   | where ProcessCommandLine contains "sc.exe create"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```

3. **Detect unusual scheduled tasks**
   ```kql
   // Modify the search to include other command-line tools for task scheduling (e.g., PowerShell)
   DeviceProcessEvents
   | where ProcessCommandLine contains "schtasks"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```

4. **Detect auto-start entries in startup folders**
   ```kql
   // Adjust folder paths based on known or suspected locations attackers might use for persistence
   DeviceFileEvents
   | where FolderPath contains "Startup"
   | project DeviceName, FileName, FolderPath, Timestamp
   ```

5. **Detect DLL hijacking attempts**
   ```kql
   // Modify file paths and file types if you suspect DLL hijacking attempts in other directories
   DeviceFileEvents
   | where FileName endswith ".dll" and (FolderPath contains "Windows" or FolderPath contains "System32")
   | project DeviceName, FileName, FolderPath, Timestamp
   ```

# Privilege Escalation

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Detect suspicious use of `whoami` command**
   ```kql
   // Optionally add other privilege-related commands to the search criteria
   DeviceProcessEvents
   | where ProcessCommandLine contains "whoami"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```

2. **Detect new administrative account creation**
   ```kql
   // Adjust "Administrators" group if you have other privileged groups
   IdentityInfo
   | where Type == "User" and AccountDomain == "Administrators"
   | project AccountName, Timestamp
   ```

3. **Unusual process started by `SYSTEM` user**
   ```kql
   // Add more specific filtering for processes you deem suspicious for SYSTEM account usage
   DeviceProcessEvents
   | where InitiatingProcessAccountName == "SYSTEM"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```

4. **Detect abnormal group membership changes**
   ```kql
   // Detect users added to the "Administrators" group
   DeviceEvents
   | where ActionType == "UserAddedToGroup"
   | extend ParsedFields = parse_json(AdditionalFields)
   | extend GroupName = tostring(ParsedFields.TargetGroupName)
   | where GroupName == "Administrators"
   | project Timestamp, AccountName, InitiatingProcessAccountName, GroupName
   | order by Timestamp desc
   ```

5. **Detect use of privileged service accounts**
   ```kql
   // Modify "svc" to match naming conventions for service accounts in your environment
   DeviceLogonEvents
   | where AccountName contains "svc" and LogonType == "Interactive"
   | project DeviceName, AccountName, Timestamp
   ```

# Defense Evasion

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Detect suspicious WMI activity**
   ```kql
   // Modify if specific WMI commands are of interest (e.g., suspicious processes)
   DeviceProcessEvents
   | where ProcessCommandLine contains "wmic"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```

# Credential Access

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Identify multiple failed network logon attempts**
   ```kql
   // Customize threshold (e.g., >5) for login failures based on your security policy
   DeviceNetworkEvents
   | where ActionType == "FailedLogin"
   | summarize FailedAttempts = count(), LastAttempt = max(Timestamp) by InitiatingProcessAccountName, RemoteIP
   | where FailedAttempts > 5
   | project LastAttempt, InitiatingProcessAccountName, RemoteIP, FailedAttempts
   ```

2. **Detect possible credential dumping (LSASS access)**
   ```kql
   // Look for suspicious access to LSASS (commonly targeted for credential dumping)
   DeviceProcessEvents
   | where ProcessCommandLine contains "lsass.exe"
   | where InitiatingProcessCommandLine contains "procdump" or InitiatingProcessCommandLine contains "mimikatz"
   | project Timestamp, DeviceName, AccountName, InitiatingProcessCommandLine
   ```

3. **Detect suspicious use of `rundll32` for credential access**
   ```kql
   // Monitor for rundll32 being used suspiciously to invoke malicious DLLs for credential theft
   DeviceProcessEvents
   | where ProcessCommandLine contains "rundll32.exe"
   | where ProcessCommandLine contains "samcli.dll" or ProcessCommandLine contains "vaultcli.dll"  // DLLs related to credential theft
   | project Timestamp, DeviceName, AccountName, ProcessCommandLine
   ```

4. **Detect suspicious PowerShell use for credential theft**
   ```kql
   // Monitor for suspicious PowerShell commands that may be related to credential harvesting
   DeviceProcessEvents
   | where ProcessCommandLine contains "powershell.exe"
   | where ProcessCommandLine contains "Get-Credential" or ProcessCommandLine contains "Get-Clipboard"
   | project Timestamp, DeviceName, AccountName, ProcessCommandLine
   ```


# Discovery

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Identify multiple failed network logon attempts**
   ```kql
   // Customize threshold (e.g., >5) for login failures based on your security policy
   DeviceNetworkEvents
   | where ActionType == "FailedLogin"
   | summarize FailedAttempts = count(), LastAttempt = max(Timestamp) by InitiatingProcessAccountName, RemoteIP
   | where FailedAttempts > 5
   | project LastAttempt, InitiatingProcessAccountName, RemoteIP, FailedAttempts
   ```

2. **Detect network scanning activity**
   ```kql
   // Replace RemotePort values to target additional known scanning ports or services
   DeviceNetworkEvents
   | where ActionType == "Scan" and RemotePort < 1024
   | summarize count() by DeviceName, RemoteIP
   ```

# Lateral Movement

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Detect RDP connections**
   ```kql
   // Adjust the port (3389) if your environment uses a non-standard port for RDP
   DeviceNetworkEvents
   | where RemotePort == 3389
   | project DeviceName, RemoteIP, Timestamp
   ```

2. **Detect abnormal SMB connections**
   ```kql
   // Customize RemotePort (445) if you use other SMB variants
   DeviceNetworkEvents
   | where RemotePort == 445
   | summarize count() by DeviceName, RemoteIP
   ```

3. **Detect use of `PsExec` tool**
   ```kql
   // Adjust based on known PsExec variants or command-line switches specific to your environment
   DeviceProcessEvents
   | where ProcessCommandLine contains "psexec"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```

4. **Detect lateral movement via WMI**
   ```kql
   // Add other WMI commands of interest if your environment has variations
   DeviceProcessEvents
   | where ProcessCommandLine contains "wmic" and ProcessCommandLine contains "\\"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```

5. **Detect remote service creation**
   ```kql
   // Modify "sc.exe create" if the attacker uses alternative service creation methods
   DeviceProcessEvents
   | where ProcessCommandLine contains "sc.exe" and ProcessCommandLine contains "create"
   | project DeviceName, ProcessCommandLine, Timestamp
   ```


# Collection

## Notes:
- Each script includes a comment on which part should be customized, such as file paths, file types, or specific processes, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Detect data staging in suspicious directories**
   ```kql
   // Edit the folder paths if attackers are known to use other directories in your environment
   DeviceFileEvents
   | where FolderPath contains "Temp" or FolderPath contains "Downloads" or FolderPath contains "AppData"
   | where FileName endswith ".zip" or FileName endswith ".rar" or FileName endswith ".7z"
   | project Timestamp, DeviceName, FolderPath, FileName, FileSize
   ```

2. **Detect large file transfers via Network Shares**
   ```kql
   // Adjust the file size threshold to fit your organization’s definition of "large files"
   DeviceFileEvents
   | where ActionType == "FileCreated" or ActionType == "FileModified"  // Track file creation or modification
   | where FolderPath startswith "\\\\"                                // Look for file access over network shares
   | where FileSize > 100000000  // Threshold set to 100 MB
   | project Timestamp, DeviceName, FileName, FolderPath, FileSize
   ```

3. **Detect screen capture activity**
   ```kql
   // Customize process names if attackers are known to use other screenshot tools in your environment
   DeviceProcessEvents
   | where ProcessCommandLine contains "snippingtool.exe" or ProcessCommandLine contains "mspaint.exe" or ProcessCommandLine contains "screenshot"
   | project Timestamp, DeviceName, ProcessCommandLine, InitiatingProcessAccountName
   ```

4. **Detect sensitive file access**
   ```kql
   // Update the file types and folder paths based on the types of sensitive data in your organization
   DeviceFileEvents
   | where FileName endswith ".docx" or FileName endswith ".xlsx" or FileName endswith ".pdf"
   | where FolderPath contains "Documents" or FolderPath contains "Finance"
   | project Timestamp, DeviceName, FileName, FolderPath, InitiatingProcessAccountName
   ```

5. **Detect clipboard access for potential data collection**
   ```kql
   // Edit the process names if attackers are known to use specific clipboard tools in your environment
   DeviceProcessEvents
   | where ProcessCommandLine contains "clip.exe" or ProcessCommandLine contains "powershell Get-Clipboard"
   | project Timestamp, DeviceName, ProcessCommandLine, InitiatingProcessAccountName
   ```

   # Command and Control (C2)

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Detect unusual outbound traffic**
   ```kql
   // This query identifies outbound traffic to public IPs on non-standard ports (above 1024). 
   // Adjust RemotePort or RemoteIPType based on your organization's network behavior.
   DeviceNetworkEvents
   | where RemoteIPType == "Public" and RemotePort > 1024
   | summarize count() by RemoteIP
   | sort by count_ desc
   ```

2. **Identify devices communicating with suspicious IPs**
   ```kql
   // Edit the list of known malicious IPs to suit your environment
   DeviceNetworkEvents
   | where RemoteIP in ("known_bad_ip_1", "known_bad_ip_2")
   | project DeviceName, RemoteIP, RemotePort, Timestamp
   ```

3. **Unusual DNS requests**
   ```kql
   // Adjust RemotePort if looking at different DNS services; customize domain TLDs if necessary
   DeviceNetworkEvents
   | where RemotePort == 53 and not (RemoteIP contains ".com" or RemoteIP contains ".org")
   | project DeviceName, RemoteIP, Timestamp
   ```

4. **Detect potential DNS tunneling activity**
   ```kql
   // Adjust the threshold and domain TLDs based on your organization's network behavior
   DnsEvents
   | where QueryType == "A"  // Filter for standard A (IPv4) DNS queries
   | where (Name endswith ".net" or Name endswith ".info" or Name endswith ".xyz")  // Adjust TLDs as necessary
   | summarize count() by ClientIP, Name
   | where count_ > 100  // DNS tunneling often generates a high volume of requests
   | project ClientIP, Name, count_
   ```

5. **Detect external connections to non-standard ports**
   ```kql
   // Replace RemoteIPType and adjust port range if necessary
   DeviceNetworkEvents
   | where RemoteIPType == "Public" and (RemotePort < 1024 or RemotePort > 65535)
   | project Timestamp, DeviceName, RemoteIP, RemotePort, ActionType
   ```


# Exfiltration

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Unusual DNS requests**
   ```kql
   // Adjust RemotePort if looking at different DNS services; customize domain TLDs if necessary
   DeviceNetworkEvents
   | where RemotePort == 53 and not (RemoteIP contains ".com" or RemoteIP contains ".org")
   | project DeviceName, RemoteIP, Timestamp
   ```

2. **Exfiltration Over C2 Channel**

```kql
// Detect unusual outbound connections to external IPs by uncommon processes
DeviceNetworkEvents
| where ActionType == "ConnectionSuccess"
| where InitiatingProcessFileName != "System"  // Exclude system processes; add more if necessary
| where RemoteIPType == "Public"  // Filters for external IP addresses
| summarize ConnectionCount = count() by 
    DeviceName, 
    InitiatingProcessFileName, 
    InitiatingProcessCommandLine, 
    RemoteIP
| where ConnectionCount > 1000  // Adjust this threshold based on normal activity
| order by ConnectionCount desc
```

```kql
// Detect processes making a high number of HTTP POST requests to external IPs
DeviceNetworkEvents
| where ActionType == "HttpPost"
| where RemoteIPType == "Public"
| where InitiatingProcessFileName != "System"
| summarize PostCount = count() by 
    DeviceName, 
    InitiatingProcessFileName, 
    InitiatingProcessCommandLine, 
    RemoteIP, 
    RemoteUrl
| where PostCount > 100  // Adjust this threshold based on normal activity
| order by PostCount desc
```

3. **Exfiltration Over Web Service**

This query looks for HTTP POST requests to popular cloud storage services, which may indicate data exfiltration via web services.

```kql
// Detect high number of HTTP POST requests to cloud storage services
DeviceNetworkEvents
| where ActionType == "HttpPost"
| where InitiatingProcessFileName != "System"  // Exclude system processes; modify as needed
| where RemoteUrl matches regex @"(dropbox\.com|drive\.google\.com|onedrive\.live\.com|box\.com|s3\.amazonaws\.com)"
// Modify the regex above to include or exclude specific cloud services relevant to your environment
| summarize PostCount = count() by 
    DeviceName, 
    InitiatingProcessFileName, 
    InitiatingProcessCommandLine, 
    RemoteUrl
| where PostCount > 50  // Adjust based on typical usage in your organization
| order by PostCount desc
```

4. **Archive Collected Data**

This query detects the creation of archive files by unusual processes, which may signal data being prepared for exfiltration.

```kql
// Detect creation of archive files by unusual processes
DeviceFileEvents
| where ActionType == "FileCreated"
| where FileName endswith '.zip' or FileName endswith '.rar' or FileName endswith '.7z' or FileName endswith '.tar.gz'
// Add or remove file extensions above to match archive formats used in your environment
| where InitiatingProcessFileName !in~ ('explorer.exe', 'winrar.exe', '7z.exe', 'tar.exe')  // Exclude known archiving tools; add any others used legitimately
| project Timestamp, 
    DeviceName, 
    InitiatingProcessFileName, 
    InitiatingProcessCommandLine, 
    FolderPath, 
    FileName
| order by Timestamp desc
```

5. **Obfuscated Files or Information**

This query searches for the use of encryption tools or commands, potentially indicating data encryption before exfiltration.

```kql
// Detect usage of encryption tools and commands
DeviceProcessEvents
| where ProcessCommandLine has_any ("gpg", "openssl", "certutil", "encrypt", "gpg.exe", "openssl.exe", "certutil.exe")
// Modify the list above to include or exclude encryption tools and keywords relevant to your environment
| project Timestamp, 
    DeviceName, 
    FileName, 
    ProcessCommandLine, 
    InitiatingProcessFileName, 
    InitiatingProcessCommandLine
| order by Timestamp desc

```


# Impact

## Notes:
- Each script includes a comment on which part should be customized, such as file hashes, IPs, or specific system directories, to suit your organization's environment.
- Ensure your query is designed to avoid false positives by fine-tuning based on local network behavior or naming conventions.

---

1. **Data Encrypted for Impact**

This query detects processes that are encrypting multiple files, which may indicate ransomware activity.

```kql
// Detect potential ransomware file encryption activity
DeviceFileEvents
| where ActionType == "FileModified"
| where FileName endswith ".encrypted" or FileName matches regex @".*\.(lock|crypt|cry)$"
    // Add or modify file extensions and patterns relevant to known ransomware in your environment
| where InitiatingProcessFileName != "explorer.exe"  // Exclude legitimate processes; add more if necessary
| summarize FileCount = count() by DeviceName, InitiatingProcessFileName, InitiatingProcessCommandLine
| where FileCount > 100  // Adjust threshold based on normal activity
| order by FileCount desc
```

2. **Inhibit System Recovery**

This query identifies attempts to delete or modify system recovery configurations or shadow copies, which can inhibit system recovery.

```kql
// Detect deletion of shadow copies and modifications to system recovery settings
DeviceProcessEvents
| where ProcessCommandLine has_any ("vssadmin delete shadows", "wmic shadowcopy delete", "diskshadow")
    or ProcessCommandLine has_any ("bcdedit /set", "wbadmin delete", "Remove-Item")
    // Add or adjust commands based on methods used to inhibit system recovery
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName, InitiatingProcessCommandLine
| order by Timestamp desc
```

3. **Service Stop**

This query detects attempts to stop or disable services, which can impact system functionality or security.

```kql
// Detect attempts to stop or disable services
DeviceProcessEvents
| where ProcessCommandLine has_any ("net stop", "sc stop", "Set-Service -Status Stopped", "Stop-Service")
    // Modify the list above to include other commands used to stop services
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName, InitiatingProcessCommandLine
| order by Timestamp desc
```

4. **System Shutdown/Reboot**

This query identifies processes initiating a system shutdown or reboot, which could be malicious if unexpected.

```kql
// Detect processes initiating system shutdown or reboot
DeviceProcessEvents
| where ProcessCommandLine has_any ("shutdown /s", "shutdown /r", "Restart-Computer", "Stop-Computer")
    // Add other commands or scripts used to shutdown or reboot systems in your environment
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName, InitiatingProcessCommandLine
| order by Timestamp desc
```

5. **Defacement**

This query detects modifications to web server content directories, which may indicate defacement activities.

```kql
// Detect modifications to web server content directories
DeviceFileEvents
| where ActionType in ("FileCreated", "FileModified", "FileDeleted")
| where FolderPath startswith @"C:\inetpub\wwwroot" or FolderPath startswith @"/var/www/html"
    // Adjust the paths above to match web content directories in your environment
| where InitiatingProcessFileName !in~ ("w3wp.exe", "httpd.exe", "nginx.exe")
    // Exclude legitimate web server processes; add more if necessary
| project Timestamp, DeviceName, ActionType, FileName, FolderPath, InitiatingProcessFileName, InitiatingProcessCommandLine
| order by Timestamp desc
```




# Technical


**NIST Incident Response Lifecycle (4 Phases)**:

1. **Preparation**

* Establish policies, response teams, tools, and training.

&#x20; **2. Detection & Analysis**

* Identify and assess potential incidents using logs, alerts, and reports.

3. **Containment, Eradication & Recovery**

* Limit damage, remove threats, and restore systems.

4. **Post-Incident Activity (Lessons Learned)**

* Review what happened, improve processes, and update documentation

\------------------------------------------------------------------------------------------------------

* **Linking files :** can mean different things depending on your context—whether you're trying to share files, create shortcuts, or reference files in code or systems.
* **Prefetch files** : are special system files created by Windows to speed up application startup times. They act like a shortcut for your operating system, storing data about how and where programs load so that future launches are faster and more efficient.

🚀 What Prefetch Files Do

* When you run an app for the first time, Windows creates a .pf file in the C:\Windows\Prefetch folder.
* This file contains metadata like:
* App name and path
* Run count
* Last execution timestamp
* Resources loaded during launch
* Windows uses this info to optimize disk access and reduce boot time for frequently used apps.

🔍 Forensics & Analysis Prefetch files are useful in digital forensics:

* Reveal which apps were run, when, and how often.
* Help investigators track malware execution or user activity.
* Each .pf file includes a hash of the executable path, making it unique to where the app was launched.

🧼 Can You Delete Them? Yes, but with caveats:

* Safe to delete if you're freeing up space or troubleshooting.
* Windows will recreate them as needed.
* Deleting them may cause apps to load slightly slower the next time. To delete: Win + R → type "prefetch" → Enter → Ctrl + A → Delete

***

## Common Event Types in Application Logs

* Startup and shutdown events for applications
* Crash reports or unhandled exceptions
* License or activation issues
* Database connection failures
* Service start/stop notifications
* Custom application messages (if the app is designed to log them)

***

## <sub>Mimikatz : Extract the sensitive password from windows systems</sub>

**Pass the hash attack** : A Pass-the-Hash (PtH) attack is a cyber technique where an attacker uses a hashed version of a password—rather than the actual password—to authenticate and gain access to systems.

***

## Name 5 log sources which an organization needed while integrating EDR or SIEM?

1. Firewall logs
2. Network devices logs
3. Endpoint logs
4. Cloud services logs
5. Active directory logs

***

## Name IPS / Firewall / windows alerts ?

**IPS** : Alert triggeres when identifies knowm malware signatures / Alerts on unauthorized access attempts

**Windows** : suspicious login attempts/brute force attempt / suspicious service creation / Data exfilteration

**Firewall :** recon activity targeting open ports / excessive firewall denies / unauthorized access attempts

\---------------------------------------------------------------------------------------------------------

## **63676 - Cybersecurity Awareness: Phishing Attacks**

\
**Vishing attack** - over phone
\
**Robo calls -** An automated phone call plays a recorded msg
\
**Called ID spoofing** - changing orginal number with other number
\
**Social media phishing** - uses social media platform to trick people
\
**Whaling attack** - targets high level executives of an organization
\
**Spear phishing** - gathers target information and prepare detailed and convincing profile.

***

**Powershell** : It is task based command line shell and scripting language what powershell can do : \* Automate system admin tasks \* Manage files, processes , registry \* Interact with API's and cloud platform \* Run scripts for configuration monitoring and deployment. \* Perform remote management and orchestration.

CMDLets: Get-process - list of processes running on system Get-Service - list of services Get-EventLog - retrives event logs Invoke-WebRequest : sends HTTP and HTTPS requests Test-NetConnection - Displays diagnostic information for connection.

$content = Get-Content -path 'example.txt'

***

***

**LoLBin** - Living off the land binary are legit system executables that attacker repurpose for malicious activities
\
Lolbin attck involves using trusted , pre-installed binaries (powershell.exe , msiexec.exe)

[download payload
\
execute malicious code
\
bypass security controls
\
perform lateral movement](#user-content-fn-1)[^1]

because these binaries are signed with Microsoft so AV EDR will ignore these services.

We should enable script blocking or monitor unusual behavior of inbuild Lolbins

### watch Lolbin attack videos on youtube.\*\*\*\*\*\*\*\*\*\*\*\*

\------------------------------------------------------------------------------------------------

**Lateral movement :**
\
it is Key tactic of advance cybersecurity attack.
\
After initial compromise,it refers how attacker move within network from one system/application/account to another.

* explore internal network
* escalate previelegs
* spread across endpoint applications
* maintain persistent even initial entry point is discovered.

**Common techniques used :**
\
Pass the hash - reuse the password to authenticate
\
Internal phishing

### <sup>We can apply least previleges between systems</sup>&#xD; <sup>configure EDR/XDR to monitor processes</sup>&#xD; <sup>monitor UEBA to capture unusual behavior</sup>

<sup>------------------------------------------------------------------------------------------------------------------------------------------</sup>

**Privilege escalation:**

It is a cyber security concept where attacker gains unauthorized access to higher level permissions within system/network/application\\

**Types of Privilege escalation:**
\
\* Vertical - elevet higher access
\
\* Horizontal - gains access to other system with same privilege

\---------------------------------------------------------------------------------------------------------

**Persistent :**&#x49;t refers to techniques and strategies attacker use to maintain ongoing access to compromised system.

### common persistent techniques:&#xD; <sup><sub>Scheduled tasks/cron jobs : re-execute malware at regular intervals<sub></sup>&#xD; <sup><sub>Registry run keys : auto start malware on windows boot<sub></sup>&#xD; <sup><sub>web shells : maintain access via compromised web servers<sub></sup>&#xD; <sup><sub>rootkits :<sub></sup>&#xD; <sup><sub>tocken/session hijacking - reuse stolen credentials<sub></sup>&#xD; <sup><sub>service creation: install malicious services that servive reboots<sub></sup>

<sup><sub>----------------------------------------------------------------------------------------------------------------------------------------<sub></sup>

**Defense evasion :** avoid detection and bypass security controls

\----------------------------------------------------------------------------------------------------------

**Web shell :** It is malicious script uploaded on web server that allows attackers to remotely execute the commands and control the server.
\
it is installed after exploiting vulnerabilities like SQL injection , misconfigured servers

reverse shell - connect back to attacker system by bypassing firewall

\--------------------------------------------------------------------------------------------------------

**Scheduled tasks Event ID's :**&#x20;

4698 - Scheduled task created

4699 - Scheduled task deleted

4700 - Scheduled task enabled
\
4701 - Scheduled task Disabled

[^1]:



# Mitre Attack

# MITRE ATT\&CK

**The MITRE ATT\&CK Framework**—short for *Adversarial Tactics, Techniques, and Common Knowledge*—is a globally accessible knowledge base that documents how cyber adversaries behave in real-world attacks. It’s like a playbook of hacker moves, used by defenders to anticipate, detect, and respond to threats more effectively.

🎯 Purpose of MITRE ATT\&CK

* **Standardizes threat intelligence** by mapping attacker behavior to known patterns.
* **Improves detection and response** by helping security teams recognize tactics and techniques.
* **Supports red and blue teams** in simulating and defending against realistic attack scenarios.
* **Enables security gap analysis** to identify weaknesses in defenses.
* **Fosters collaboration** with a shared language across cybersecurity teams.

🧩 Structure: Tactics, Techniques, and Procedures (TTPs)

🔐 Example:

* **Tactic**: Credential Access
* **Technique**: Brute Force
* **Sub-technique**: Password Spraying
* **Procedure**: APT28 using Hydra to automate login attempts

🛠️ How It's Used

🔍 Threat Detection & Hunting

* Map logs and alerts to ATT\&CK techniques to identify suspicious behavior.
* Build behavioral analytics that go beyond signature-based detection.

🧪 Red Teaming & Adversary Emulation

* Simulate known threat actor campaigns using documented TTPs.
* Test defenses against realistic attack paths.

🛡️ Security Operations & SOC Maturity

* Assess coverage across tactics and techniques.
* Prioritize detection engineering and response playbooks.

**Purpose Behind Its Creation**

* **Bridge the gap between threat intelligence and defense**: Traditional security tools relied heavily on static indicators like IP addresses or file hashes, which attackers could easily change. MITRE ATT\&CK introduced a **behavioral approach**, focusing on how adversaries operate rather than what tools they use.
* **Enable proactive defense**: Instead of reacting to known malware, ATT\&CK helps organizations **anticipate attacker moves** and build resilient detection strategies

Real-World Roots

The framework is based on **actual observations** from cyber incidents, threat reports, and analyst research. That’s why it continues to evolve—new techniques are added as attackers adapt


# MITRE ATT\&CK

**The MITRE ATT\&CK Framework**—short for *Adversarial Tactics, Techniques, and Common Knowledge*—is a globally accessible knowledge base that documents how cyber adversaries behave in real-world attacks. It’s like a playbook of hacker moves, used by defenders to anticipate, detect, and respond to threats more effectively.

🎯 Purpose of MITRE ATT\&CK

* **Standardizes threat intelligence** by mapping attacker behavior to known patterns.
* **Improves detection and response** by helping security teams recognize tactics and techniques.
* **Supports red and blue teams** in simulating and defending against realistic attack scenarios.
* **Enables security gap analysis** to identify weaknesses in defenses.
* **Fosters collaboration** with a shared language across cybersecurity teams.

🧩 Structure: Tactics, Techniques, and Procedures (TTPs)

🔐 Example:

* **Tactic**: Credential Access
* **Technique**: Brute Force
* **Sub-technique**: Password Spraying
* **Procedure**: APT28 using Hydra to automate login attempts

🛠️ How It's Used

🔍 Threat Detection & Hunting

* Map logs and alerts to ATT\&CK techniques to identify suspicious behavior.
* Build behavioral analytics that go beyond signature-based detection.

🧪 Red Teaming & Adversary Emulation

* Simulate known threat actor campaigns using documented TTPs.
* Test defenses against realistic attack paths.

🛡️ Security Operations & SOC Maturity

* Assess coverage across tactics and techniques.
* Prioritize detection engineering and response playbooks.

**Purpose Behind Its Creation**

* **Bridge the gap between threat intelligence and defense**: Traditional security tools relied heavily on static indicators like IP addresses or file hashes, which attackers could easily change. MITRE ATT\&CK introduced a **behavioral approach**, focusing on how adversaries operate rather than what tools they use.
* **Enable proactive defense**: Instead of reacting to known malware, ATT\&CK helps organizations **anticipate attacker moves** and build resilient detection strategies

Real-World Roots

The framework is based on **actual observations** from cyber incidents, threat reports, and analyst research. That’s why it continues to evolve—new techniques are added as attackers adapt


# MITRE ATT\&CK

**The MITRE ATT\&CK Framework**—short for *Adversarial Tactics, Techniques, and Common Knowledge*—is a globally accessible knowledge base that documents how cyber adversaries behave in real-world attacks. It’s like a playbook of hacker moves, used by defenders to anticipate, detect, and respond to threats more effectively.

🎯 Purpose of MITRE ATT\&CK

* **Standardizes threat intelligence** by mapping attacker behavior to known patterns.
* **Improves detection and response** by helping security teams recognize tactics and techniques.
* **Supports red and blue teams** in simulating and defending against realistic attack scenarios.
* **Enables security gap analysis** to identify weaknesses in defenses.
* **Fosters collaboration** with a shared language across cybersecurity teams.

🧩 Structure: Tactics, Techniques, and Procedures (TTPs)

🔐 Example:

* **Tactic**: Credential Access
* **Technique**: Brute Force
* **Sub-technique**: Password Spraying
* **Procedure**: APT28 using Hydra to automate login attempts

🛠️ How It's Used

🔍 Threat Detection & Hunting

* Map logs and alerts to ATT\&CK techniques to identify suspicious behavior.
* Build behavioral analytics that go beyond signature-based detection.

🧪 Red Teaming & Adversary Emulation

* Simulate known threat actor campaigns using documented TTPs.
* Test defenses against realistic attack paths.

🛡️ Security Operations & SOC Maturity

* Assess coverage across tactics and techniques.
* Prioritize detection engineering and response playbooks.

**Purpose Behind Its Creation**

* **Bridge the gap between threat intelligence and defense**: Traditional security tools relied heavily on static indicators like IP addresses or file hashes, which attackers could easily change. MITRE ATT\&CK introduced a **behavioral approach**, focusing on how adversaries operate rather than what tools they use.
* **Enable proactive defense**: Instead of reacting to known malware, ATT\&CK helps organizations **anticipate attacker moves** and build resilient detection strategies

Real-World Roots

The framework is based on **actual observations** from cyber incidents, threat reports, and analyst research. That’s why it continues to evolve—new techniques are added as attackers adapt



# Microsoft  Sentinel (SIEM)

## Microsoft Sentinel workspace <a href="#module-unit-title" id="module-unit-title"></a>

Before deploying Microsoft Sentinel, it's crucial to understand the workspace options. The Microsoft Sentinel solution is installed in a Log Analytics Workspace, and most implementation considerations are focused on the Log Analytics Workspace creation. The single most important option when creating a new Log Analytics Workspace is the region. The region specifies the location where the log data will reside.

The three implementation options:

* Single-Tenant with a single Microsoft Sentinel Workspace
* Single-Tenant with regional Microsoft Sentinel Workspaces
* Multi-Tenant

### Single-tenant single workspace <a href="#single-tenant-single-workspace" id="single-tenant-single-workspace"></a>

The single-tenant with a single Microsoft Sentinel workspace will be the central repository for logs across all resources within the same tenant.

This workspace receives logs from resources in other regions within the same tenant. Because the log data (when collected) will travel across regions and stored in another region, this creates two possible concerns. First, it can incur a bandwidth cost. Second, if there's a data governance requirement to keep data in a specific region, the single workspace option wouldn't be an implementation option.

<figure><img src="https://2363832561-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcXy5hq3eo7DEg0EEJn0D%2Fuploads%2Fy5rqE6RjvGJpNJx0aMFq%2Fimage.png?alt=media&#x26;token=bb4d794e-3215-4dcd-857e-52c984f05bf3" alt=""><figcaption></figcaption></figure>

### Single-tenant with regional Microsoft Sentinel workspaces <a href="#single-tenant-with-regional-microsoft-sentinel-workspaces" id="single-tenant-with-regional-microsoft-sentinel-workspaces"></a>

The single-tenant with regional Microsoft Sentinel workspaces will have multiple Sentinel workspaces requiring the creation and configuration of multiple Microsoft Sentinel and Log Analytics workspaces.

<figure><img src="https://2363832561-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcXy5hq3eo7DEg0EEJn0D%2Fuploads%2FPmE9ZFNVYvHbH79WTqHd%2Fimage.png?alt=media&#x26;token=3afa2b70-b032-446d-986a-ad17eb8d1eb4" alt=""><figcaption></figcaption></figure>

### Multi-tenant workspaces <a href="#multi-tenant-workspaces" id="multi-tenant-workspaces"></a>

If you're required to manage a Microsoft Sentinel workspace, not in your tenant, you implement Multi-Tenant workspaces using Azure Lighthouse. This security configuration grants you access to the tenants. The tenant configuration within the tenant (regional or multi-regional) is the same consideration as before.

<figure><img src="https://2363832561-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcXy5hq3eo7DEg0EEJn0D%2Fuploads%2F9Vq9lHmTo1XEzHnxynWq%2Fimage.png?alt=media&#x26;token=07d8c410-52c4-4a24-a040-d7e731c3ba98" alt=""><figcaption></figcaption></figure>

resource group --> log analytics workspace --> Add Microsoft sentinel&#x20;

### Create and configure a Log Analytics Workspace <a href="#create-and-configure-a-log-analytics-workspace" id="create-and-configure-a-log-analytics-workspace"></a>

1. The next page, **Add Microsoft Sentinel to a workspace** will display a list of available Log Analytics workspaces to add Microsoft Sentinel. Select the **+ create a new workspace** button to start the "Create Log Analytics workspace" process.
2. The Basics tab includes the following options:

   Expand table

   | Option         | Description                                                                                                    |
   | -------------- | -------------------------------------------------------------------------------------------------------------- |
   | Subscription   | Select the Subscription                                                                                        |
   | Resource Group | Select or create a Resource Group                                                                              |
   | Name           | Name is the name of the Log Analytics workspace and will also be the name of your Microsoft Sentinel Workspace |
   | Region         | The region is the location the log data is stored.                                                             |

   3.Select the **Review + Create** button and then select the **Create** button.

### Add Microsoft Sentinel to the workspace <a href="#add-microsoft-sentinel-to-the-workspace" id="add-microsoft-sentinel-to-the-workspace"></a>

The "Add Microsoft Sentinel to Workspace" screen will now appear after you've completed the previous steps.

1. Wait for the newly created "Log Analytics Workspace" to appear in the list. This operation could take a few minutes.
2. Select the newly created Log Analytics workspace. And select the **Add** button.

The new Microsoft Sentinel workspace is now the active screen. The Microsoft Sentinel left navigation has four areas:

* General
* Threat management
* Content management
* Configuration

The Overview tab displays a standard dashboard of information about the ingested data, alerts, and incidents.

**To change event retention period:**\
&#x20;            Goto Setting --> Workspace setting --> Tables --> 3 dots(right side ) --> Manage table --> select days in interactive retention like 30-60-90 days.

## Manage workspaces across tenants using Azure Lighthouse <a href="#module-unit-title" id="module-unit-title"></a>

If you're required to manage multiple Microsoft Sentinel workspaces, or workspaces not in your tenant, you have two options:

* Microsoft Sentinel Workspace manager
* Azure Lighthouse

### Microsoft Sentinel Workspace manager <a href="#microsoft-sentinel-workspace-manager" id="microsoft-sentinel-workspace-manager"></a>

Microsoft Sentinel's Workspace manager enables users to centrally manage multiple Microsoft Sentinel workspaces within one or more Azure tenants. The Central workspace (with Workspace manager enabled) can consolidate content items to be published at scale to Member workspaces. Workspace manager is enabled in the `Configuration settings`.

<figure><img src="https://2363832561-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcXy5hq3eo7DEg0EEJn0D%2Fuploads%2FFqgq35XSUoFS25mvTxrO%2Fimage.png?alt=media&#x26;token=282252f1-ca88-4bde-b8a5-8350013ac51d" alt=""><figcaption></figcaption></figure>

### Azure Lighthouse <a href="#azure-lighthouse" id="azure-lighthouse"></a>

Implementing Azure Lighthouse provides the option to enable your access to the tenant. Once Azure Lighthouse is onboarded, use the directory + subscription selector on the Azure portal to select all the subscriptions containing workspaces you manage.

Azure Lighthouse allows greater flexibility to manage resources for multiple customers without having to sign in to different accounts in different tenants. For example, a service provider may have two customers with different responsibilities and access levels. By using Azure Lighthouse, authorized users can sign in to the service provider's tenant to access these resources

### Microsoft Sentinel-specific roles <a href="#microsoft-sentinel-specific-roles" id="microsoft-sentinel-specific-roles"></a>

All Microsoft Sentinel built-in roles grant read access to the data in your Microsoft Sentinel workspace:

* **Microsoft Sentinel Reader**: can view data, incidents, workbooks, and other Microsoft Sentinel resources.
* **Microsoft Sentinel Responder**: can, in addition to the above, manage incidents (assign, dismiss, etc.)
* **Microsoft Sentinel Contributor**: can, in addition to the above, create and edit workbooks, analytics rules, and other Microsoft Sentinel resources.
* **Microsoft Sentinel Automation Contributor**: allows Microsoft Sentinel to add playbooks to automation rules. It isn't meant for user accounts.

**Giving Microsoft Sentinel permissions to run playbooks**

Microsoft Sentinel uses a **special service account** to run incident-trigger playbooks manually or to call them from automation rules. The use of this account (as opposed to your user account) increases the security level of the service.

In order for an automation rule to run a playbook, this account must be granted explicit permissions to the resource group where the playbook resides. At that point, any automation rule will be able to run any playbook in that resource group. To grant these permissions to this service account, your account must have Owner permissions on the resource groups containing the playbooks.

* **Connecting data sources to Microsoft Sentinel**

  For a user to add data connectors, you must assign the user write permissions on the Microsoft Sentinel workspace. Also, note the required other permissions for each connector, as listed on the relevant connector page.
* **Guest users assigning incidents**

  If a guest user needs to be able to assign incidents, then in addition to the Microsoft Sentinel Responder role, the user will also need to be assigned the role of Directory Reader.

### Microsoft Sentinel roles and allowed actions <a href="#microsoft-sentinel-roles-and-allowed-actions" id="microsoft-sentinel-roles-and-allowed-actions"></a>

The following table summarizes the roles and allowed actions in Microsoft Sentinel.

<figure><img src="https://2363832561-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcXy5hq3eo7DEg0EEJn0D%2Fuploads%2Fna69Sts1bdmH1YzLsUTX%2Fimage.png?alt=media&#x26;token=83fd32cc-58fc-46ab-9dde-257e56a062e1" alt=""><figcaption></figcaption></figure>

{{{% embed url="<https://learn.microsoft.com/en-us/training/modules/create-manage-azure-sentinel-workspaces/6-manage-azure-sentinel-settings>" %}}}

**Rule configuration in sentinel -** analytics -Scheduled query -Near Real time query rule -Microsoft incident creation rule

**data source integration in sentinel** - content Hub (install solution) --> Data connector (map the connector)and create data collection rule - select VM -> Select data type ->review and create.

<kbd>**To exclude certain events from being indexed by Microsoft Sentinel**</kbd><kbd>,</kbd>&#x20;

you can use **ingestion-time filtering** or **Data Collection Rules (DCR)** with the **Azure Monitor Agent (AMA)**. Here are the steps for both methods:

#### Ingestion-Time Filtering

1. **Navigate to Settings**: In Microsoft Sentinel, go to the **Settings** section.
2. **Select Data Sources**: Choose the data source you want to configure.
3. **Configure Ingestion-Time Filters**: Set up filters to exclude specific events based on criteria like Event ID, Source, or other attributes.

#### Using Data Collection Rules (DCR) with AMA

1. **Create a Data Collection Rule**: In the **Azure Monitor** section, create a new Data Collection Rule.
2. **Define the Rule**: Specify the criteria for collecting data, including exclusions for certain events.
3. **Deploy the Rule**: Apply the rule to the relevant systems or virtual machines.

#### Example: Excluding Specific Event IDs

If you want to exclude specific event IDs, you can configure the rule to ignore those IDs during data collection. For example, to exclude Event ID 4662 (which is often related to object access), you can set up a filter in the DCR to ignore this ID

## rsyslog / syslog-ng is log forwarding tools which uses syslog protocol


# Rule creation

**Rule configuration in sentinel -** analytics -Scheduled query -Near Real time query rule -Microsoft incident creation rule

1. Goto Configuration&#x20;
2. Analytics
3. Create - > NRT Query Rule&#x20;
4. General&#x20;
   1. Rule name&#x20;
   2. Description
   3. Severity
   4. Mitre attack
5. Set Rule logic&#x20;
   1. Enter Query to search logs
   2. Event Grouping - select group all events into single alert
   3. Supression - enable  - Stop running query after alert is generated
6. Incident setting&#x20;
7. Automate response
8. Review and create.



# Device Onboarding

Steps to collect Logs from Windows VM :

1. Install AMA on VM
2. Create a Data collection Rule that targets Security event Log
3. Assign DCR to your VM
4. Verify Logs in sentinel

**if its Azure windows VM then**

* Go to VM resource from Azure portal
* Under monitoring ,select Extensions + Applications
* Click + add and select AzureMonitorWindowsAgent

**If its Non Azure or on-Prem VM**

* Download Azure ARC script from Azure portal
* Run script on on prem VM so it will listdown in Azure
* then install AMA agent from extensions.

## Ports used for integration:

**For Windows :** \
Win VM —---- 5986-------> Windows event Forwarding(Forwarder) ------> AMA ------443------> Ms Sentinel

VM --> Forwarder = 5986\
Forwarder via AMA --> Sentinel = 443

**For Linux :**\
VM -----514-----> Rsyslog/rsyslog.ng -----28330------> AMA -------443-----> Sentinel

VM ---> Rsyslog = 514\
rsyslog --> AMA = 28330\
AMA --> Sentinel = 443



# Playbook Creation in Sentinel

Playbook

we need to design work flow then define automation rule to execute it

1. Goto sentinel --> Automation --> Playbook
2. Click + Add > Playbook with incident trigger
3. Use Logic app designer to build a workflow
   * Trigger : when incident created or updated
   * Action : Send email , Call API's , update ticket etc.
4. Setup Automation Rule : It controls when and How playbook run
   * Goto Sentinel -> Automation -> Automation Rules
   * Click + Add new rule
     * Condition : Incident severity , status , entity type
     * Actions : Run Playbook , Assign incident , tag incident


# Sentinel Interview que.

**what is sentinel and how we can differ from traditional siem ?**
\
\--> Built on Azure
\
no need of physical infrastructure
\
scalable
\
use advance analytics to reduce false positive
\
automated response
\
unified visibility

**key components of Azure sentinel?**
\
\-->
\
Data Connectors - Ingest logs and telemetry from different third party sources
\
Log analytic workspace - Centralized data repository for storing data and quering
\
Analytic rules - Detect threates using built in rules or custom rules
\
Incidents-
\
Workbook - Dashboards
\
Playbook (SOAR) - Automated workflow
\
Threat intelligence
\
Notebook - advance analytics , ML
\
Watchlist
\
Automation rules
\
UEBA (user and entity behavior analytics)

**How Sentinel integrated with Azure entra ID ?**
\
\--> Sentinel uses "Microsoft entra ID" data connector to inject logs from AZure AD.

**What types of data connectors supported in Azure sentinel ?**
\
\-->
\
service to service - real time injection from MS services
\
Agent based - Uses Azure monitor agent (AMA) for syslog / CEF and custom logs
\
API based - rest API or code less connector platform for custom integrations
\
Content Hub solution - Bundled with Dashboard , playbook and analytics rules

**How does sentinel uses Threat intelligence ?**
\
\--> It uses Microsoft defender Threat intelligence or Taxii
\
it provides IOC's - ips , domains , hash

**Analytic rule ?**
\
\--> logic based configuration to trigger alert
\
scheduled Rule - run at regular intervals
\
Microsoft security rule - ingest alerts from other tools
\
fusion rules - use machine learning to detect attack
\
custom rule - build from scratch using KQL

**Aggregation and Normalization :**
\
\--> Aggregation : collecting and consolidating data in one place
\
Normalization : converting collected data into understandable format.

**what is Fusion rules ?**
\
\--> AI driven correlation of multi stage attack across data sources.
\
Fusion is built in machine learning powered correlation engine designed to detect multistage attack.

fusion alerts are rare but highly accurate .

fusion creates high severity incidents.

**What is ASIM (Advance security information model ) - Normalization in sentinel**
\
\--> its Normalization framework
\
transforms vendor specific logs into standardized schema.
\
it acts as Translation layer between raw logs and siem tool.

**how UEBA works ?**
\
user and Entity behavioural analytics is helps to detect insider threats , compromised accounts by analyzing behavioural patterns
\
across user devices ,IP , applications.

**how to integrate devices with sentinel ?**
\
\-->
\
**Azure monitoring agent** - for windows/Linux servers , firewalls and syslog /CEF based devices.

**Azure Arc** - for hybrid environment - on prem devices

**custom connectors** - for unsupported devices - use rest API

**How to integrate using Azure arc ?**
\
\-->

1. enable azure arc from Azure portal
2. install connected machine agent on "on prem server"
3. Generate script from Azure arc and run on prem server.- this registers the device as azure resource
4. Install azure monitoring agent
5. connect it to log analytic workspace linked to sentinel
6. configure Data collection rule(DCR)

**ports used in Linux/firewall (syslog forwarding)**

VM to Log forwarder (syslog-ng) --- 514
\
Log forwarder to AMA agent ----------28330
\
AMA to Azure sentinel ---------------443 HTTPS

**Log forworder tools(rsyslog or syslog.ng) uses syslog protocol**

**#Ports used in Windows integration**\
**Windows server to windows event forwarding - TCP 5985**

**#which access need to integrate defender other than contributer?** \
\--> Security Administrator

**#How service now you will integrate via automation?**\
&#x20;\-->&#x20;

1. Install the Microsoft Sentinel Solution for ServiceNow

* Available via the ServiceNow Store and Microsoft Sentinel Content Hub.
* This app enables bi-directional sync: incidents created in Sentinel appear in ServiceNow, and closing them in ServiceNow updates Sentinel too.

2. Create a Logic App in Azure

* Go to Microsoft Sentinel > Automation > Playbooks.
* Create a new playbook using the ServiceNow connector.
* Use the trigger: “When an incident is created”.

3. Configure the Playbook

* Add actions to:
* Create a new incident in ServiceNow.
* Populate fields like severity, description, and a deep link to the Sentinel incident.
* Optionally, include logic to filter incidents based on severity or tags

## How to investigate scheduled tasks --> Investigate Scheduled Tasks in Windows

1. Use Task Scheduler GUI

* Open Task Scheduler via Start Menu or taskschd.msc.
* Navigate to Task Scheduler Library to view all tasks.
* Review each task’s:
* Triggers (what starts it)
* Actions (what it does)
* Conditions (when it runs)
* History (enable it if disabled)

zero day attack how to check tables in sentinel if you dont know anything \ <sup>**-->**</sup> <sup></sup><sup>.Show tables</sup>
---------------------------------------------------------------------------------------------------------------------------------



# KQL Query KD

***

1. What is the Newspaper Printer's Name?

Ans: Clark Kent

1.

<details>

<summary>Next, you talk with <code>Clark Kent</code>. He seems very distressed about the whole situation. 😓 He tells you he simply printed the article that was emailed to him, as he always does.</summary>

now let's write KQL where role == "Editorial Intern"

```
// Some code

Employees 
| where role == "Editorial Intern" 
```

result will be

Ans :

</details>

1. **When was the Editorial Intern hired at The Valdorian Times?**

   looking at the above KQL result there is column name hire\_date.

Ans :

1. Q **How many total emails has Clark Kent received?**

**Ans :**

```
// KQL

Email 
| where recipient == "clark_kent@valdoriantimes.news"
| count
```

1. What was the subject line of this email ?

Ans : Let's modify previous Kql with date and timestamp

```
// KQL

Email 
| where recipient == "clark_kent@valdoriantimes.news"
| where timestamp between  (datetime(2024-01-31T00:00:00Z) .. datetime(2024-02-01T00:00:00Z))
```

URGENT: Final OpEd Draft Edits (Please publish the following article in tomorrow's paper))

1. **Enter the sender's email address.**

Ans : In previous KQL there is sender column that's answer

1. **What was the name of the .docx file that was sent in this email?**

Ans :- expand the carat located on the left side of the result

1. **Do you think this needs further investigation (yes/no)? Choose wisely 😉**

Ans :- yes

![](https://kc7.troubleshooterclub.in/~gitbook/image?url=https%3A%2F%2F686432324-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F9BKyfpqPfaYj8iMpiZWl%252Fuploads%252FaEusvckZMEcZmL5M8sXa%252Fimage.png%3Falt%3Dmedia%26token%3D5ad428b9-69fb-4e8f-b633-82394dd95dee\&width=768\&dpr=4\&quality=100\&sign=9d0ddbd4\&sv=2)

![](https://kc7.troubleshooterclub.in/~gitbook/image?url=https%3A%2F%2F686432324-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F9BKyfpqPfaYj8iMpiZWl%252Fuploads%252F3kgatZVWUF8Gsdpr0Mhw%252Fimage.png%3Falt%3Dmedia%26token%3Dc365aa0a-538e-4944-a33c-26e86cd349ff\&width=768\&dpr=4\&quality=100\&sign=534ecf87\&sv=2)

![](https://kc7.troubleshooterclub.in/~gitbook/image?url=https%3A%2F%2F686432324-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F9BKyfpqPfaYj8iMpiZWl%252Fuploads%252Foiuv3L57H8hjYmE0G0WT%252Fimage.png%3Falt%3Dmedia%26token%3D3076d9ed-659b-464a-8b3a-7c926b1debac\&width=768\&dpr=4\&quality=100\&sign=1b1ccfac\&sv=2)

![](https://kc7.troubleshooterclub.in/~gitbook/image?url=https%3A%2F%2F686432324-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F9BKyfpqPfaYj8iMpiZWl%252Fuploads%252FiGNKCg815a5eQddkMwTr%252Fimage.png%3Falt%3Dmedia%26token%3Dbc5aa4f1-1af4-4794-89d9-60d101364ef0\&width=300\&dpr=4\&quality=100\&sign=cf6bf0f6\&sv=2)

![](https://kc7.troubleshooterclub.in/~gitbook/image?url=https%3A%2F%2F686432324-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F9BKyfpqPfaYj8iMpiZWl%252Fuploads%252FBnqbPHFYB9ZkFV9GMvQN%252Fimage.png%3Falt%3Dmedia%26token%3D9e480f37-b595-45b1-b5b2-1bc9316d5151\&width=300\&dpr=4\&quality=100\&sign=49a578de\&sv=2)

SecurityIncident\
\| extend ExpandedAlertIds = todynamic(AlertIds)\
\| mv-expand AlertIdValue = ExpandedAlertIds\
\| extend AlertId = tostring(AlertIdValue) // Needed for join\
\| join kind=inner (\
SecurityAlert\
\| where TimeGenerated > ago(30d)\
\| where Entities has "alka.sudarshan" or Entities has "alka sudarshan"\
\| extend SystemAlertId = tostring(SystemAlertId)\
\| project TimeGenerated, AlertName, CompromisedEntity, ExtendedProperties, Entities, SystemAlertId\
) on $left.AlertId == $right.SystemAlertId\
\| project TimeGenerated, AlertName, CompromisedEntity, ExtendedProperties, Entities, SystemAlertId, IncidentNumber

\| take 5 --> it will print 1st entried from the table

\| project-away ---> to remove colomn&#x20;

\| extend eventType == eventCategory   ---> eventCategory will rename as eventType&#x20;

* If we need to create coloum then we can use **#Extend** keyword\
  \| Extend Duration = startTime  - EndTime




# Microsoft Defender for Endpoint

**Windows device onboarding to Microsoft defender-------**

Device need to be joined AZure AD --> need to be connected with Intune --> then it will onboarded to Defender

To join Azure AD
\
search access work or school account

we can directly enroll in MDM intune
\
search access work or school account and select enroll only in device management


# Device onboarding in Defender

Pre-requisite for **Windows device onboarding to Microsoft defender-------**

Device need to be joined AZure AD --> need to be connected with Intune --> then it will onboarded to Defender

To join Azure AD
\
search access work or school account

we can directly enroll in MDM intune
\
search access work or school account and select enroll only in device management

\----------------------------------------------------------

how to integrate windows device with defender ?
\
->

1. Goto Microsoft defender
2. Setting -> Endpoint -> Device management -> onboarding
3. Select operating system
4. Choose your deployment method
5. Download onboarding pkg
6. Run script manaually on device to install pkg as admin / Using Intune we can deploy automatically for large number of devices.
