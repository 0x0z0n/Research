# SOC Tools Reference — BlueForge

Practical reference guide for every tool used in BlueForge runbooks. Covers what each tool does, where to find key information in it, and the specific fields/views relevant to alert triage.

---

## Microsoft Sentinel

**What it is:** Cloud-native SIEM and SOAR platform. Primary detection and investigation tool.

**Key areas:**
| Area | Path | Use |
|------|------|-----|
| Incidents | Sentinel → Incidents | Triage queue — all fired alerts |
| Logs | Sentinel → Logs | Run KQL queries ad-hoc |
| Analytics Rules | Sentinel → Analytics | Scheduled detection queries |
| Hunting | Sentinel → Hunting | Proactive threat hunting queries |
| Workbooks | Sentinel → Workbooks | Visual dashboards per use case |
| Threat Intelligence | Sentinel → Threat Intelligence | STIX/TAXII TI feed management |
| Watchlists | Sentinel → Watchlists | Reference lists for KQL (IP allowlists, DA accounts, PAW hosts) |

**Most-used tables in KQL:**
```
SecurityEvent          — Windows Security log events
SigninLogs             — Azure AD / Entra ID authentication
AzureActivity          — Azure resource operations
DeviceProcessEvents    — MDE process creation (Defender XDR)
DeviceNetworkEvents    — MDE network connections
DeviceFileEvents       — MDE file operations
DeviceRegistryEvents   — MDE registry changes
DeviceAlertEvents      — MDE alerts
EmailEvents            — Defender for Office 365
OfficeActivity         — O365 audit logs
CloudAppEvents         — MCAS / Defender for Cloud Apps
DnsEvents              — DNS query logs
AWSCloudTrail          — AWS API audit logs
```

---

## Microsoft Defender for Endpoint (MDE)

**What it is:** EDR platform. Provides endpoint telemetry, behavioral detection, and isolation capability.

**Key actions during incidents:**
| Action | Where | When to Use |
|--------|-------|-------------|
| Isolate device | Device page → Device actions → Isolate device | Confirmed malware, active C2, ransomware |
| Collect investigation package | Device page → Device actions | Full forensic artifact collection |
| Run antivirus scan | Device page → Device actions | Verify after containment |
| Stop and quarantine file | Alert → Evidence → File → Stop and quarantine | Block malicious file from running |
| Add indicator | Indicators → File/IP/URL/Certificate | Block known bad IOCs environment-wide |
| Live response | Device page → Live response | Remote shell for deep investigation |

**Process tree:** Alert → Alert story → select a process → right-click for context. Shows parent/child relationships clearly.

---

## SentinelOne

**What it is:** EDR with AI-behavioral detection. Used alongside or instead of MDE.

**Key areas:**
| Feature | Use |
|---------|-----|
| Threats | Alert triage queue — severity, status, storyline |
| Storyline | Process tree with full kill-chain visualization |
| Deep Visibility | Raw telemetry query (similar to MDE Advanced Hunting) |
| Network Quarantine | Isolate endpoint while keeping SentinelOne cloud comms |
| Remote Shell | Remote access for investigation |
| Rollback | Undo ransomware file changes (Windows VSS-based) |

**SentinelOne Deep Visibility query example:**
```
EventType = "Process Creation" AND TgtProcName = "powershell.exe" 
AND TgtProcCmdLine Contains "-enc"
```

---

## Cortex XDR (Palo Alto)

**What it is:** XDR platform combining endpoint, network, and cloud telemetry.

**Key areas:**
| Area | Use |
|------|-----|
| Incidents | Correlated alert groups with causality analysis |
| Causality Analysis | Root cause tree — identifies patient zero chain |
| Response Actions | Isolate, terminate process, block file |
| Threat Hunting | XQL (XDR Query Language) for raw telemetry |
| Behavioral Threat Protection | BIOC rules — behavioral detection |

---

## Zscaler

**What it is:** Cloud proxy / SSE platform. All web traffic routes through it.

**Key investigation steps in Zscaler:**
- **Log investigation:** Zscaler Admin → Analytics → Web Insights
- **URL lookup:** Search by user, URL, or IP to find click activity
- **Block URL:** Policy → URL & Cloud App Control → add to block list
- **SSL inspection:** Verify TLS inspection is enabled for suspicious categories
- **Bandwidth threshold:** Check for large upload events (exfiltration indicator)

---

## Awake Security (NDR)

**What it is:** Network Detection & Response. Analyzes encrypted traffic using ML.

**Key use cases in SOC:**
- Detecting C2 beaconing in encrypted HTTPS traffic
- Identifying lateral movement across internal segments
- Flagging unusual data volumes between endpoints
- Detecting reconnaissance (port scans, SMB enumeration)

**Investigation flow:** Alerts → select device → Activity timeline → Connections tab → sort by bytes sent

---

## Armis (OT/IoT)

**What it is:** Passive device discovery and monitoring for OT, IoT, and unmanaged devices.

**Key use cases:**
- Identify unmanaged/shadow devices on the network
- Detect OT protocol anomalies (Modbus, DNP3, BACnet)
- Risk scoring for devices that cannot run EDR agents
- Alert on device behavior changes (e.g., IoT device initiating outbound connections)

---

## Forensics & Investigation Tools

| Tool | Use | Key Command |
|------|-----|-------------|
| CyberChef | Decode base64, deobfuscate, convert | Use "Magic" recipe for unknown encoding |
| Wireshark | Packet capture analysis | Filter: `tcp.stream eq N` to follow a session |
| Volatility | Memory forensics | `vol.py -f mem.dmp pslist` — list processes |
| Velociraptor | Remote artifact collection | VQL queries for live system data |
| Sysinternals Autoruns | Persistence discovery | Shows all auto-start locations |
| Sysinternals Process Monitor | Real-time process/file/registry | Filter by process name or path |

---

## Quick Reference — Where to Look for What

| You need to find... | Look here |
|--------------------|-----------|
| Which process made a network connection | MDE DeviceNetworkEvents → InitiatingProcessFileName |
| What a PowerShell script actually did | Windows Event ID 4104 (Script Block Logging) |
| Who created a scheduled task | SecurityEvent 4698 → SubjectUserName |
| Whether a file hash is malicious | VirusTotal → Hash search |
| What a suspicious IP is | AbuseIPDB + Shodan + PassiveDNS |
| Whether a phishing email was clicked | Defender for O365 → URL click events |
| Whether lateral movement happened | MDE DeviceNetworkEvents → filter RemotePort 445, 3389 |
| Whether data left the org | Zscaler Web Insights → BytesSent > threshold |
| Whether credentials were dumped | MDE → LSASS access events → OpenProcessApiCall |
| When a user last authenticated | SigninLogs → UserPrincipalName filter |

