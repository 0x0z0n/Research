# Holmes CTF 2026

**Event:** Holmes CTF 2026: *The Reichenbach Directive* (Hack The Box)
**Team:** 0x0z0n - write-ups by `z0n`.


## At a Glance

| Sherlock | Challenge | Focus | Result | Write-up | Solver |
|:--------:|-----------------------|--------------------------|-----------------------------|:-------------------------:|:--------------------------------------------------:|
| **01** | **SilentDividend** | Electron/NSIS reversing, LuaJIT FFI stealer, Web3 phishing, on-chain key oracle | 10/10 | [Write-up](SilentDividend/README.md) | - |
| **02** | **BottleOut** | Wiped-laptop DFIR, MFT/Prefetch/4688 recovery, Gajim XMPP client, Tactical RMM | 10/10 | [Write-up](BottleOut/README.md) | - |
| **03** | **whisper-chain** | XMPP/Prosody recon, OTR-style crypto, Wayback CDX recovery | 8/8 | [Write-up](whisper-chain/README.md) | [`solve.py`](whisper-chain/solve.py) |
| **04** | **PaperGhost** | USB artefacts, SRUM/ESE, Windows Search index recovery | 9/9 | [Write-up](PaperGhost/README.md) | - |
| **05** | **PoisonedBranch** | Software supply chain, Linux auditd, `bkcrack` known-plaintext | `HTB{P0150N3D_BR4NCH_N3V3R_D135}` | [Write-up](PoisonedBranch/README.md) | [`solve.py`](PoisonedBranch/solve.py) |
| **06** | **SilentPassenger** | Android Automotive forensics, MQTT, DEX/protocol reversing | 20/20 | [Write-up](SilentPassenger/README.md) | [`solve.py`](SilentPassenger/solve.py) |
| **07** | **Iron Feather** | PX4 firmware RE, custom KDF + AES-256-GCM, ULog forensics | 17/17 | [Write-up](IronFeather/README.md) | - |
| **08** | **Borrowed Name** | AdaptixC2 beacon traffic decryption, UPN-write privesc, service hijack | 12/12 | [Write-up](BoorowedName/README.md) | - |
| **09** | **LastLight / DIOGENES** | AD live response, memory forensics, Golden Ticket, RBCD | `HTB{3v3n_Th3_F0g_Kn0ws_D10g3n3s}` | [Write-up](LastLight/README.md) | [`solve.py`](LastLight/solve.py) |

Rooms 01, 02, 03, 04, 06, 07 and 08 are **question-graded**: there is no `HTB{}` string, and the result is the number of questions answered. Rooms 05 and 09 end in a final flag.

> **Folder name note:** the Sherlock 08 directory is spelled `BoorowedName` (sic). Links in this README use the real path.



## The Story Behind the Rooms

The Sherlocks are not independent. Several share infrastructure, victims and artefacts, so reading them together reconstructs one campaign against the fictional **DIOGENES** organisation.

```mermaid
flowchart LR
    subgraph Initial_Access
        PG["04 PaperGhost<br/>planted USB, VON BORK implant"]
        PB["05 PoisonedBranch<br/>poisoned internal repo"]
        SD["01 SilentDividend<br/>trojanised Electron app"]
    end
    subgraph Operator_Infrastructure
        BO["02 BottleOut<br/>jailer laptop: VPN, RMM, Gajim"]
        WC["03 whisper-chain<br/>murknet.htb XMPP"]
    end
    subgraph Domain_Compromise
        BN["08 Borrowed Name<br/>network view of the AD attack"]
        LL["09 LastLight<br/>memory and logs view of the same attack"]
    end
    subgraph Physical_Endgame
        IF["07 Iron Feather<br/>drone mission and crash"]
        SP["06 SilentPassenger<br/>compromised car head unit"]
    end

    PG -- "leaked developer credentials<br/>(tainsworth)" --> PB
    BO -. "same murknet.htb XMPP estate" .- WC
    BN -- "same intrusion,<br/>two evidence sets"  LL
```

Links verified between the write-ups:

- **04 → 05.** PaperGhost's Windows Search index leaks the plaintext credentials of developer *Tom Ainsworth*. PoisonedBranch is then Tom's compromised workstation (`LT-TAinsworth`).
- **02 ↔ 03.** BottleOut's recovered Gajim client logs in as `spurio9@murknet.htb`, and its certificate carries the same SAN set (`groups`, `command`, `upload`) that whisper-chain enumerates on the live Prosody server.
- **08 ↔ 09.** Both rooms cover the **same Active Directory intrusion** from different angles. Borrowed Name sees it on the wire (decrypted AdaptixC2 traffic: `afenwick` abuses `userPrincipalName` write access to reset `jreed`'s password, then hijacks a service on `DC02` as `svc_bkup`). LastLight sees it from the DC's memory image and event logs (the matching `4738`/`4723` events, the `svc_bkup` implant, TID `4968`, and the RBCD backdoor). The domain SID prefix `S-1-5-21-2253468260-689643353-167204612` is shared.
- **01, 06, 07.** These end in geographic coordinates or a crash site in central London (SilentDividend's contract decodes to `51.5049, 0.0348`; SilentPassenger's relay car sits at `51.4997, -0.1608`; Iron Feather's drone crashes at `51.5017 N, 0.1621 W`, near Knightsbridge).



## Challenge Overviews

### 01 · [SilentDividend](SilentDividend/README.md)
A malicious NSIS-packaged Electron app (`TrustSettle`) attacks crypto-wallet holders three ways: a LuaJIT FFI backdoor watches `C:\Users\Public\.env` and exfiltrates keys over WinHTTP; a fake Terms-of-Service page tricks the victim into `approve(attacker, MaxUint256)`; and the preload script pulls a decryption key from a Sepolia smart contract to unpack a hidden shell command. A second contract, owned by an address derived via XOR, streams the final ciphertext.
**Techniques:** NSIS/asar static unpacking, Lua VM sandbox tracing, Win32 API recovery via `ffi.cdef`, ROL8-XOR known-plaintext attack, EIP-55 checksum derivation, keccak256 stream-cipher decryption.

### 02 · [BottleOut](BottleOut/README.md)
Not a malware room: the challenge is **recovery from a partial wipe**. A 13.9 GB E01 of the "jailer's" Windows 11 laptop holds a Tactical RMM agent (no Mesh Agent), a portable Gajim client whose install tree was deleted with one PowerShell `Remove-Item`, and an OpenVPN session that lasted 44 seconds. Everything the questions ask about survived somewhere: the registry, Prefetch, event 4688 command lines, orphaned MFT entries, or the WebAuthN operational log.
**Techniques:** FTK Imager block-device mounting, `MFTECmd`/`PECmd`/`EvtxECmd` triage, orphan recovery with Autopsy when FTK's tree fails, Prefetch loaded-directories as a path oracle, CBOR extraction from WebAuthN events.
*The ZIP contains only the story PDF; the evidence lives on the spawned analysis VM.*

### 03 · [whisper-chain](whisper-chain/README.md)
Live reconnaissance of a Prosody XMPP server (`murknet.htb`). A TLS certificate exposes the whole estate; open in-band registration yields an account; a public room leaks four rotated-but-reused passwords; PDF author metadata identifies a user; that user's bookmarks reveal hidden rooms; and the decryptor for eighteen encrypted PubSub operator commands exists only in a dead threat-intel article's Wayback capture, under two keys split across a rotation.
**Techniques:** XEP-0077 registration, MUC scraping, XEP-0048 bookmarks, PubSub, Wayback CDX API, PBKDF2 (120,000 iterations) with OpenSSL AES-CBC. XMPP was hand-rolled over a raw socket (see the write-up for why).

### 04 · [PaperGhost](PaperGhost/README.md)
Junior analyst Clara Voss runs an "update package" from a USB drive left by a contractor posing as IT support. The VON BORK implant records audio and video, then exfiltrates about 172 MB to a relay. The final answer comes from a forgotten side channel: `Windows.edb` cached an `AutoSummary` snippet of a contractor PDF containing a developer's plaintext credentials.
**Techniques:** USBSTOR/WPDBUSENUM history, UserAssist ROT13/FILETIME decoding, JumpList OLE streams, SRUM (`SRUDB.dat`) via `dissect.esedb`, CapabilityAccessManager consent-store timeline, Windows Search index recovery.

### 05 · [PoisonedBranch](PoisonedBranch/README.md)
A backdoored internal repo (`diogenes-ticket-parser`) hides a Meterpreter/Mettle implant by XOR-ing it against a bundled JPEG; running the script reassembles it and calls home. The victim's **auditd log records the attacker's own hostname, operator cookie and path-traversal payload verbatim**, so the payload can be replayed against the attacker's file server to steal their SSH key, log in, and crack the encrypted `LOOT.zip`.
**Techniques:** Python source XOR extraction, auditd command reconstruction, path-traversal replay with `curl --resolve`, ZipCrypto known-plaintext cracking with `bkcrack`.

### 06 · [SilentPassenger](SilentPassenger/README.md)
Forensics of a TOPWAY/Allwinner T3 Android Automotive head unit. The OEM OTA client `TWCore` subscribes to a hardcoded MQTT topic; a retained "install silently" message unwraps four nested payloads ending in a proxy module. Impersonating that module on its C2 channel exposes the operator's HTTP traffic, which registers the car as a relay and states where it is parked. About half of the 20 answers require talking to live services.
**Techniques:** firmware unpacking, priv-app and DEX analysis, custom RSA/AES protocol reversing, binary packet framing, MQTT retained-message abuse.

### 07 · [Iron Feather](IronFeather/README.md)
A PX4 flight-controller binary plus an encrypted `dataman` mission store and encrypted `.ulg` flight log, all in a custom `PX4DMENC` container (AES-256-GCM). The key comes from a 384-round mixing routine feeding PBKDF2-HMAC-SHA256, and it is recovered by running the KDF directly via `dlopen()`. The decrypted data shows a 24-waypoint mission with a payload drop, followed by a forged `MAV_CMD_INJECT_FAILURE` that kills the motors and crashes the drone near Knightsbridge.
**Techniques:** stripped PIE reversing, KDF extraction by execution rather than reimplementation, GCM/AAD handling, `pyulog` flight forensics, GPS/geospatial analysis.

### 08 · [Borrowed Name](BorrowedName/README.md) *(insane, 1000 pts)*
A lure FAT32 image sideloads an **AdaptixC2** beacon; a PCAP and an NTLM event log are the rest of the evidence. The pivotal fact: **the beacon carries the key that decrypts its own traffic, stored immediately after the ciphertext it unlocks** (16 bytes at file offset `0x15904`). With that, the entire operator session decrypts: recon, a DACL read, `internal_monologue` NTLM theft, the `ResetNightmare` BOF (CVE-2026-27912) abusing `userPrincipalName` writes, `make_token` (logon type 9), and a service-hijack lateral move to the DC.
**Techniques:** reading the framework's source for container layout, per-structure endianness verification, RC4 stream reassembly (chunked encoding), BOF extraction and hashing, cross-correlation of PCAP and NTLM event 4021 by PID.

### 09 · [LastLight / DIOGENES](LastLight/README.md)
A 3.2 GB memory image of a domain controller, Sysmon and Security logs, and an NTDS backup rebuild the full intrusion: UPN-spoofing password reset, PsExec-style service implant, theft of a forest-root admin's access token, DCSync, a forged Golden Ticket, and an RBCD backdoor on the DC itself. The final flag is unlocked by submitting the two logon sessions behind the password attack.
**Techniques:** Volatility 3 kernel object walking (`_TOKEN`, `_ETHREAD`), offline ccache carving and PAC decryption with `impacket`, NTDS.dit extraction via `dissect.esedb`, Security/Sysmon correlation.



## Recurring Themes

| Theme | Where it appeared |
|-----------------------------------------|--------------------------------------------------------------------------------------|
| **The key ships with the ciphertext** | 01 (key fetched from an on-chain contract), 07 (KDF is runnable in the binary), 08 (key 16 bytes after the encrypted profile) |
| **Known-plaintext and keystream reuse** | 01 (ROL8-XOR), 05 (ZipCrypto/`bkcrack`), 08 (RC4 reused keystream) |
| **Metadata outlives deletion** | 02 (Prefetch, MFT, 4688 survive the wipe), 03 (PDF Info dictionaries), 04 (search-index cache) |
| **Logs record the attacker's own tradecraft** | 02 (event 4688), 05 (auditd), 09 (4738/4723/5136 and Sysmon 13) |
| **Read the tool's source, not just the bytes** | 03 (hand-rolled XMPP), 08 (AdaptixC2 wire format), 07 (PX4 container) |
| **Evidence may not be in the ZIP** | 02 and 03 ship only a story PDF; the evidence is on the spawned VM or remote host |



## Tooling Used

| Area | Tools |
|------------------------------------|----------------------------------------------------------------------|
| Windows disk/artefact forensics | FTK Imager, Autopsy, `MFTECmd`, `PECmd`, `EvtxECmd`, `RECmd`, `bstrings`, `regipy`, `LnkParse3`, `olefile`, `dissect.esedb` |
| Memory / Active Directory | Volatility 3, `impacket`, `dissect.eventlog`, `python-evtx` |
| Reversing | `objdump`/`readelf`, `dlopen()` harnesses, `unicorn`, `jadx`, `pefile`, 7-Zip/asar unpackers, Lua 5.1 |
| Network / protocol | `scapy` (PCAP stream reassembly), `openssl s_client`, `nmap`, raw-socket XMPP, `paho-mqtt`, `pyfatfs` |
| Crypto / cracking | `pycryptodome`, `bkcrack`, OpenSSL |
| Flight and geo | `pyulog`, `pymap3d` |



## Repository Structure

```
.
├── README.md               
├── SilentDividend/            Sherlock 01
├── BottleOut/                 Sherlock 02
├── whisper-chain/             Sherlock 03   
├── PaperGhost/                Sherlock 04
├── PoisonedBranch/            Sherlock 05   
├── SilentPassenger/           Sherlock 06  
├── IronFeather/               Sherlock 07
├── BoorowedName/              Sherlock 08   
└── LastLight/                 Sherlock 09   
```

Each challenge directory contains:

- `README.md`: the standalone write-up with methodology, key commands, and lessons learned.
- `solve.py`: a standalone solver, where one was written (01, 02, 04, 07 and 08 are documented inline instead).
- `screenshots/`: evidence captured during analysis, where applicable.



## Disclaimer

All scenarios, characters and organisations are fictional and belong to the Hack The Box Holmes CTF 2026 event. The content here is published for educational purposes. Malware samples referenced in the write-ups were analysed statically or in isolated environments and are not included.