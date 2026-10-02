# Bottle Out - Wiped Laptop, Gajim XMPP Client, Tactical RMM Agent

> [!success] Solved - 2026-09-19 · 10 of 10 flags
> **No `HTB{}` string exists for this room** - it is question-graded. Sherlock 02 of the event.
> The jailer's identity, the last flag, came from `Microsoft-Windows-WebAuthN%4Operational.evtx`: **Abel Stokes**.

> [!info] Scenario, verbatim
> 2 - Bottle Out
> The story will unfold through the PDFs provided with each challenge's downloadable ZIP.
>
> All characters, locations, and events are fictional. Any resemblance to real people, places, or events is purely coincidental.
>
> RDP into the analysis VM. The credentials are Administrator:Holmes2026!
>
> **Supplied artifact:** `BottleOut.zip` → `Holmes CTF 2026 Sherlock 02.pdf` **and nothing else.** The evidence is not in the download.



## Flags - Answers

| # | Question | Answer | Method |
|:---:|----------------------------------|---------------------------|-------------------------|
| 1 | VPN server address and port | `18.156.81.166:7577` | `spur.log`, `UDPv4 link remote` |
| 2 | CA that issued the VPN client certificate | `NPLN-CA` | `spur.log`, `VERIFY OK: depth=1` |
| 3 | IP assigned by the VPN server | `10.129.175.2` | `spur.log`, `PUSH_REPLY … ifconfig` |
| 4 | Remote management agent and version | `Tactical RMM Agent v.2.11.0` | `tacticalrmm.exe` version resource |
| 5 | Domain the agent communicates with | `api.antimattercommunication.xyz` | `HKLM\SOFTWARE\TacticalRMM\ApiURL` |
| 6 | Agent authentication token (SHA-1) | `98ec588da683c01820232943a6151e8e7772419b` | same key, `Token` |
| 7 | Operation Vanish command | `Remove-Item -LiteralPath C:\Users\spur\Gajim -Recurse -Force` | answer mask + `GAJIM.EXE` prefetch dir 07 |
| 8 | IM account | `spurio9@murknet.htb` | filename `omemo_spurio9@murknet.htb.db` |
| 9 | IM password | `spur999!*` | `Settings.sqlite`, plaintext JSON |
| 10 | Full name of the jailer | `Abel Stokes` | WebAuthN operational event log |



## 0. How the flags were obtained

1. Unpacked `BottleOut.zip` - **one PDF, no artifacts.** Confirmed by full object inventory: 3 pages, 10 JPEGs, 0 attachments, 0 hidden streams.
2. RDP into `BLUEBOX` (Windows Server 2019, `10.129.x.x`, SSH/RDP/WinRM). `DESKTOP-QMTIG5I.E01` sits on the Administrator desktop; `C:\Tools` carries the full Zimmerman suite, FTK Imager, Autopsy, Chainsaw.
3. Mounted the E01 in FTK Imager as **Block Device / Read Only** → `D:`. **Only ~11 GB free on `C:`** - mount, never extract wholesale.
4. Registry gave flags 5 and 6 immediately: loaded the image's `SOFTWARE` hive, read `HKLM\SOFTWARE\TacticalRMM`.
5. `MFTECmd` over `D:\$MFT` (143,530 records, 15,746 free) → CSV, then queried in PowerShell. This is the spine of everything that follows.
6. `PECmd` on `GAJIM.EXE-EDCE70B8.pf` recovered the deleted install path `C:\Users\spur\Gajim` - flag 7's five-character path segment.
7. FTK `[orphan]` tree → the Gajim `UserData` folder → exported `Settings.sqlite`, `Logs.db`, `openpgp.db`, `omemo_spurio9@murknet.htb.db`, `Cert_store`. Flags 8 and 9 fell out of the filenames and one plaintext JSON blob.
8. `EvtxECmd` on `Security.evtx` → 1,362 **event 4688** records with full command lines, spanning the entire operator session. This gave the OpenVPN config and log paths that no longer exist in the MFT.
9. **Autopsy** `$OrphanFiles` recovered `spur.log` (6,201 B) where FTK's tree could not rebuild the parent chain. Flags 1, 2, 3 all sit in that one file.
10. `bstrings` regex sweep over the event logs surfaced a CBOR-encoded WebAuthn credential carrying `displayName: Abel Stokes` - flag 10.



## 1. Shape of the challenge

Not a malware room. There is no implant, no C2 beacon, no obfuscation. The entire difficulty is **recovery from a partial wipe**, and the tooling question is which artifact class survives it.

| Survived the wipe | Did not |
|:------------------------------------------------:|-------------------------------------------------|
| Registry hives (`SOFTWARE`, `SYSTEM`, `SAM`) | Gajim install tree (`C:\Users\spur\Gajim`) |
| Prefetch | OpenVPN user config (`spur.ovpn`) |
| `Security.evtx` (1,850 records, 4688 auditing on) | Gajim message archive contents |
| `Microsoft-Windows-WebAuthN%4Operational.evtx` | Browser profiles (never used) |
| MFT records (partially - parents reused) | `$Recycle.Bin`, VSS |

The operator ran one PowerShell `Remove-Item` against the chat client's directory and nothing else. Everything the questions ask about survives in some form - but four of ten answers required recovering content from files whose directory entries were gone.

`spur` is a four-character username, which is how flag 7's answer mask (`?:\?????\????\?????`) resolved to `C:\Users\spur\Gajim` rather than something under `Program Files`.



## 2. The evidence is on the box, not in the ZIP

Stated plainly because it cost the most time in this room: **`BottleOut.zip` contains only the story PDF.** The challenge page lists it under "Scenario Files - Files to assist you in finding the flag", which reads like an artifact download and is not one.

The PDF's `/Title` metadata leaks the working name: `Holmes CTF 2026 - Sherlock 02 - XMPP Server Forensics`. That is the single most useful thing in the file, and it is not in the rendered text.

The spawned instance is an **analysis VM** you RDP into, with the E01 already staged. FTK Imager here is GUI-only (`FTK Imager.exe`, no `ftkimager.exe` CLI), so the mount step cannot be done from WinRM - and a volume mounted in the RDP session is not guaranteed visible in a separate WinRM session.



## 3. Tactical RMM - flags 4, 5, 6

Everything is in one registry key. Load the image's hive rather than parsing offline:

```powershell
reg load HKLM\IMG_SOFTWARE D:\Windows\System32\config\SOFTWARE
reg query HKLM\IMG_SOFTWARE\TacticalRMM /s
reg unload HKLM\IMG_SOFTWARE
```

```
BaseURL   https://api.antimattercommunication.xyz
ApiURL    api.antimattercommunication.xyz
AgentID   HYlezOqYIjpJGWxfUkEQgUbYzDzReiejGHslxkTH
Token     98ec588da683c01820232943a6151e8e7772419b
AgentPK   4
```

`ApiURL` is the answer to flag 5, not `BaseURL` - the question asks for the FQDN, and `BaseURL` carries the scheme.

`agent.log` (`D:\Program Files\TacticalAgent\agent.log`, 1,608 B) shows the agent service starting repeatedly and failing on:

```
SyncMeshNodeID() getMeshNodeID() exec: "C:\Program Files\Mesh Agent\MeshAgent.exe": file does not exist
```

Tactical RMM pairs with MeshCentral for remote *control*; it was never installed. The operator wanted the scripting and command-execution half without the remote-desktop half.

> [!warning] Flag 4's punctuation is the whole answer
> The version resource on `tacticalrmm.exe` reads `ProductName: Tactical RMM Agent`, `ProductVersion: v2.11.0.0`. The Prefetch filename (`TACTICALAGENT-V2.11.0-WINDOWS`) gives the three-part form. Neither `Tactical RMM Agent v2.11.0` nor `TacticalAgent v2.11.0` is accepted.
> The accepted string is **`Tactical RMM Agent v.2.11.0`** - the answer-format hint is written `v.X.Y.Z` and **the period after the `v` is literal.** Read HTB format hints as exact punctuation, not typography.
>
> Also note: Tactical RMM has **no entry in the Uninstall registry key** - it installs as a bare service. The `SYSTEM` hive's `ControlSet001\Services\tacticalrmm` gives `DisplayName: TacticalRMM Agent Service`, which is the service name and carries no version. Neither authoritative source produces the accepted string on its own.



## 4. Operation Vanish - flag 7

The MFT confirms the command's effect; Prefetch confirms its target.

```powershell
& "C:\Tools\EZ-Tools\net6\PECmd.exe" -f "D:\Windows\Prefetch\GAJIM.EXE-EDCE70B8.pf" | Select-String 'SPUR'
```

Directory 07 in the loaded-directories list is `C:\USERS\SPUR\GAJIM` - five, four, five characters, matching the mask's `?:\?????\????\?????` segment exactly.

```
*********** ************ C:\Users\spur\Gajim ******** ******
     11          12                            8        6
```

`Remove-Item` = 11, `-LiteralPath` = 12, `-Recurse` = 8, `-Force` = 6.

Prefetch also pins the execution window:

| Prefetch entry | Last write (local, UTC-7) |
|:-------------------:|-----------------------------------------------------------|
| `TACTICALAGENT-V2.11.0-WINDOWS-*` | 01:28:55, 01:29:00 |
| `MPCMDRUN.EXE-*` | 05:30:51 |
| `POWERSHELL.EXE-920BBA2A` | 05:37:45 |
| `CMD.EXE-4A81B364` | 05:37:47 |
| `TACTICALRMM.EXE-C27D286F` | 05:59:37 |

PowerShell fires, cmd follows two seconds later. `MpCmdRun.exe` - Defender's CLI - runs seven minutes before. Unconfirmed whether that was an exclusion or a disable; it is worth noting and was not pursued.



## 5. Gajim - flags 8, 9

**Gajim Portable 2.6.0**, not an installed Gajim. That is why nothing appears under `AppData\Roaming`: portable builds keep state in a `UserData` folder beside the binary. The only live trace in the profile root is `.dbus-keyrings`.

Download and execution, from the MFT (UTC):

```
08:43:23  OpenVPN-2.7.6-I001-amd64.msi        → Downloads (5.8 MB, still present)
08:49:50  Gajim-Portable-2.6.0-64bit.exe      → Downloads (159 MB, still present)
08:50:21  installer executed
08:52:23  Gajim-Portable.lnk created in the portable root (deleted)
```

The `UserData` folder, recovered from FTK's `[orphan]` tree:

| File | Size | Content |
|:--------------------:|--------------------------------------|------------------------------------|
| `Settings.sqlite` | 20,480 | account JSON - **flag 9 in plaintext** |
| `Logs.db` | 241,664 | full Gajim 2.x schema, **zero message rows** |
| `omemo_spurio9@murknet.htb.db` | 57,344 | spur's own OMEMO keys only - **filename is flag 8** |
| `openpgp.db` | 32,768 | schema only, no public keys |
| `Cert_store\DL20CMLRBAODGIIY` | 1,980 | XMPP server TLS certificate |

Directories present but **empty**: `Bob`, `Avatars`, `Avatar_icons`, `Downloads`, `Downloads.thumb`, `Theme`, `Plugins*`.

Flag 8 needs no parsing - Gajim names its OMEMO store `omemo_<jid>.db`. Flag 9 is a plaintext string in the settings blob, recoverable with `bstrings` rather than a SQLite client:

```powershell
& "C:\Tools\EZ-Tools\net6\bstrings.exe" -f C:\Temp\Settings.sqlite --ls "password"
```

### The server certificate

Self-signed, `CN=murknet.htb`, with three SANs that describe the infrastructure:

```
groups.murknet.htb     MUC / group chat
command.murknet.htb    not a standard XMPP subdomain
upload.murknet.htb     HTTP File Upload (XEP-0363)
```

`command.murknet.htb` is deliberately named and unexplained by anything else in the image. `murknet.htb` does not resolve from the CTF network and nothing listens on 5222 - the server is scenery, not a target.



## 6. OpenVPN - flags 1, 2, 3

The default paths are clean. `Program Files\OpenVPN\config`, `config-auto`, and `ProgramData\OpenVPN\Log` hold only their stock `README.txt` files. The MFT has no `.ovpn` record for `spur.ovpn` at all - that record was reused.

**Event 4688 supplied the paths.** `EvtxECmd` on `Security.evtx` produced 1,362 process-creation records; filtering for `openvpn`:

```
12:16:59  reg.exe add HKCU\...\Run /v OPENVPN-GUI /d "…\openvpn-gui.exe"
12:18:22  net.exe localgroup "OpenVPN Administrators" "DESKTOP-QMTIG5I\spur" /add
12:18:23  openvpn.exe --log "C:\Users\spur\OpenVPN\log\spur.log" --config "spur.ovpn" …
12:21:10  openvpn.exe --log "C:\Users\spur\OpenVPN\log\spur.log" --config "spur.ovpn" …
```

`spur.log` exists in the MFT as entry **154158**, parent **137132**, 6,201 bytes, unallocated - under `PathUnknown\Directory with ID 0x000217AC-00000001`.

> [!note] FTK could not reach it; Autopsy could
> The parent directory record was reused, so FTK Imager's `[orphan]` tree has no `log` node to click - the file is genuinely absent from its listing between `keyring-25.6.0.dist-info` and `microsoft.system.package.metadata`. Autopsy's `$OrphanFiles` enumerates by MFT entry regardless of whether the parent chain rebuilds, and found it immediately.
> Ingest configuration matters: **Keyword Search only.** The default module set (PhotoRec carving, hash lookup, EXIF) will exhaust the 11 GB of free space on this VM.

The recovered log, abridged:

```
05:21:10 TCP/UDP: Preserving recently used remote address: [AF_INET]18.156.81.166:7577
05:21:10 UDPv4 link remote: [AF_INET]18.156.81.166:7577
05:21:10 VERIFY OK: depth=1, CN=NPLN-CA
05:21:10 VERIFY OK: depth=0, CN=NPLN-VPN-7577
05:21:10 PUSH: Received control message: 'PUSH_REPLY,redirect-gateway def1 bypass-dhcp,
         dhcp-option DNS 8.8.8.8,dhcp-option DNS 1.1.1.1,route-gateway 10.129.175.1,
         topology subnet,ping 10,ping-restart 120,
         ifconfig 10.129.175.2 255.255.255.0,peer-id 1,cipher AES-256-GCM'
05:21:10 MANAGEMENT: >STATE:1788265270,ASSIGN_IP,,10.129.175.2,,,,
05:21:15 Initialization Sequence Completed
05:21:15 MANAGEMENT: >STATE:1788265275,CONNECTED,SUCCESS,10.129.175.2,18.156.81.166,7577,,
05:21:54 SIGTERM[hard,] received, process exiting
```

Depth 1 is the issuing CA (`NPLN-CA`) and answers flag 2; depth 0 is the server certificate (`NPLN-VPN-7577`) and does not.

**The session lasted 44 seconds.** Connected at 05:21:15, killed at 05:21:54. Long enough to reach something, not to do much.



## 7. Abel Stokes - flag 10

Every obvious source is a dead end:

- SAM RID 1002 `V` blob: username `spur`, **full name also `spur`**, `UserPasswordHint: Chaos`
- `ProfileList`: SID ending `-1002`, no name field
- Chrome and Edge profiles: schema-only, never browsed
- Gajim `Logs.db`: zero message rows; `openpgp.db`: zero public keys
- No event 4720 (account creation) in `Security.expected` - the account predates the log

The name is in **`Microsoft-Windows-WebAuthN%4Operational.evtx`** (68 KB), as a CBOR-encoded passkey registration:

```powershell
& "C:\Tools\EZ-Tools\net6\bstrings.exe" `
  -f "D:\Windows\System32\winevt\Logs\Microsoft-Windows-WebAuthN%4Operational.evtx" `
  -m 5 --ls "Stokes"
```

```
!a~&dnamewabel.stokes@hotmail.comkdisplayNamekAbel Stokes
```

The CBOR field pairs are `name: abel.stokes@hotmail.com` and `displayName: Abel Stokes`. The jailer registered a WebAuthn credential against a Microsoft account, and Windows logged the credential's display name. **Nobody wipes the WebAuthN operational log.**

The generalisable move: a regex sweep for `[A-Z][a-z]{2,} [A-Z][a-z]{2,}` across every `.evtx` on the volume. Windows logs are full of two-word phrases, but a real person's name stands out against `Security Group` and `Logon Type`.



## 8. Timeline

All UTC. Laptop timezone is **UTC-7**, so `spur.log`'s `05:21` is `12:21` here.

| UTC | Event | Source |
|:------------:|----------------------------------|--------------|
| 08:33:59 | earliest `Security.evtx` record | EvtxECmd |
| 08:40:31 | `spur` profile created | MFT |
| 08:43:23 | OpenVPN MSI downloaded | MFT |
| 08:49:50 | Gajim Portable downloaded | MFT |
| 08:50:21 | Gajim installer executed | Prefetch |
| 08:52:23 | `Gajim-Portable.lnk` created | MFT |
| 08:57:44 | `openvpnserv.exe` first start | 4688 |
| 12:16:59 | `OPENVPN-GUI` Run-key persistence added | 4688 |
| 12:18:22 | `spur` added to `OpenVPN Administrators` | 4688 |
| 12:18:23 | first `openvpn.exe --config spur.ovpn` | 4688 |
| 12:21:10 | tunnel negotiated, `10.129.175.2` assigned | `spur.log` |
| 12:21:15 | `Initialization Sequence Completed` | `spur.log` |
| 12:21:54 | `SIGTERM`, VPN down | `spur.log` |
| 12:24:43 | Gajim `UserData` subfolders created | MFT |
| 12:36:37 | `Settings.sqlite` last written | MFT |
| 12:37:43 | wipe - `Remove-Item` against `C:\Users\spur\Gajim` | MFT / Prefetch |
| 12:57:04 | latest `Security.evtx` record | EvtxECmd |

Fifteen minutes from profile creation to a fully provisioned operator workstation; four hours of gap; then twenty minutes of activity ending in the wipe.



## 9. Blind alleys - eliminated, do not re-walk

- **`bstrings` string-search over the `.E01` container.** A `--ls "PUSH_REPLY"` sweep across 12.96 GB extracted 3,223,383 strings and returned **zero hits** - while `PUSH_REPLY` sits at offset `0x00000bc0` of a file inside that image. EnCase block compression defeats raw string search. **A null result from string-searching an E01 proves nothing.** 11 minutes wasted, and nearly a wrong conclusion about whether the tunnel ever came up.
- **`Music` and `Links` as flag 7's five-character folder.** Both exist in the live profile and both are exactly five characters. Both contain only stock `desktop.ini` / `.lnk` files created at profile setup. The mask's target was a directory that no longer exists.
- **SAM `Names` subkey via `reg query`.** Returns `Access is denied` even as SYSTEM. Use `RECmd` against the hive file, or read the numbered RID key's `V` value directly.
- **`Bob` as a person.** A directory under Gajim's `UserData` named after a person, in a room whose last question asks for a person's name. It is empty and was empty before imaging.
- **Browser artifacts.** Chrome and Edge profiles both exist with plausible file sizes (`Web Data` 169,984 B, Edge `History` 229 KB) and both are schema-only. Size is not evidence of use.
- **The live XMPP server.** `murknet.htb` does not resolve; nothing listens on 5222/5269 on the analysis VM. The cert SANs describe infrastructure that is not reachable.
- **`reg query Uninstall` for flag 4.** Tactical RMM is not registered there at all.



## 10. Tools & techniques

`FTK Imager` 4.7.3.81 · `Autopsy` 4.23.1 · `MFTECmd` · `PECmd` · `EvtxECmd` · `RECmd` · `bstrings` · `reg load` / `reg query` · `evil-winrm` · `xfreerdp3` · `nmap` · `pdftotext`

**Concepts:** E01 block-device mounting · MFT CSV triage in PowerShell · orphaned-file recovery when the parent record is reused · Prefetch loaded-directory lists as a path oracle for deleted installs · event 4688 command-line auditing as a substitute for missing config files · answer-mask crib as a hard constraint · portable-application state layout · CBOR field extraction from WebAuthn event records



## 11. MITRE ATT&CK

| Technique | ID | Evidence |
|:---------------------------------:|------------------------------------|---------------------------|
| Remote Access Software | T1219 | Tactical RMM Agent v2.11.0 beaconing to `api.antimattercommunication.xyz` |
| Command and Scripting Interpreter: PowerShell | T1059.001 | `Remove-Item -LiteralPath … -Recurse -Force` |
| Indicator Removal: File Deletion | T1070.004 | `C:\Users\spur\Gajim` tree deleted; `$Recycle.Bin` empty |
| Protocol Tunneling | T1572 | OpenVPN 2.7.6 tunnel to `18.156.81.166:7577` |
| Encrypted Channel: Asymmetric Cryptography | T1573.002 | TLSv1.3 control channel, `NPLN-CA`-issued client cert |
| Unsecured Credentials: Credentials In Files | T1552.001 | XMPP password `spur999!*` plaintext in `Settings.sqlite` |
| Application Layer Protocol: Web Protocols | T1071.001 | RMM agent HTTPS to its API domain |
| Account Manipulation | T1098 | `net localgroup "OpenVPN Administrators" spur /add` |
| Data from Local System | T1005 | operator staging on a purpose-built profile |

> [!warning] Honest scope
> IDs assigned without access to the live ATT&CK matrix. **T1005 is the weakest** - nothing in the image shows collection, only provisioning; it is included because the room's premise is a courier workstation, which is inference from the scenario PDF rather than from the artifacts. **T1098 is borderline**: adding a user to `OpenVPN Administrators` is the MSI's own post-install step in some configurations, not necessarily adversary behaviour, though here it ran interactively 90 seconds before the first connection attempt. No technique covers XMPP-over-OMEMO as an operator comms channel; T1573.002 is applied to the VPN, not the chat.



## 12. Detection / blue-team notes

**Detection.** The operator profile is the indicator, not any single tool:

- A user profile created and fully provisioned with a VPN client, an RMM agent, and an encrypted chat client inside **fifteen minutes**.
- Tactical RMM agent installed **without** the paired Mesh Agent - `SyncMeshNodeID()` errors in `agent.log` on every service start are a reliable tell for the scripting-only deployment.
- A portable chat client (`*-Portable-*.exe`) run from `Downloads`, then its entire directory removed by PowerShell in the same session.
- `MpCmdRun.exe` execution minutes before a deletion event.
- An RMM agent whose API domain is not the organisation's RMM tenant. `api.antimattercommunication.xyz` is a durable IOC; `98ec588d…419b` is the agent's own token and identifies this specific host to that tenant.

**On the wipe.** `Remove-Item -Recurse -Force` removes directory entries; it does not touch Prefetch, the event logs, registry hives, or the MFT's record of what once existed. **Every flag in this room survived the wipe** - the operator deleted the data and left the metadata that describes it. Anti-forensics that targets one directory is not anti-forensics.

**For responders.** Where a directory's MFT parent record has been reused, FTK Imager's orphan tree cannot rebuild the path and will silently omit the file. Autopsy's `$OrphanFiles` enumerates by entry number and will find it. Knowing that one difference was the gap between six flags and nine.



## 13. Method notes

- **Read the challenge page before debugging the network.** Eight exchanges went into VPN connectivity - wrong tunnel, no tunnel, then a stale spawn - while the page itself said `RDP into the analysis VM` and gave the credentials. The blocker was never technical.
- **The ZIP is not the evidence.** Reasoning from "~1 MB archive" to "config and log files" was wrong by a wide margin; the megabyte was JPEG story art.
- **Grep large output before proposing new searches.** `Abel Stokes` was present in a paste sent while three further searches were being drafted. Two full exchanges were spent hunting for something already captured. Any output over a few hundred lines gets a regex sweep before it gets read.
- **Never format illustrative examples as an answer table.** A worked example mapping Q1–Q3 onto a *personal* HTB VPN session was rendered as a three-column table and submitted as answers. Examples go in prose.
- **A null string-search result on a compressed container is not evidence of absence.** See §9.
- **Answer-format punctuation is literal.** Flag 4 cost three submissions over a single period character.



## 14. Open items

1. **`difficulty` and `points` unverified** - not read off the Holmes platform page. Confirm and correct.
2. **`solves` omitted** - not read off the platform.
3. **`command.murknet.htb` unexplained.** Present in the server certificate's SANs, not a standard XMPP subdomain, and nothing else in the image references it.
4. **`MpCmdRun.exe` at 12:30:51 UTC not characterised.** Seven minutes before the wipe. Whether it disabled Defender, added an exclusion, or ran a scan was not determined - `Microsoft-Windows-Windows Defender%4Operational.evtx` (1.1 MB) is unread.
5. **`Logs.db` free pages not carved.** 241,664 B is large for an empty Gajim schema. Deleted message rows may sit in freelist pages that a plain strings pass skips.
6. **`spur.log-slack` (1,991 B) unread** - file slack adjacent to the recovered log.
7. **The four-hour gap (08:57 → 12:16 UTC) is unexplained.** The `Store` and `AppXDeploymentServer` operational logs (5.3 MB and 3.2 MB, the two largest on the volume) were never examined.



## Cross-references

- [[HTB-Holmes2026-Silent-Dividend-Electron-Preload-Dropper-Onchain-Key-Oracle]] - Sherlock 01 of the same event; source of the answer-mask-as-constraint technique reused here for flag 7
- [[00_ctf-writeup-standard]] - structure this note conforms to
- [[HTB]]



## Change Log

- 2026-09-19 - Note created. All ten flags solved and recorded; scenario captured verbatim. `difficulty` and `points` marked unverified pending a read of the platform page (§14.1–2).
