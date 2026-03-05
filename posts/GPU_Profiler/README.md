# GPU-Profiler
Managing resources on a hybrid graphics laptop (AMD/Intel + NVIDIA) in a Linux environment can be a bottleneck for cybersecurity tasks. I created this repository because I was facing several challenges

This documentation is designed to be the definitive guide for your GitHub repository, **PowerProfile**. It reflects your professional role as a **SOC Analyst** and your expertise in both **Red and Blue team operations**.

---

# z0n // Power Profile Dashboard

### High-Performance GPU Orchestration & System Telemetry for Kali Linux

**Power Profile** is an aesthetic, high-performance hardware management interface developed to solve the "Idle GPU" problem on hybrid-graphics laptops (AMD/Intel + NVIDIA). By leveraging **PRIME Render Offloading**, this tool allows you to bypass integrated graphics and force-inject the power of your **NVIDIA RTX 5060** into specific cybersecurity workflows—all through a modern, BMW M-Power inspired dashboard.

---

##  The Problem & Vision

As a **SOC Analyst** working with a **Lenovo LOQ** (AMD Radeon 780M + NVIDIA RTX 5060), I identified a significant efficiency gap in standard Linux distributions:

* **NVIDIA Under-utilization:** Critical tasks like hash cracking or VM rendering were defaulting to integrated graphics, leaving the dedicated GPU at 0%.
* **Execution Friction:** Manually typing environment variables for every tool was slow and prone to error.
* **Visual Blindness:** Existing monitors didn't provide the "at-a-glance" telemetry needed during high-load operations.

**Power Profile** provides a unified "Cockpit" to solve these issues, specifically optimized for **X11 environments** and the **Kali Linux** ecosystem.

---

##  Key Features

### 1. Dual-Path Execution Engine

* **Module 01: GUI Binary Mode**
* Designed for standalone applications like **VMware Workstation** or **Burp Suite**.
* Launches processes silently in the background with GPU injection.


* **Module 02: Terminal Override (CLI)**
* Designed for offensive tools like **Hashcat** or **Nmap**.
* Spawns a dedicated terminal window and persists after execution for log analysis.



### 2. Real-Time M-Power Telemetry

* **Circular Analog Gauges:** Features custom-drawn Python/Tkinter gauges inspired by automotive performance clusters.
* **Kernel-Level Monitoring:** Queries `/sys/class/drm/` for AMD and `nvidia-smi` for NVIDIA to provide sub-second accuracy.
* **Dynamic Load Warning:** Gauges shift from Neon Cyan to Warning Crimson when utilization exceeds **85%**.

### 3. Smart History & Favorites

* **Persistence:** Remembers your 10 most-used binaries and commands via `z0n_launcher_favorites.json`.
* **Native Integration:** Uses **Zenity** to invoke the modern OS file manager for binary selection.

---

##  Installation

### Prerequisites

* **Kali Linux** (or any Debian-based rolling release).
* **NVIDIA Proprietary Drivers** (v535+).
* **X11 Display Server** (Wayland is currently unsupported).

### Setup

```bash
# Clone the Core
git clone https://github.com/0x0z0n/PowerProfile.git
cd PowerProfile

# Install UI & System Hooks
pip install customtkinter
sudo apt update && sudo apt install zenity mesa-utils nvtop -y

# Launch Protocol
python3 Powerprofile.py

```

---

##  Technical Core

The engine operates by wrapping execution strings with specific environment variables before passing them to the `/bin/bash` sub-shell:

| Mode | Environment Variables Injected |
| --- | --- |
| **NVIDIA (dGPU)** | `__NV_PRIME_RENDER_OFFLOAD=1` `__GLX_VENDOR_LIBRARY_NAME=nvidia` |
| **Integrated (iGPU)** | Default System Path (No injection) |

> **Note:** For VMware users, this tool automatically works with the `mks.gl.allowBlacklistedDrivers = "TRUE"` preference to ensure 3D acceleration is never dropped.

