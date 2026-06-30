# Certification Progression Path — BlueForge

Structured certification roadmap for blue team / SOC career progression from analyst to engineer level.

---

## Current Status

| Certification | Issuer | Status | Obtained |
|---------------|--------|--------|----------|
| CC — Certified in Cybersecurity | ISC2 | ✅ Active | 2024 |
| SC-200 — Security Operations Analyst | Microsoft | ✅ Active | 2024 |
| SAA-C03 — Solutions Architect Associate | AWS | ✅ Active | 2024 |

---

## Next Target — CySA+ CS0-003

**Why:** Validates threat intelligence, vulnerability management, and incident response skills directly aligned with SOC L2/L3 work. Recognized by DoD 8570 for CSSP Analyst roles.

**Exam details:**
- Code: CS0-003
- Questions: 85 (max)
- Time: 165 minutes
- Passing score: 750/900
- Domains: Security Operations (33%), Vulnerability Management (30%), Incident Response (20%), Reporting & Communication (17%)

**Study resources:**
- CompTIA CySA+ Study Guide (Mike Chapple)
- Jason Dion practice exams (Udemy)
- TryHackMe — SOC Level 2 path
- This repo: `01-network-security/` + `02-soc-runbooks/` + `04-mitre-attack/`

---

## 6-Month Roadmap

```
Month 1–3:   CySA+ CS0-003 (active study)
Month 4:     AZ-500 Microsoft Azure Security Engineer
Month 5–6:   PNPT (Practical Network Penetration Tester) — purple team exposure
```

---

## Long-Term Path (12–24 Months)

```
Blue Team Track:
CySA+ → GREM (GIAC Reverse Engineering Malware) → GCFE (GIAC Forensic Examiner)

Detection Engineering Track:
CySA+ → AZ-500 → GDAT (GIAC Defending Advanced Threats)

Red Team Awareness Track:
PNPT → OSCP (OffSec) — for purple team / detection validation work
```

---

## Domain-to-Tool Mapping

| Cert Domain | Tools/Skills in BlueForge |
|-------------|--------------------------|
| Security Operations | Sentinel, MDE, SentinelOne, Cortex XDR |
| Vulnerability Management | Nessus concepts, CVE analysis, patch prioritization |
| Incident Response | NIST 800-61, PICERL, runbooks in `02-soc-runbooks/` |
| Threat Intelligence | MITRE ATT&CK, IOC enrichment, TI feeds |
| SIEM/KQL | All 50 queries in `03-kql-queries/` |

