# Missing Record ID Analysis

## What It Is

Every event written to a Windows event log is assigned a sequential **EventRecordID** — a monotonically increasing integer maintained independently per log file. If events are deleted, the log is cleared mid-session, or the file is tampered with, gaps appear in that sequence.

**Identify Missing Record IDs** scans the EventRecordID sequence of every loaded EVTX file and reports any gaps. A gap is forensic evidence that one or more events were removed from the log — either by an attacker covering their tracks, or by a log rotation/clearing policy.

---

## How to Open It

**Analysis → Identify Missing Record IDs** in the menu bar.

The analysis runs instantly against the events already in memory — no re-parse required.

---

## How It Works

For each loaded EVTX file independently:

1. Collect all `EventRecordID` values from the events in that file.
2. Find the minimum and maximum IDs seen — this is the observed range.
3. Compute the full expected set: every integer from min to max.
4. Subtract the observed set — the difference is the set of missing IDs.
5. Compress consecutive missing IDs into ranges (e.g. `1,205–1,208` instead of four individual entries).

The analysis always operates on the **full unfiltered event set**. Active Advanced Filter, Quick Filter, or session filter conditions do not affect the result — a gap hidden behind an active filter is still detected.

Files are analysed independently to prevent false positives when multiple EVTX files are loaded together (each file maintains its own ID sequence starting from 1).

---

## Reading the Results

### No gaps found

```
No gaps found — all Record ID sequences are complete across 3 file(s).
```

All sequences are intact. No evidence of deletion or tampering in the loaded files.

### Gaps detected

```
4 missing Record ID(s) detected across 2 file(s).

Security.evtx
  Range: 1 – 98,432  |  Events: 98,428  |  Expected: 98,432
  Missing IDs: 12,401, 45,882–45,884
```

Each file section shows:

| Field | Meaning |
|-------|---------|
| Range | First and last EventRecordID seen in this file |
| Events | Number of distinct IDs present |
| Expected | Total IDs the range should contain (Range end − Range start + 1) |
| Missing IDs | The specific IDs that are absent, compressed into ranges |

---

## Interpreting Gaps

A gap does not automatically confirm malicious activity. Common legitimate causes:

| Cause | Characteristics |
|-------|----------------|
| Log cleared by administrator | Large single gap spanning recent IDs; a 1104 "Log was cleared" event usually present near the gap |
| Log rotation / max-size wrap | Old low-numbered IDs absent; the file contains only the most recent N events |
| Partial EVTX export | Only a subset of the file was exported — normal in cloud/SIEM exports |
| Corrupted log file | Irregular gaps, possibly mixed with parsing errors |

Indicators that a gap is suspicious:

- Gap appears at a specific time window correlating with other suspicious activity
- Multiple files show gaps in overlapping time windows
- No EID 1104 "Log was cleared" event near the gap
- Gap covers IDs corresponding to a known attack window (cross-reference timestamps from adjacent events)

---

## Both Modes

The analysis works in both **Normal Mode** and **Juggernaut Mode**:

- **Normal Mode** — reads `record_id` from the in-memory event list.
- **Juggernaut Mode** — reads the `record_id` column directly from the Arrow table (fast, no Parquet scan required).

---

## Limitations

- The analysis can only detect gaps within the range of events that were loaded. If the EVTX file begins at ID 50,000 (because earlier events aged out or were cleared before loading), the gap from 1 to 49,999 is not detectable — EventHawk only sees what was parsed.
- EID 1104 (log clear) is not automatically cross-referenced in this dialog. Check the Events table manually for EID 1104 near the timestamps adjacent to any detected gap.
- Record IDs are per-file. Loading `Security.evtx` from two different machines does not produce false positives — each file is analysed independently.
- If `EventRecordID` is absent from an event (can occur with some third-party logging agents), that event is excluded from the sequence check.

---

## Related Docs

- [View Logon Sessions](10c-logon-sessions.md) — correlate suspicious gaps with logon activity
- [Analysis Tabs](09-analysis-tabs.md) — ATT&CK, IOC, and attack-chain analysis
- [Advanced Filter — Time Range](06-advanced-filter.md#time-range) — narrow to the time window around a detected gap
