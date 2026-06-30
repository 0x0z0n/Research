# Windows Event IDs — SOC Quick Reference

A curated list of the most important Windows Event IDs for SOC analysts. Covers authentication, privilege use, account management, object access, process execution, and system events.

---

## Authentication & Logon Events

| Event ID | Description | Log Source | SOC Relevance |
|----------|-------------|------------|---------------|
| 4624 | Successful account logon | Security | Baseline normal behavior; detect anomalous logons |
| 4625 | Failed account logon | Security | Brute force, password spray detection |
| 4634 | Account logoff | Security | Session duration analysis |
| 4647 | User-initiated logoff | Security | Session tracking |
| 4648 | Logon using explicit credentials | Security | Pass-the-hash, lateral movement indicator |
| 4672 | Special privileges assigned to new logon | Security | Admin logon tracking |
| 4768 | Kerberos TGT requested (AS-REQ) | Security | Normal Kerberos flow baseline |
| 4769 | Kerberos service ticket requested (TGS-REQ) | Security | Kerberoasting when RC4 encryption (0x17) |
| 4771 | Kerberos pre-authentication failed | Security | Brute force against Kerberos |
| 4776 | Domain controller attempted to validate credentials | Security | NTLM authentication events |

### Logon Types Reference

| Type | Name | Common Scenario | Risk |
|------|------|-----------------|------|
| 2 | Interactive | Physical keyboard logon | Low |
| 3 | Network | File share, RPC, net use | Medium |
| 4 | Batch | Scheduled tasks | Low |
| 5 | Service | Service account logon | Low–Medium |
| 7 | Unlock | Workstation unlock | Low |
| 8 | NetworkCleartext | IIS basic auth, WinRM | High (cleartext) |
| 9 | NewCredentials | runas /netonly | Medium |
| 10 | RemoteInteractive | RDP logon | High |
| 11 | CachedInteractive | Offline domain logon | Low |

---

## Account & Group Management

| Event ID | Description | SOC Relevance |
|----------|-------------|---------------|
| 4720 | User account created | Backdoor account detection |
| 4722 | User account enabled | Re-enabling dormant accounts |
| 4723 | Password change attempted | Credential change tracking |
| 4724 | Password reset by admin | Forced reset post-compromise |
| 4725 | User account disabled | Account cleanup or lockdown |
| 4726 | User account deleted | Covering tracks post-attack |
| 4728 | Member added to global security group | Privilege escalation |
| 4732 | Member added to local security group | Local admin group changes |
| 4733 | Member removed from local security group | Cleanup after attack |
| 4740 | Account locked out | Result of brute force or spray |
| 4756 | Member added to universal security group | AD group changes |

---

## Privilege & Object Access

| Event ID | Description | SOC Relevance |
|----------|-------------|---------------|
| 4662 | Operation performed on AD object | DCSync detection (replication rights) |
| 4663 | Attempt to access object | Sensitive file / folder access |
| 4670 | Object permissions changed | ACL modification for persistence |
| 4698 | Scheduled task created | Persistence mechanism |
| 4699 | Scheduled task deleted | Covering tracks |
| 4700 | Scheduled task enabled | Re-activating persistence |
| 4701 | Scheduled task disabled | Disabling legitimate tasks |
| 4702 | Scheduled task updated | Modifying existing task for execution |
| 4703 | Token right adjusted | Privilege adjustment |
| 4704 | User right assigned | New privilege granted |

---

## Process Execution

| Event ID | Description | Log Source | SOC Relevance |
|----------|-------------|------------|---------------|
| 4688 | New process created | Security | Process execution tracking (enable command line logging) |
| 4689 | Process exited | Security | Process duration analysis |
| 4104 | PowerShell script block execution | PowerShell | Detects encoded/obfuscated PS scripts |
| 4103 | PowerShell pipeline execution | PowerShell | Module logging for PS commands |

---

## System & Service Events

| Event ID | Description | SOC Relevance |
|----------|-------------|---------------|
| 7034 | Service crashed unexpectedly | May indicate service-based attacks |
| 7035 | Service sent start/stop control | Service manipulation |
| 7036 | Service entered running/stopped state | Service state changes |
| 7040 | Service start type changed | Persistence — service set to auto-start |
| 7045 | New service installed | Critical — malicious service installation |

---

## Audit Log Events

| Event ID | Description | SOC Relevance |
|----------|-------------|---------------|
| 1102 | Audit log cleared (Security log) | Attacker covering tracks — CRITICAL |
| 104 | System log cleared | Log tampering |
| 4616 | System time changed | Anti-forensics, log manipulation |
| 4719 | System audit policy changed | Disabling audit logging |

---

## Network & Firewall Events

| Event ID | Description | SOC Relevance |
|----------|-------------|---------------|
| 5140 | Network share accessed | SMB enumeration, lateral movement |
| 5142 | Network share created | Attacker-created shares |
| 5145 | Network share object checked | Detailed file share access |
| 4946 | Firewall rule added | C2 port opening |
| 4947 | Firewall rule modified | Firewall tampering |
| 4948 | Firewall rule deleted | Removing defensive rules |
| 6416 | New external device recognized | USB device insertion |

---

## Defender / Security Tool Events

| Event ID | Description | Log Source | SOC Relevance |
|----------|-------------|------------|---------------|
| 5001 | Defender real-time protection disabled | System | AV tamper — CRITICAL |
| 5004 | Defender real-time protection configuration changed | System | Configuration change |
| 5007 | Defender configuration changed | System | Policy modification |
| 5010 | Defender scanning for malware disabled | System | Evasion attempt |
| 1116 | Malware detected | Microsoft-Windows-Windows Defender | Detection event |
| 1117 | Malware action taken | Microsoft-Windows-Windows Defender | Remediation event |

---

## KQL — Query All Critical Event IDs at Once

```kql
// Monitor all high-value Event IDs in one query
SecurityEvent
| where EventID in (
    1102, 104,          // Log clearing
    4624, 4625, 4648,   // Logon events
    4662, 4663,         // Object access
    4698, 4702,         // Scheduled tasks
    4720, 4728, 4732,   // Account/group management
    4740,               // Account lockout
    4769,               // Kerberos
    5001,               // Defender disabled
    5140,               // Network share
    6416,               // USB device
    7045                // New service
)
| project TimeGenerated, EventID, Account, Computer, IpAddress, Activity
| order by TimeGenerated desc
```

