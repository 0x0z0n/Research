# 0x0z0n.blog 

A technical blog dedicated to documenting my transition from **SOC operations** to **Offensive Security**. This repository houses the source code and markdown content for my personal security journal.

### Content Focus

* **The SOC Diaries:** Insights from 2+ years of defensive operations and incident response.
* **Machine Walkthroughs:** Structured writeups for **HackTheBox** and **TryHackMe**.
* **Windows Internals:** Deep dives into kernel architecture, process injection, and security sub-systems.
* **Red Team Labs:** Documentation of my custom malware development and C2 framework research.

### Built With

* **Theme:** Minimalist, high-readability dark mode for late-night reading.
* **Hosting:** GitHub Pages

### Repository Structure

```bash
├── _posts/
├── _projects/
├── assets/
└── resume

```

# Research


# Scripts


### Logs Parse

[EVTX_CSV_JSON_Logs](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Pirate/Evidence/evtx_files/evt_cj.py "Results")


### Usage Instructions

**For SIEM / ADX / Elastic Ingestion (JSONL):**
```bash
python evt_cj.py -i ~/z0n/z0n/posts/Garfield/Evidence -o ~/z0n/z0n/posts/Garfield/Evidence/Json -f jsonl
```

**For Offline Timeline Explorer / Pandas (CSV):**
```bash
python evt_cj.py -i ~/z0n/z0n/posts/Garfield/Evidence -o ~/z0n/z0n/posts/Garfield/Evidence/CSV -f csv
```

**Run with specific CPU limits and debug logging:**
```bash
python evt_cj.py -i C:\Incident_Logs\ -o C:\Processed_Logs\CSV -f csv -w 4 --debug
```


### Parse PCAP -> TCP Stream -> Yaml 

[PCAP_YAML_TXT](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Pirate/PCAP/pyaml.py "Results")


**Run with specific CPU limits and debug logging:**

```bash
python3 pyaml.py capture.py
```