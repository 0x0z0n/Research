# Severity SLA Matrix — BlueForge SOC Runbooks

This matrix defines the expected response time and minimum required action for each severity level used across all 50 runbook alerts.

## SLA Reference

| Severity | SLA | First Action | Escalation Threshold |
|----------|-----|-------------|----------------------|
| 🔴 CRITICAL | Immediate (< 15 min) | Isolate affected host, page IR team, open P1 ticket | Always escalate — no exceptions |
| 🟠 HIGH | < 1 hour | Investigate, begin containment, escalate if confirmed | Escalate if you cannot contain within 30 min |
| 🟡 MEDIUM | < 4 hours | Investigate, document findings, tune if false positive | Escalate if evidence of active threat found |
| 🟢 LOW | < 24 hours | Review during next shift, close or escalate with evidence | Escalate if pattern emerges across multiple endpoints |

## CRITICAL Alerts in This Runbook (Immediate Response Required)

| # | Alert | MITRE |
|---|-------|-------|
| 02 | Password Spray Attack | T1110.003 |
| 06 | Malicious URL Clicked by User | T1566.002 |
| 07 | Malware Detected by EDR | T1204 |
| 08 | Ransomware Behavioral Detection | T1486 |
| 11 | Lateral Movement via SMB / PsExec | T1021.002 |
| 12 | Pass-the-Hash (PtH) Attack | T1550.002 |
| 14 | DCSync Attack Detected | T1003.006 |
| 15 | Mimikatz / Credential Dumping | T1003.001 |
| 19 | Data Exfiltration via Cloud Storage | T1567.002 |
| 22 | C2 Beaconing Activity | T1071.001 |
| 27 | Volume Shadow Copy Deletion | T1490 |
| 31 | Process Injection Detected | T1055 |
| 32 | LSASS Memory Access | T1003.001 |
| 36 | Windows Event Log Cleared | T1070.001 |
| 40 | Web Shell Uploaded / Detected | T1505.003 |
| 50 | Golden Ticket / Kerberos Ticket Anomaly | T1558.001 |

## Notes

- SLA clock starts from the time the alert appears in the SIEM queue, not from detection time.
- For CRITICAL alerts, phone/Teams call takes precedence over ticket — do not rely on email.
- All alert dispositions (True Positive, False Positive, Benign True Positive) must be documented in the ticket before closing.
- False positives should be documented and reviewed weekly for tuning opportunities.
