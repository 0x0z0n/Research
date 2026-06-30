# Threat Intelligence Feeds & IOC Enrichment Sources

Quick reference for all TI sources used during alert triage and threat hunting in BlueForge runbooks.

---

## Free IOC Lookup Tools

| Tool | URL | Use For | Input Types |
|------|-----|---------|-------------|
| VirusTotal | virustotal.com | Hash, IP, domain, URL reputation | MD5, SHA1, SHA256, IP, domain, URL |
| AbuseIPDB | abuseipdb.com | IP abuse reports and reputation | IP address |
| URLScan.io | urlscan.io | URL detonation and screenshot | URL |
| Shodan | shodan.io | Internet-exposed device/service info | IP address, hostname |
| OTX AlienVault | otx.alienvault.com | Full IOC context — pulses, threat actors | Hash, IP, domain, URL, CVE |
| Hybrid Analysis | hybrid-analysis.com | Malware sandbox (static + dynamic) | File, URL, hash |
| AnyRun | any.run | Interactive malware sandbox | File, URL |
| PassiveDNS | passivedns.mnemonic.no | Historical DNS resolutions | Domain, IP |
| Robtex | robtex.com | DNS, BGP, IP/domain relationships | IP, domain |
| Talos Intelligence | talosintelligence.com | Cisco Talos reputation data | IP, domain, email sender |
| MXToolbox | mxtoolbox.com | Email header analysis, blacklist check | Email header, IP, domain |
| Browserling | browserling.com | Safe browser-in-browser URL testing | URL |
| URLVoid | urlvoid.com | URL reputation across 30+ engines | URL |
| ThreatFox | threatfox.abuse.ch | Recent IOC database | Hash, IP, domain, URL |
| MalwareBazaar | bazaar.abuse.ch | Malware sample database | Hash, file |
| URLhaus | urlhaus.abuse.ch | Malicious URL database | URL, domain |
| Feodo Tracker | feodotracker.abuse.ch | C2 botnet tracker (Emotet, etc.) | IP, domain |

---

## Email Header Analysis

When investigating phishing alerts (#05), check these fields manually:

| Header Field | What to Check |
|-------------|---------------|
| `Received:` chain | Trace the path — does it match the claimed sender domain? |
| `Return-Path:` | Should match `From:` domain — mismatch = spoofing indicator |
| `SPF` result | `pass` is good; `fail` or `softfail` = suspicious |
| `DKIM` result | `pass` = signature valid; `fail` = tampered or spoofed |
| `DMARC` result | `pass` = aligned; `fail` + `reject` policy = blocked by good systems |
| `X-Originating-IP` | Actual sender IP — look up on AbuseIPDB |
| `Message-ID` | Random-looking IDs are fine; patterned IDs can indicate bulk send tools |
| `User-Agent` | May reveal the mail client used — legitimate vs bulk mailer |

---

## MITRE ATT&CK Threat Intelligence Mapping

| Source | Coverage | Best Used For |
|--------|----------|---------------|
| MITRE ATT&CK | Techniques, groups, software | Mapping IOCs to known threat actors |
| CISA Known Exploited Vulnerabilities | CVEs actively exploited | Patch prioritization |
| Google TAG | APT campaigns | Nation-state threat intel |
| Mandiant / Google Cloud Threat Intel | APT groups, malware families | Advanced threat research |
| RecordedFuture (paid) | Real-time TI | Enterprise threat intel platform |
| CrowdStrike Adversary Intel (paid) | Named adversaries | Enterprise threat actor tracking |

---

## Sandbox Analysis Checklist

When submitting a file or URL to AnyRun / Hybrid Analysis, check for:

- [ ] Network connections — any C2 callbacks? What IPs/domains?
- [ ] Process tree — what child processes were spawned?
- [ ] File drops — what files were created on disk? Where?
- [ ] Registry changes — any Run key modifications?
- [ ] Persistence mechanisms — scheduled tasks, services created?
- [ ] MITRE ATT&CK tags — what techniques did the sandbox detect?
- [ ] Verdict — Malicious / Suspicious / Clean?
- [ ] IOCs extracted — hashes, IPs, domains, mutex names

---

## IOC Types Reference

| IOC Type | Example | Where Found |
|----------|---------|-------------|
| MD5 hash | `d41d8cd98f00b204e9800998ecf8427e` | File metadata, EDR alerts |
| SHA256 hash | `e3b0c44298fc...` | EDR alerts, sandbox reports |
| IP address | `185.220.101.45` | Firewall logs, proxy logs, EDR |
| Domain | `evil-c2-domain.xyz` | DNS logs, proxy logs |
| URL | `http://evil.xyz/payload.exe` | Proxy logs, email click logs |
| Email address | `attacker@phish-domain.com` | Email header, phishing reports |
| Mutex | `Global\MicrosoftEdge` | Sandbox reports, memory forensics |
| Registry key | `HKCU\Software\Run\malware` | Sysmon Event ID 13, EDR |
| File path | `C:\Users\Public\malware.exe` | EDR process events, file events |
| User-agent | `Mozilla/5.0 (bot-pattern)` | Proxy logs, web server logs |
| ASN | `AS4134` | Network flow logs |
| Certificate hash | SHA1 thumbprint | TLS inspection logs |

