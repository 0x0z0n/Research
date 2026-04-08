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


# Scripts / Packages


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

### Evidence Collections (Defensive Operations)

[Linux](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/grab_lin_logs.sh "Results")


[Windows](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/grab_win_logs.ps1 "Results")

#### EventHawk Debian Installation Guide (v1.3)

***Source/Author*** (Windows): https://lnkd.in/gNVmsScQ

***Deb Package*** (Debian): 

[First Part](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/EventHunt/eventhawk_part_aa "Results")

[Second Part](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/EventHunt/eventhawk_part_ab "Results")

```bash
cat eventhawk_part_* > eventhawk_1.3_amd64.deb
```

EventHawk is distributed as a **zero-dependency, fully containerized `.deb` package**. You do not need to pre-install Python, Rust, or any GUI frameworks on your host system to run this tool.

***What is Bundled Inside***
When you install this package, it unpacks a completely isolated environment into `/opt/eventhawk/` containing:
* **Python Runtime** (Python 3.10+)
* **Qt GUI Libraries** (PySide6)
* **Rust Parsing Engine** (`pyevtx-rs` binaries)
* **Data Processing Engines** (DuckDB & PyArrow)
* **Sentinel Anomaly Engine**

##### Installation
Because the package contains all its own dependencies, installation is a single command. 

Transfer the `eventhawk_1.3_amd64.deb` file to your target machine and run:
```bash
sudo apt install ./eventhawk_1.3_amd64.deb
```
*(Note: We use `apt` instead of `dpkg -i` because it cleanly registers the local package in the system database and sets up the application menu shortcuts automatically).*

##### Usage
Once installed, the `eventhawk` command is globally available.

**Launch the GUI:**
Search for "EventHawk" in your system's application menu, or run:
```bash
eventhawk gui
```

**Launch the Headless CLI:**
For scripting or terminal-only environments:
```bash
eventhawk parse --help
```

##### Uninstallation
To completely remove the application and its isolated `/opt/` environment:
```bash
sudo apt remove eventhawk
```