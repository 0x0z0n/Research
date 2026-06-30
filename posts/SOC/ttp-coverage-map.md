# TTP Coverage Map — BlueForge

Maps all 50 runbook alerts to MITRE ATT&CK techniques. Use this to identify detection gaps and import `navigator-layer.json` into ATT&CK Navigator for a visual coverage heatmap.

---

## Coverage Summary

| Tactic | Techniques Covered | Alerts |
|--------|-------------------|--------|
| Initial Access | T1078, T1078.002, T1078.004, T1190, T1566.001 | 5 |
| Execution | T1059.001, T1204, T1566.001, T1566.002 | 4 |
| Persistence | T1053.005, T1136.001, T1505.003, T1543.003, T1547.001 | 5 |
| Privilege Escalation | T1078.002, T1548.002 | 2 |
| Defense Evasion | T1027, T1055, T1070.001, T1070.008, T1218, T1562.001, T1562.004 | 7 |
| Credential Access | T1003.001, T1003.006, T1110, T1110.001, T1110.003, T1558.001, T1558.003, T1621 | 9 |
| Discovery | T1046, T1083, T1135 | 3 |
| Lateral Movement | T1021.001, T1021.002, T1550.002 | 3 |
| Collection | T1039, T1114.003, T1530 | 3 |
| Command & Control | T1071, T1071.001, T1071.004, T1090.003 | 4 |
| Exfiltration | T1048, T1567.002 | 2 |
| Impact | T1486, T1490 | 2 |
| **Total** | **35+ unique techniques** | **50 alerts** |

---

## Full TTP Mapping

| Alert # | Alert Name | Tactic | Technique ID | Technique Name |
|---------|-----------|--------|-------------|----------------|
| 01 | Brute Force Login Attempt | Credential Access | T1110.001 | Password Guessing |
| 02 | Password Spray Attack | Credential Access | T1110.003 | Password Spraying |
| 03 | MFA Fatigue | Credential Access | T1621 | MFA Request Generation |
| 04 | Impossible Travel | Initial Access | T1078 | Valid Accounts |
| 05 | Phishing Email Delivered | Initial Access | T1566.001 | Spearphishing Attachment |
| 06 | Malicious URL Clicked | Execution | T1566.002 | Spearphishing Link |
| 07 | Malware Detected by EDR | Execution | T1204 | User Execution |
| 08 | Ransomware Behavioral | Impact | T1486 | Data Encrypted for Impact |
| 09 | Suspicious PowerShell | Execution | T1059.001 | PowerShell |
| 10 | LOLBins Abuse | Defense Evasion | T1218 | System Binary Proxy Execution |
| 11 | Lateral Movement SMB/PsExec | Lateral Movement | T1021.002 | SMB/Windows Admin Shares |
| 12 | Pass-the-Hash | Lateral Movement | T1550.002 | Pass the Hash |
| 13 | Kerberoasting | Credential Access | T1558.003 | Kerberoasting |
| 14 | DCSync Attack | Credential Access | T1003.006 | DCSync |
| 15 | Mimikatz Detected | Credential Access | T1003.001 | LSASS Memory |
| 16 | New Local Admin Created | Persistence | T1136.001 | Local Account |
| 17 | Privileged Login Off-Hours | Initial Access | T1078.002 | Domain Accounts |
| 18 | Suspicious RDP External | Lateral Movement | T1021.001 | Remote Desktop Protocol |
| 19 | Data Exfil Cloud Storage | Exfiltration | T1567.002 | Exfiltration to Cloud Storage |
| 20 | Sensitive Data in Email (DLP) | Exfiltration | T1048 | Exfiltration Over Alternative Protocol |
| 21 | DNS Tunneling | Command & Control | T1071.004 | DNS |
| 22 | C2 Beaconing | Command & Control | T1071.001 | Web Protocols |
| 23 | Tor Usage | Command & Control | T1090.003 | Multi-hop Proxy |
| 24 | Internal Port Scan | Discovery | T1046 | Network Service Scanning |
| 25 | Suspicious Scheduled Task | Persistence | T1053.005 | Scheduled Task |
| 26 | Registry Run Key Modified | Persistence | T1547.001 | Registry Run Keys |
| 27 | Volume Shadow Copy Deletion | Impact | T1490 | Inhibit System Recovery |
| 28 | Defender / AV Disabled | Defense Evasion | T1562.001 | Disable or Modify Tools |
| 29 | Firewall Rules Modified | Defense Evasion | T1562.004 | Disable or Modify System Firewall |
| 30 | Suspicious Service Installed | Persistence | T1543.003 | Windows Service |
| 31 | Process Injection | Defense Evasion | T1055 | Process Injection |
| 32 | LSASS Memory Access | Credential Access | T1003.001 | LSASS Memory |
| 33 | UAC Bypass | Privilege Escalation | T1548.002 | Bypass User Account Control |
| 34 | Encoded/Obfuscated Command | Defense Evasion | T1027 | Obfuscated Files or Information |
| 35 | SMB Share Enumeration | Discovery | T1135 | Network Share Discovery |
| 36 | Event Log Cleared | Defense Evasion | T1070.001 | Clear Windows Event Logs |
| 37 | Email Forwarding Rule | Collection | T1114.003 | Email Forwarding Rule |
| 38 | Azure AD Risky Sign-in | Initial Access | T1078.004 | Cloud Accounts |
| 39 | SQL Injection | Initial Access | T1190 | Exploit Public-Facing Application |
| 40 | Web Shell Uploaded | Persistence | T1505.003 | Web Shell |
| 41 | Suspicious AWS API Calls | Collection | T1530 | Data from Cloud Storage |
| 42 | Office App Spawned Process | Execution | T1566.001 | Spearphishing Attachment |
| 43 | Mass File Access — Insider | Collection | T1039 | Data from Network Shared Drive |
| 44 | USB Device Inserted | Initial Access / Exfil | T1091 | Replication Through Removable Media |
| 45 | DA Account from Non-PAW | Privilege Escalation | T1078.002 | Domain Accounts |
| 46 | Account Lockout Storm | Credential Access | T1110 | Brute Force |
| 47 | Sensitive File Access | Discovery / Collection | T1083 | File and Directory Discovery |
| 48 | Outbound to Malicious IP | Command & Control | T1071 | Application Layer Protocol |
| 49 | Mass Email Deletion | Defense Evasion | T1070.008 | Clear Mailbox Data |
| 50 | Golden Ticket Detected | Credential Access | T1558.001 | Golden Ticket |

---

## Known Detection Gaps (Future Coverage)

Techniques not yet covered in this runbook — planned for future additions:

| Technique | ID | Reason Not Yet Covered |
|-----------|----|-----------------------|
| Supply Chain Compromise | T1195 | Complex to detect without vendor telemetry |
| Firmware Modification | T1542 | Requires hardware-level telemetry |
| Boot Record Modification | T1542.003 | Low frequency in standard enterprise env |
| Container Escape | T1611 | Cloud/container environment specific |
| SAML Token Forgery | T1606.002 | Golden SAML — planned next |

