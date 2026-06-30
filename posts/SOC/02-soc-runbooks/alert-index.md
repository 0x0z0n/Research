# Alert Index — All 50 Runbook Alerts

Quick reference index. Click the alert name to jump to its full runbook entry.

| # | Alert Name | Severity | Tactic | MITRE ID |
|---|-----------|----------|--------|----------|
| 01 | Brute Force Login Attempt | 🟠 HIGH | Credential Access | T1110.001 |
| 02 | Password Spray Attack | 🔴 CRITICAL | Credential Access | T1110.003 |
| 03 | MFA Fatigue (Multiple Failed MFA) | 🟠 HIGH | Credential Access | T1621 |
| 04 | Impossible Travel Alert | 🟠 HIGH | Initial Access | T1078 |
| 05 | Phishing Email Delivered to Mailbox | 🟠 HIGH | Initial Access | T1566.001 |
| 06 | Malicious URL Clicked by User | 🔴 CRITICAL | Execution | T1566.002 |
| 07 | Malware Detected by EDR | 🔴 CRITICAL | Execution | T1204 |
| 08 | Ransomware Behavioral Detection | 🔴 CRITICAL | Impact | T1486 |
| 09 | Suspicious PowerShell Execution | 🟠 HIGH | Execution | T1059.001 |
| 10 | Living off the Land (LOLBins) Abuse | 🟠 HIGH | Defense Evasion | T1218 |
| 11 | Lateral Movement via SMB / PsExec | 🔴 CRITICAL | Lateral Movement | T1021.002 |
| 12 | Pass-the-Hash (PtH) Attack | 🔴 CRITICAL | Lateral Movement | T1550.002 |
| 13 | Kerberoasting Attack | 🟠 HIGH | Credential Access | T1558.003 |
| 14 | DCSync Attack Detected | 🔴 CRITICAL | Credential Access | T1003.006 |
| 15 | Mimikatz / Credential Dumping Tool | 🔴 CRITICAL | Credential Access | T1003.001 |
| 16 | New Local Administrator Account Created | 🟠 HIGH | Persistence | T1136.001 |
| 17 | Privileged Account Login Outside Hours | 🟡 MEDIUM | Initial Access | T1078.002 |
| 18 | Suspicious RDP from External IP | 🟠 HIGH | Lateral Movement | T1021.001 |
| 19 | Data Exfiltration via Cloud Storage | 🔴 CRITICAL | Exfiltration | T1567.002 |
| 20 | Sensitive Data in Email Attachment (DLP) | 🟠 HIGH | Exfiltration | T1048 |
| 21 | DNS Tunneling Detected | 🟠 HIGH | Command & Control | T1071.004 |
| 22 | C2 Beaconing Activity Detected | 🔴 CRITICAL | Command & Control | T1071.001 |
| 23 | Tor Network Usage Detected | 🟠 HIGH | Command & Control | T1090.003 |
| 24 | Internal Port Scan Detected | 🟡 MEDIUM | Discovery | T1046 |
| 25 | Suspicious Scheduled Task Created | 🟠 HIGH | Persistence | T1053.005 |
| 26 | Registry Run Key Modified | 🟠 HIGH | Persistence | T1547.001 |
| 27 | Volume Shadow Copy Deletion | 🔴 CRITICAL | Impact | T1490 |
| 28 | Windows Defender / AV Disabled | 🟠 HIGH | Defense Evasion | T1562.001 |
| 29 | Firewall Rules Modified | 🟡 MEDIUM | Defense Evasion | T1562.004 |
| 30 | Suspicious New Service Installed | 🟠 HIGH | Persistence | T1543.003 |
| 31 | Process Injection Detected | 🔴 CRITICAL | Defense Evasion | T1055 |
| 32 | LSASS Memory Access (Credential Harvesting) | 🔴 CRITICAL | Credential Access | T1003.001 |
| 33 | UAC Bypass Attempt | 🟠 HIGH | Privilege Escalation | T1548.002 |
| 34 | Encoded / Obfuscated Command Execution | 🟠 HIGH | Defense Evasion | T1027 |
| 35 | Network Share Enumeration (SMB Recon) | 🟡 MEDIUM | Discovery | T1135 |
| 36 | Windows Event Log Cleared | 🔴 CRITICAL | Defense Evasion | T1070.001 |
| 37 | Suspicious Email Forwarding Rule Created | 🟠 HIGH | Collection | T1114.003 |
| 38 | Anomalous Azure AD / Entra ID Sign-in Risk | 🟠 HIGH | Initial Access | T1078.004 |
| 39 | SQL Injection Attack Detected | 🟠 HIGH | Initial Access | T1190 |
| 40 | Web Shell Uploaded / Detected | 🔴 CRITICAL | Persistence | T1505.003 |
| 41 | Suspicious AWS API Calls (CloudTrail) | 🟠 HIGH | Collection | T1530 |
| 42 | Unusual Process Spawned from Office App | 🟠 HIGH | Execution | T1566.001 |
| 43 | Large Number of Files Accessed (Insider) | 🟠 HIGH | Collection | T1039 |
| 44 | USB Mass Storage Device Inserted | 🟡 MEDIUM | Initial Access / Exfil | T1091 |
| 45 | Domain Admin Used from Non-PAW | 🟠 HIGH | Privilege Escalation | T1078.002 |
| 46 | Account Lockout Storm | 🟡 MEDIUM | Credential Access | T1110 |
| 47 | Sensitive File Access by Unusual User | 🟠 HIGH | Discovery / Collection | T1083 |
| 48 | Outbound Traffic to Known Malicious IP | 🟠 HIGH | Command & Control | T1071 |
| 49 | Mass Email Deletion by User | 🟠 HIGH | Defense Evasion | T1070.008 |
| 50 | Golden Ticket / Kerberos Ticket Anomaly | 🔴 CRITICAL | Credential Access | T1558.001 |

---

**Count by Severity:**
- 🔴 CRITICAL: 16 alerts
- 🟠 HIGH: 27 alerts
- 🟡 MEDIUM: 6 alerts
- 🟢 LOW: 1 alert
