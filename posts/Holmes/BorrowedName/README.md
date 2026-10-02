
# Holmes CTF 2026: Borrowed Name

# Borrowed Name - AdaptixC2 Beacon Traffic Decryption, UPN-Write Privesc, Service Hijack

> [!success] Solved - 2026-09-20 05:32 (platform clock) · 12 of 12 flags
> **No `HTB{}` string exists for this room** - it is question-graded. Sherlock 08 of the event · insane · 1000 points.
> The room is one pivot repeated at two scales: **the beacon binary carries the key that decrypts its own C2 traffic, stored immediately after the ciphertext it unlocks.** Recover 16 bytes at file offset `0x15904` and the entire intrusion reads as plaintext.

> [!info] Scenario, verbatim
> SCENARIO NAME
> 8 - Borrowed Name
> The story will unfold through the PDFs provided with each challenge's downloadable ZIP.
>
> All characters, locations, and events are fictional. Any resemblance to real people, places, or events is purely coincidental.
>
> **Supplied artifact:** `BorrowedName.zip` -> `danger.txt`, `danger.zip` (password-protected), `Holmes CTF 2026 - Sherlock 08 - DIOGENES Active Directory Incident.pdf`. The inner archive holds `capture.pcapng`, `Q3_Salary_Review.img`, and `C/Windows/System32/winevt/logs/Microsoft-Windows-NTLM%4Operational.evtx`. The evidence is in the download.



## Flags - Answers

| # | Question | Answer | Method |
|---|-----------------------------------------------|---------------------------------------|------------------------------|
| 1 | C2 used for this attack | `adaptix` | agent watermark `be4c0149` + `13ConnectorHTTP` RTTI + stock BeaconHTTP defaults |
| 2 | SessionKey:EncryptionKey | `53fc4c03c7b461befe5dcb268e3d9208:4580221ac3fe51be1797524a048e552d` | key at `0x15904`; SessionKey from the decrypted beat |
| 3 | CVE used for privilege escalation | `CVE-2026-27912` | decrypted BOF output, `[*] Action: ResetNightmare` |
| 4 | md5sum of the custom BOF | `583236cc3ef2488fb133385bcd75825e` | `resetnightmare` object, 70,169 B, lifted from the tasking stream |
| 5 | ObjectSID of the writable Property | `S-1-5-21-2253468260-689643353-167204612-1125` | DACL BOF, ACE #4, `ObjectAceType 28630ebb-…` = `userPrincipalName` |
| 6 | Named attack for the password, and when | `internal_monologue:2026-09-09 20:44:11` | NTLM evtx 4021 + HTTP `Date` on the tasking response |
| 7 | Credentials used to perform the attack | `afenwick:*Seash5lls*` | `/upnpass:` argument to the `resetnightmare` BOF |
| 8 | Targeted user and resulting password | `jreed:Aigohng8vai0seish4zi` | same BOF's decrypted output |
| 9 | New token logon type after privesc | `9` | `make_token` BOF output, `DIOCORE\jreed (logon: 9)` |
| 10 | Path the new agent was uploaded to | `\\192.168.56.11\ADMIN$\svc_bkup` | lateral-movement BOF argument, `dc02` -> `192.168.56.11` |
| 11 | Service group used to start the agent | `defragsvc` | original path `svchost.exe -k defragsvc` |
| 12 | New BeaconID:SessionKey | `ddc68fa7:289122cf1ec91c67eb89c30642adfea4` | second beacon's `X-Beacon-Id`, same EncryptKey |

All timestamps are **UTC**. The host is `gmt_offset 0xf8` = UTC−8; the grader wanted UTC.



## 0. How the flags were obtained

1. Unpacked the outer ZIP, read the inner-archive password from `danger.txt`, extracted three artifacts.
2. Mounted `Q3_Salary_Review.img` with `pyfatfs` at offset `1048576` (MBR partition 1, type `0x0c`). Six files: a lure `README.TXT`, a decoy `TEMP.PDF`, `Salary_Review_Q3_2026.pdf.lnk` pointing at `docviewer.exe`, `VERSION.DLL` exporting `RunPayload`, and `winupdate.exe`.
3. Identified `winupdate.exe` as an **AdaptixC2 `beacon` agent** - `13ConnectorHTTP` / `9Connector` RTTI strings in `.rdata`, and the pcap's URI set, header name and User-Agent matching the framework's stock `BeaconHTTP` listener defaults exactly.
4. Cloned the AdaptixC2 source to read the wire format rather than guess it. `AgentConfig.cpp` gives the profile layout: **`[u32 size][RC4 ciphertext][16-byte key]`, with the key stored immediately after the blob it decrypts.**
5. Found the blob at file offset `0x15800`, 276 bytes total. Key = `4580221ac3fe51be1797524a048e552d`. Decrypted profile: server `192.168.56.1`, port `8818`, sleep 4 s, jitter 0.
6. Base64-decoded the `X-Beacon-Id` header, RC4'd it with that key -> the registration beat: `agent_id 58debcbb`, **SessionKey `53fc4c03…`**, `acp 1252`, `oemcp 437`, `gmt −8`, `pid 6040`, `build 26200`, `core.diogenes.htb`.
7. Reassembled both TCP streams, stripped the listener's page template (26-byte prefix, 21-byte suffix) from every response, and RC4'd every body with the SessionKey. **The entire operator session decrypts.**
8. Parsed the tasking stream into 17 `COMMAND_EXEC_BOF` records, dumped 13 distinct BOF objects and their arguments, and hashed them.
9. Read the BOF output stream end to end: recon -> DACL enumeration -> `internal_monologue` -> `resetnightmare` -> `make_token` -> service hijack.
10. Correlated the credential-theft moment against `Microsoft-Windows-NTLM%4Operational.evtx` event 4021 - `ProcessName winupdate`, `ProcessPID 0x1798` (6040, matching the beat) - for flag 6's timestamp.
11. Decoded the second beacon's `X-Beacon-Id` from `192.168.56.11` with the same EncryptKey -> flag 12.



## 1. Shape of the challenge

Three artifacts, one of which is load-bearing and two of which are supporting.

| Artifact | Role |
|:------------------------:|----------------------------------------------|
| `Q3_Salary_Review.img` | supplies the **key**. Nothing else in it is asked about. |
| `capture.pcapng` | supplies **ten of twelve answers**, but only after decryption. |
| `NTLM%4Operational.evtx` | supplies **one timestamp**, and nothing else. |

The structural fact: **this is not a crypto challenge, it is a "read the tool's source" challenge.** RC4 with a 16-byte key is trivial once you have the key, and the key is in cleartext 16 bytes past the ciphertext. What gates the room is knowing the container layout, the beat field order, the response wrapper offsets and the tasking format - all of which are in the framework's public repository and none of which are guessable from the bytes.

This is the same structure as Silent Dividend and Iron Feather, stated for the third time in one event: **protection was applied to the data, and the thing that unlocks it shipped alongside.** See the MOC, §3.3.



## 2. The lure

```
MBR, partition 1, type 0x0c (FAT32 LBA), start sector 2048

docviewer.exe                  18,432  aca111935d339b17544ead3e8c2c8831
VERSION.DLL                    14,848  6e787589a69ce783b0380b0de86a2d68   exports RunPayload
winupdate.exe                  90,624  b1c8c95d3bfa22780076084377584739
Salary_Review_Q3_2026.pdf.lnk     302  9203f64685b7007b4f80070c55fc096d
README.TXT                        217  cd0068ff74c1a1c573c1300622d0b15b
TEMP.PDF                          625  4edcb91dc1b02f67a79c7ad43ff29a96
```

A mounted-image lure with a PDF-named LNK, a signed-looking `docviewer.exe`, and `VERSION.DLL` sideloaded beside it. `VERSION.DLL` exports a single function, `RunPayload`, and the only readable strings in `docviewer.exe` are `\winupdate.exe` and `winupdate.exe`. Classic DLL-search-order chain; **none of it is asked about**, and time spent reversing the loader is time wasted. The image exists to deliver one file whose `.rdata` holds one key.



## 3. The key - flag 2's EncryptionKey

`AgentConfig::AgentConfig()` in the AdaptixC2 beacon reads:

```cpp
Packer* packer = new Packer((BYTE*)ProfileBytes, size);
ULONG profileSize = packer->Unpack32();

this->encrypt_key = (PBYTE) MemAllocLocal(16);
memcpy(this->encrypt_key, packer->data() + 4 + profileSize, 16);

DecryptRC4(packer->data()+4, profileSize, this->encrypt_key, 16);
```

The key is at `blob + 4 + profileSize`. In `winupdate.exe` that resolves to file offset `0x15904`:

```
015800  00 01 00 00  <- profileSize = 256 (little-endian)
015804  fd 13 ad 94 ... 256 bytes of RC4 ciphertext ...
015904  45 80 22 1a c3 fe 51 be 17 97 52 4a 04 8e 55 2d   <- EncryptKey
015914  00 00 00 00  <- zero padding, end of blob
```

`4580221ac3fe51be1797524a048e552d` - 32 hex characters, which is exactly what the listener's UI generates (`ax.random_string(32, "hex")`) and what the Go transport hex-decodes to 16 bytes before constructing its RC4 cipher.

Decrypted profile:

```
agent_type    be4c0149
kill_date     0            working_time  0
sleep_delay   4            jitter_delay  0
use_ssl       0
servers       ["192.168.56.1"]        ports  [8818]
http_method   POST
uris          /api/v1/status  /updates/check.php  /content.html
parameter     X-Beacon-Id
user_agent    Mozilla/5.0 (Windows NT 6.2; rv:20.0) Gecko/20121202 Firefox/20.0
headers       "\r\n"
ans_pre_size  26           ans_size (extra)  21
hh_count 0   rotation 0   proxy_type 0
```

`ans_pre_size 26` / `ans_size 21` are the offsets that strip the listener's page template:

```
{"status": "ok", "data": "<<<PAYLOAD_DATA>>>", "metrics": "sync"}
└──────── 26 bytes ──────┘                    └──── 21 bytes ────┘
```

The identical profile, byte for byte and key for key, is embedded in the second-stage agent uploaded to the DC. **One listener key covers the whole intrusion**, which is why flag 12 needed no additional work.

> [!warning] This build mixes endianness - assuming one convention silently yields structured garbage
> Upstream AdaptixC2's `Packer` is big-endian throughout. This build is not:
>
> | Direction | Endianness | Proof |
> |:-----------------:|----------------------------------|-------------------------------------|
> | Embedded profile | **little** | port bytes `72 22` = 8818; URI length `0f 00 00 00` = 15 |
> | Server -> agent tasking | **little** | size `44 1a 00 00`; `cmd 32 00 00 00` = 50 |
> | Registration beat | **big** | `acp 04 e4` = 1252; `oemcp 01 b5` = 437; sessionkey length `00 00 00 10` = 16 |
> | Agent -> server output | **big** | frame size `00 00 00 44` = 68 |
>
> Each reading is independently over-determined - code pages 1252/437, a UTC−8 offset, build 26200, a 4-second sleep matching the observed 4-second check-in cadence. There is no single convention that satisfies all four. **Verify endianness per-structure against a field whose value you can predict, not once for the protocol.**



## 4. The beat - flag 2's SessionKey, and flag 12

`Agent::BuildBeat()` packs the agent's identity and its freshly-generated 16-byte SessionKey, then RC4s the whole thing with the profile key. The listener base64-decodes the `X-Beacon-Id` header, decrypts it, and formats the agent id as `%08x`:

```go
return fmt.Sprintf("%08x", agentType), fmt.Sprintf("%08x", agentId), agentInfo, bodyData, nil
```

That `%08x` is where the BeaconID string in flags 12 comes from - it is a formatting choice in the server, not a value on the wire.

| | Beacon 1 (`192.168.56.22`) | Beacon 2 (`192.168.56.11`) |
|:-----------------:|----------------------------|----------------------------------------|
| BeaconID | `58debcbb` | `ddc68fa7` |
| SessionKey | `53fc4c03c7b461befe5dcb268e3d9208` | `289122cf1ec91c67eb89c30642adfea4` |
| pid / tid | 6040 / 10820 | 3376 / 4968 |
| build | 26200 (Win 11) | 17763 (Server 2019) |
| identity | `core.diogenes.htb` \ `WS02` \ `afenwick` | `core.diogenes.htb` \ `DC02` \ `SYSTEM` |
| process | `winupdate` | `svc_bkup` |
| flag byte | `0b0011` - not elevated, not server | `0b1111` - **elevated, server** |

The flag byte is `is_server<<3 | elevated<<2 | sys64<<1 | arch64`. Reading it confirms the whole arc in four bits: the room opens on a non-elevated workstation user and closes on SYSTEM on a domain controller.

`pid 6040` = `0x1798`, which is the same PID the NTLM event log records for `ProcessName: winupdate`. That single correspondence ties the network evidence to the host evidence and is what makes flag 6's timestamp defensible rather than inferred.



## 5. Decrypting the session

RC4 is re-keyed per message with the same key, so **every message reuses one keystream**. That is visible before any decryption: long identical byte runs at matching offsets across unrelated responses. It is also the reason a partial known-plaintext attack would have worked had the key not been in the binary.

```python
reqs  = split_msgs(stream(client -> server))   # bodies are RC4(SessionKey)
resps = split_msgs(stream(server -> client))   # bodies are template + RC4(SessionKey) + template
payload = body[26 : len(body)-21]
```

Responses use `Transfer-Encoding: chunked`, so a Content-Length-only reassembler returns empty bodies for every message that actually carries tasking - the sixteen that matter. This cost one wrong turn; see §11.

### Frame formats

**Agent -> server** (big-endian):

```
[u32 total_size]
  repeated:
    [u32 task_id][u32 command]
      command 0x33 (EXEC_BOF_OUT): [u32 callback_type][u32 length][bytes]
      command 0x32 (EXEC_BOF):     <task finished>
```

`callback_type` `0x00` = `CALLBACK_OUTPUT`, `0x0d` = `CALLBACK_ERROR`. The error callback is what surfaced the operator's typo in §7.

**Server -> agent** (little-endian):

```
[u32 total_size][u32 command = 50]
[u8 async][u32 len]["go\0"]
[u32 bof_len][COFF object]
[u32 arg_block_len][u32 arg_block_total][u32 len][arg] ...
```

The argument block carries its own total length before the first argument - a duplicate that will silently consume the first real argument if you treat it as one. That is what corrupted the first extraction of the uploaded PE.



## 6. Reconnaissance and the DACL - flag 5

Thirteen distinct BOFs, all `go`-entry, all synchronous:

| md5 | Size | Purpose |
|:-----------------------------------------:|----------------|----------------------------------|
| `eb4963180235a5ff56317b0cd3a0f562` | 6,700 | `whoami /all` |
| `49c1b73b0b533519a4cc0988a16a0c43` | 4,184 | `route print` |
| `fbb23e2dc1c7ab31909ec88ba03a39dd` | 3,584 | adapter / DNS config |
| `665d91a2b04034a15281d6554a03032e` | 11,210 | LDAP user enumeration |
| `7db0b0779235cf89c3582e0fafd20e98` | 11,137 | LDAP group lookup |
| `e952dca1016aa7a3087974502d84f1ca` | 11,236 | LDAP computer enumeration |
| `84f69337b38cd892aa44e57b48a47915` | 11,880 | LDAP domain information |
| `794bdda4dbef52d1dddc34b7eed2f712` | 7,109 | DNS record resolution |
| `735a6502645641d7001c4fba0a13b76f` | 35,470 | **LDAP security-descriptor reader** |
| `56c92e28050c334b1b54974ffd022192` | 9,484 | **`internal_monologue`** |
| `583236cc3ef2488fb133385bcd75825e` | 70,169 | **`resetnightmare`** - flag 4 |
| `d61a5f6dc3201a6a05de50b4e1516918` | 2,168 | `make_token` |
| `11575c637217fa9a57229cdb9da11f13` | 3,410 | service-hijack lateral movement |

The DACL reader, run against `afenwick`, pulled 2,456 bytes of security descriptor and printed 51 ACEs. ACE #4 is the one:

```
ObjectDN                : CN=afenwick,OU=Analysts,OU=Staff,DC=core,DC=diogenes,DC=htb
ObjectSID               : S-1-5-21-2253468260-689643353-167204612-1125
ACEType                 : ACCESS_ALLOWED_OBJECT_ACE
ActiveDirectoryRights   : WriteProperty
ObjectAceFlags          : ACE_OBJECT_TYPE_PRESENT
ObjectAceType           : 28630ebb-41d5-11d1-a9c1-0000f80367c1     <- userPrincipalName
SecurityIdentifier      : S-1-5-21-2253468260-689643353-167204612-1125
```

**`afenwick` can write his own `userPrincipalName`.** That is the entire privilege-escalation primitive.

> [!note] The question's wording is wrong; the BOF's field label is what it grades against
> An ACE has no "ObjectSID of a property" - the field identifying the *property* is `ObjectAceType`, a GUID. But this BOF labels the ACE's target-object SID `ObjectSID`, and that is the accepted answer. Fortunately `ObjectSID` and `SecurityIdentifier` are the same value on this ACE, so the ambiguity had no cost.
>
> Generalisation, consistent with §3.1 of the MOC: **when a question's terminology does not match the domain, it matches the tool's output.** Read the question as a field name in the artifact, not as a statement about Active Directory.



## 7. CVE-2026-27912 - ResetNightmare

`resetnightmare` chains a UPN write into a Kerberos password reset. Decrypted output, abridged:

```
[*] Action: ResetNightmare (CVE-2026-27912)
[*] UPN-write + enterprise AS-REQ + kadmin/changepw password reset

[*] Impersonating afenwick for LDAP operations
[*] Step 1: Setting fake UPN on afenwick -> jreed
[+] UPN set: afenwick -> jreed
[*] Step 2: AS-REQ enterprise for kadmin/changepw as jreed
[*] Sending AS-REQ to dc02.core.diogenes.htb:88 (RC4 pre-auth, key derived from afenwick's password)
[+] AS-REP received - KDC issued TGT for jreed
[+] TGT acquired (kadmin/changepw) for target
[*] Step 3: Clearing fake UPN from afenwick before changepw
[+] UPN cleared
[*] Step 4: Resetting jreed's password via kadmin/changepw
[*] New password: Aigohng8vai0seish4zi
[+] Password change success!
[+] Verified: jreed accepts the new password
```

The mechanism is the classic UPN-collision confusion: the KDC resolves the enterprise principal `jreed` by UPN, but pre-authentication is validated against `afenwick`'s long-term key. Clearing the UPN before the changepw call removes the collision so the subsequent operation lands on the real `jreed`.

**Step 2 is why flag 7 exists.** RC4 pre-auth requires `afenwick`'s key, i.e. his password, which is why the operator had to steal it first.

> [!note] The operator fat-fingered it, and the error callback recorded the failure
> The BOF was tasked twice, eight seconds apart:
>
> ```
> 20:46:39   /targer:jreed /new:Aigohng8vai0seish4zi /upnuser:afenwick /upnpass:*Seash5lls*
> 20:46:47   /target:jreed /new:Aigohng8vai0seish4zi /upnuser:afenwick /upnpass:*Seash5lls*
> ```
>
> The first returned `[X] /target: required (account to reset)`. Identical BOF, identical md5, identical password - only the flag name differs. Worth recording because it is the clearest possible evidence of a human at a keyboard rather than an automated chain, and because the failed run is the shorter, cleaner place to read the argument list.

`*Seash5lls*` is **flag 7**, recovered from the argument rather than by cracking the hash. The NTLMv2 response is in the capture and could be cracked, but the operator handed the plaintext to the BOF.



## 8. internal_monologue - flag 6

The credential-theft BOF takes no arguments and imports exactly three SECUR32 functions:

```
__imp_SECUR32$AcquireCredentialsHandleA
__imp_SECUR32$InitializeSecurityContextA
__imp_SECUR32$AcceptSecurityContext
```

plus the literal `1122334455667788`. That is a local SSPI loopback with a fixed server challenge - the agent negotiates NTLM with itself, patches in a known challenge, and reads the resulting response out of the security buffer. No LSASS access, no network peer, no relay.

```
NTLMv2 Response:
afenwick::DIOCORE:1122334455667788:032b0b4aa446b7d68c6780135ef2ec24:0101000000000000b98318f8...
```

The host-side artifact is a single event:

```
Microsoft-Windows-NTLM/Operational  Event 4021  2026-09-09 20:44:11.745045Z
  ProcessName      : winupdate
  ProcessPID       : 0x00001798          (6040 - matches the beacon's beat)
  Username         : afenwick   DomainName : DIOCORE
  TargetService    : Null
  NtlmUsageId      : 1
  NtlmUsageReason  : NTLM was called directly by the calling application.
  SessionKeyStatus : Missing
```

The tasking response carrying this BOF is stamped `Date: Wed, 09 Sep 2026 20:44:11 GMT`. **Log and wire agree to the second**, from independent sources.

> [!warning] Flag 6 cost three submissions on the name alone
> Rejected: `Internal Monologue`, `InternalMonologue`, `Internal Monologue Attack`. Accepted: **`internal_monologue`**.
>
> The answer key uses the **BOF's shipped filename**, not the technique's published name. Elad Shamir's paper calls it the Internal Monologue Attack; the AdaptixC2 extension kit calls the object `internal_monologue`. The grader wanted the second.
>
> This is the fourth instance of the MOC's §3.1 rule and the first where the correct form is *lowercase snake_case*. Rule extended: **when the answer names a capability the operator invoked, submit the name of the file the operator invoked, not the name of the technique it implements.**



## 9. Privesc and lateral movement - flags 9, 10, 11

`make_token` with the new credentials:

```
args: "jreed" (UTF-16), "Aigohng8vai0seish4zi" (UTF-16), "DIOCORE" (UTF-16), 9
out:  The user impersonated successfully: DIOCORE\jreed (logon: 9)
```

Logon type **9** is `LOGON32_LOGON_NEW_CREDENTIALS` - the token keeps the local identity and swaps only the network credentials. It is the correct choice here because the beacon stays `afenwick` locally while authenticating to the DC as `jreed`, and it is the reason the operator never needed to touch LSASS.

The lateral-movement BOF takes four arguments and an embedded PE:

```
arg 1  "dc02"
arg 2  "defragsvc"
arg 3  "\\dc02\ADMIN$\svc_bkup"
arg 4  <103,936 bytes>   PE32+ GUI x86-64, md5 ae74305b36c450b8850e34599426d28a
```

Output:

```
Trying to connect to dc02
Uploading binary (103936 bytes) to: \\dc02\ADMIN$\svc_bkup
Binary uploaded successfully (103936 bytes written)
SC_HANDLE Manager: 0x0000020AACB60FC0
Opening service: defragsvc
Original service binary path: "C:\Windows\system32\svchost.exe -k defragsvc"
Service path was changed to: "\\dc02\ADMIN$\svc_bkup"
Service was started
Service path was restored to: "C:\Windows\system32\svchost.exe -k defragsvc"
```

The uploaded PE is a service binary - `AgentService`, `StartServiceCtrlDispatcherA`, `RegisterServiceCtrlHandlerA` - carrying the same AdaptixC2 profile and the same EncryptKey. `defragsvc` is the **svchost service group** whose `-k` argument the operator hijacked, which is flag 11. The path is restored immediately after start, so a post-incident registry snapshot shows nothing.

> [!note] Flag 10 wants the IP, the artifact says the hostname
> The BOF argument and its own output both read `\\dc02\ADMIN$\svc_bkup`. The accepted answer is `\\192.168.56.11\ADMIN$\svc_bkup`. The mapping comes from the operator's own DNS BOF three minutes earlier (`A dc02.core.diogenes.htb 192.168.56.11`) and is confirmed by the second beacon's source address.
>
> This is the **inverse** of the §3.1 literal-string rule, and the only flag in the event where normalising the artifact was required rather than penalised. The discriminator is the answer-format hint: it says `\\IP\Share\...`, and the hint outranks the artifact's rendering.



## 10. Timeline

All UTC. Local is UTC−8.

| UTC | Event | Source |
|:----------------------:|---------------------------------------------|-----------------------------------|
| 09-08 21:01–21:02 | WinRM / powershell NTLM during image build (`DESKTOP-9VL5A7L`, `WIN-NMVE917FCFR`) | NTLM evtx |
| 09-09 19:20:17 | `afenwick` NTLM from `unhappy-meal` `192.168.56.1` over `TERMSRV/192.168.56.22` - **fails**, `0xc000006d` | evtx 4022 |
| 09-09 19:42:58 | same, **succeeds** | evtx 4022 |
| 09-09 **20:32:33** | **first beacon check-in**, `58debcbb`, `afenwick` on `WS02`, not elevated | pcap |
| 09-09 20:32:57 | `whoami /all` | BOF |
| 09-09 20:33:13 | `route print` | BOF |
| 09-09 20:34:09 | adapter / DNS config - `ws02`, DNS `192.168.56.11` | BOF |
| 09-09 20:35:21, 20:35:53 | LDAP user enumeration - 22 users | BOF |
| 09-09 20:36:45 | LDAP group lookup `Tier0` - **not found** | BOF |
| 09-09 20:37:18 | LDAP computer enumeration - 2 computers | BOF |
| 09-09 20:37:46 | DNS `A dc02` -> `192.168.56.11` | BOF |
| 09-09 20:38:18, 20:40:10 | LDAP domain information, then `dc01.diogenes.htb` (parent domain) | BOF |
| 09-09 20:40:47 | DNS `A dc01` -> `192.168.56.10` | BOF |
| 09-09 **20:41:43** | **DACL read on `afenwick`** - 51 ACEs, `WriteProperty` on `userPrincipalName` | BOF |
| 09-09 **20:44:11** | **`internal_monologue`** - `afenwick` NetNTLMv2 captured | BOF + evtx 4021 |
| 09-09 20:46:39 | `resetnightmare` - **fails on `/targer:` typo** | BOF error callback |
| 09-09 **20:46:47** | **`resetnightmare` succeeds** - `jreed` password reset | BOF |
| 09-09 **20:48:24** | **`make_token` `DIOCORE\jreed`, logon type 9** | BOF |
| 09-09 **20:49:36** | **upload to `\\dc02\ADMIN$\svc_bkup`, `defragsvc` hijacked and started** | BOF |
| 09-09 ~20:50:00 | **second beacon `ddc68fa7`** checks in from `192.168.56.11` as `SYSTEM`, elevated | pcap |
| 09-09 20:50:05 | capture ends | pcap |

**Seventeen and a half minutes** from first check-in to SYSTEM on a domain controller. Nine minutes of that is reconnaissance; the kill chain from DACL read to DC beacon is eight minutes and seventeen seconds.

The RDP session at 19:42:58 predates the beacon by fifty minutes and uses the same credentials the beacon later re-steals. Whether the operator forgot he had them or the two phases are different operators is not determinable from these artifacts.



## 11. Final payload

Reproduction, from the supplied ZIP to all twelve answers.

```bash
cd ~/bn && unzip BorrowedName.zip -d outer
unzip -P 'PaedeiRae1xiexahwuno' outer/danger.zip -d ev
pip install --break-system-packages scapy python-evtx pyfatfs

#  lure: FAT32 at partition offset 2048*512 (no loop mount needed) 
python3 - <<'PY'
from pyfatfs.PyFatFS import PyFatFS
fs = PyFatFS("ev/Q3_Salary_Review.img", offset=1048576, read_only=True)
for n in fs.listdir("/"):
    open("img/"+n,"wb").write(fs.open("/"+n,"rb").read())
PY

#  key: [u32 LE size][ciphertext][16-byte key] in .rdata 
python3 - <<'PY'
import struct
d=open("img/winupdate.exe","rb").read()
n=struct.unpack_from('<I',d,0x15800)[0]              # 256
key=d[0x15804+n:0x15804+n+16]
print("EncryptKey", key.hex())                        # 4580221a...552d
PY

#  beat: base64(X-Beacon-Id) -> RC4(EncryptKey) -> BIG-endian struct 
#   [u32 agent_type][u32 agent_id][u32 sleep][u32 jitter][u32 kill][u32 work]
#   [u16 acp][u16 oemcp][i8 gmt][u16 pid][u16 tid][u32 build][u8 maj][u8 min]
#   [u32 ip][u8 flag][u32 len=16][SessionKey] then 4 length-prefixed strings

#  session: strip the page template, RC4 with SessionKey 
#   responses are chunked; a Content-Length-only reassembler drops every
#   message that carries tasking
#   payload = body[26 : len(body)-21]

#  tasking: LITTLE-endian, output frames: BIG-endian 
#   srv->agent: [u32 size][u32 cmd=50][u8 async][u32 len]["go\0"]
#               [u32 bof_len][COFF][u32 argblk_len][u32 argblk_total][u32 len][arg]...
#   agent->srv: [u32 size] then [u32 task][u32 cmd]
#               cmd 0x33: [u32 callback][u32 len][bytes];  cmd 0x32: finished

#  flag 6's timestamp 
python3 - <<'PY'
import Evtx.Evtx as evtx, re
p='ev/C/Windows/System32/winevt/logs/Microsoft-Windows-NTLM%4Operational.evtx'
with evtx.Evtx(p) as f:
    for r in f.records():
        x=r.xml()
        if 'winupdate' in x: print(re.search(r'SystemTime="([^"]+)"',x).group(1))
PY
```



## 12. Tools & techniques

`python3` · `scapy` · `python-evtx` · `pyfatfs` · `pefile` · `strings` · `git` (AdaptixC2 source) · `pdftotext` · `unzip`

**Concepts:** FAT32 extraction from a raw image by partition offset without a loop mount · AdaptixC2 `beacon` agent identification by RTTI class names and stock listener defaults · **agent watermark (`be4c0149`) as a framework fingerprint** · embedded-profile recovery where the RC4 key is stored immediately after its own ciphertext · beat decoding for BeaconID and SessionKey · listener page-template offsets (`ans_pre_size` / `ans_size`) as the framing for response payloads · **per-structure endianness verification against predictable fields** · chunked-transfer reassembly as a prerequisite for C2 decryption · RC4 keystream reuse across messages as a visible pre-decryption tell · COFF object extraction from a tasking stream and md5 attribution · COFF symbol-table reading for BOF capability identification · AD object DACL interpretation (`ObjectAceType` GUID -> attribute) · UPN-collision Kerberos abuse · `LOGON32_LOGON_NEW_CREDENTIALS` semantics · svchost service-group hijack with path restoration · NTLM Operational event 4021 `NtlmUsageId 1` as the Internal Monologue signature



## 13. MITRE ATT&CK

| Technique | ID | Evidence |
|:----------------------------------------------------:|------------------------------------------------|-----------------------------------------------------------|
| User Execution: Malicious File | T1204.002 | mounted `.img` with a PDF-named LNK invoking `docviewer.exe` |
| Hijack Execution Flow: DLL Search Order Hijacking | T1574.001 | `VERSION.DLL` exporting `RunPayload` beside `docviewer.exe` |
| Application Layer Protocol: Web Protocols | T1071.001 | HTTP POST beaconing to `192.168.56.1:8818`, three rotating URIs |
| Encrypted Channel: Symmetric Cryptography | T1573.001 | RC4-16 with a per-agent SessionKey, profile key in the binary |
| Account Discovery: Domain Account | T1087.002 | LDAP user and computer enumeration BOFs |
| Permission Groups Discovery: Domain Groups | T1069.002 | LDAP group lookup, `Tier0` |
| OS Credential Dumping: LSASS Memory | T1003.001 | **weak - see scope note** |
| Brute Force: Password Cracking | T1110.002 | NetNTLMv2 captured for offline recovery of `*Seash5lls*` |
| File and Directory Permissions Modification | T1222.001 | `userPrincipalName` write on `afenwick` |
| Access Token Manipulation: Make and Impersonate Token | T1134.003 | `make_token DIOCORE\jreed`, logon type 9 |
| Create or Modify System Process: Windows Service | T1543.003 | `defragsvc` `ImagePath` changed, started, restored |
| Lateral Tool Transfer | T1570 | 103,936-byte service agent written to `ADMIN$` |
| Remote Services: SMB/Windows Admin Shares | T1021.002 | `\\dc02\ADMIN$\svc_bkup` |

> [!warning] Honest scope
> IDs assigned without access to the live ATT&CK matrix. **T1003.001 is wrong and is listed only because nothing better exists.** Internal Monologue is explicitly a *non*-LSASS technique - it negotiates NTLM with the local SSPI provider and reads the response out of a security buffer. ATT&CK has no sub-technique for local SSPI challenge-response coercion; T1003.001 is the closest slot and it misdescribes the mechanism. Flag it if the matrix has since added one.
>
> **No technique covers the CVE-2026-27912 primitive.** UPN-collision abuse of enterprise principal name resolution is neither T1558 (Kerberos ticket abuse, which concerns forged or extracted tickets) nor T1098 (account manipulation, which describes persistence via account modification). The UPN write here is a transient means to a password reset, reverted within the same BOF run. T1222.001 captures the write and nothing else.
>
> T1110.002 is **inferred**: the room shows the hash captured and the plaintext later supplied to a BOF, but no cracking artifact. That the two are connected is the only reading the evidence supports, not something it proves.



## 14. Detection / blue-team notes

**On the C2 channel.** The traffic is not subtle once you know the shape:

- **A custom request header carrying a long base64 blob on every single request, with a zero-length body.** `X-Beacon-Id` is the AdaptixC2 default and it appeared on all 278 requests in this capture. Any header that is constant-length, high-entropy and present on every request from one host is a beacon identifier.
- **Four-second check-ins with zero jitter.** `sleep_delay 4, jitter_delay 0` produced a metronome: `20:32:33, :37, :41, :45`. Perfectly periodic HTTP to a single host is the cheapest beacon detection there is, and this sample makes no attempt to hide it.
- **Three URIs rotating round-robin from one client** (`/api/v1/status`, `/updates/check.php`, `/content.html`) - a mixture of API, PHP and static-HTML paths that no real application serves to one user agent in strict rotation.
- **A hard-coded Firefox 20 User-Agent in 2026.** Stock AdaptixC2; nobody changed it.
- **`Content-Type: application/octet-stream` on a response whose body is JSON.** The listener's page template is JSON-shaped, the header is not. Header/body disagreement of this kind is a profile artifact.

**On the host side.**

- **`Microsoft-Windows-NTLM/Operational` event 4021 with `NtlmUsageId: 1` ("NTLM was called directly by the calling application") and `SessionKeyStatus: Missing`, from a process that is not a known NTLM consumer.** This is the Internal Monologue signature, and this log is not enabled by default in most environments. Enabling it is a one-GPO change and it is the only artifact in this room that dates the credential theft.
- **A service whose `ImagePath` changes to a UNC path and changes back within seconds.** The restoration is the tell: a legitimate reconfiguration stays. Service Control Manager event 7040 records both edits; neither the pre- nor post-image registry shows anything.
- **Any svchost group service whose binary path stops being `svchost.exe -k <group>`.** `defragsvc` is a shared-process service; a non-svchost `ImagePath` on one is definitionally wrong.
- **`WriteProperty` on `userPrincipalName` granted to the object's own SID.** This is the enabling misconfiguration and it is a BloodHound-visible, statically auditable condition. No exploit is required to find it; audit for self-write on UPN across the directory and this CVE has no targets.

**On the encryption, at the class level.** An agent that ships its own decryption key sixteen bytes past the ciphertext is not protecting its configuration from a defender - it is protecting it from `strings`. Any responder with the binary has the traffic, permanently, for every agent that listener ever produced, because the EncryptKey is per-listener and not per-agent. **Recovered beacon binary plus captured traffic equals plaintext**, and that should be the first thing attempted in any intrusion where both are in evidence, before any effort goes into behavioural inference from packet sizes and timing.



## 15. Method notes

- **Read the framework's source before parsing its protocol.** The single highest-leverage action in this room was `git clone` of AdaptixC2. It supplied the profile container layout, the field order of the beat, the `%08x` BeaconID formatting, the page-template offsets and the tasking structure - five things that would each have cost an hour of guessing and one of which (the key's position *after* the blob) is genuinely non-obvious. **When an artifact is produced by public tooling, the tooling is the documentation.**
- **Verify endianness per structure, against a field whose value you can predict.** Assuming one convention for the whole protocol produced plausible-looking garbage. Codepage 1252, OEM 437, a −8 GMT offset and a build number are all values you know before you parse them; use them as the oracle. Generalises beyond endianness to any format assumption.
- **A capability question is answered by the tool's filename, not the technique's name.** Three submissions on flag 6 went to prose variants of "Internal Monologue" before `internal_monologue` took. The event has now produced four instances of the same underlying rule; this one adds *casing and separator* to the list of things that are literal.
- **The answer-format hint outranks the artifact when they conflict.** Flag 10's artifact says `\\dc02\...`; the hint says `\\IP\...`; the hint won. Everywhere else in this event the artifact's rendering won. The discriminator is whether the hint *specifies a representation* - `(SID)`, `(md5 hash)`, `\\IP\Share\...` do; `(string)` does not.
- **`(string)` is the least informative hint in the format vocabulary and should be treated as a warning.** Flag 1 cost four submissions - `AdaptixC2`, `192.168.56.1:8818`, `192.168.56.1`, `unhappy-meal` - before `adaptix` landed. Every one was defensible from evidence. When the hint is bare `(string)`, enumerate the naming variants *first* and submit the most minimal, lowest-case form early, because there is no signal in the hint to narrow on.
- **Parse the wrapper before concluding the payload is empty.** Sixteen of seventeen tasking responses returned zero-length bodies to a Content-Length-only reassembler, which reads exactly like an empty C2 channel. `Transfer-Encoding: chunked` was in the headers the whole time. Cousin of the MOC's §3.5 rule: **a null result from a parser that cannot handle the container is not a result.**
- **The failed operator command is often the better artifact.** The `/targer:` typo run produced a short error callback that listed the argument syntax cleanly; the successful run buried it in 900 bytes of progress output.



## 16. Blind alleys - eliminated, do not re-walk

- **Reversing `docviewer.exe` and `VERSION.DLL`.** A complete DLL-sideload chain, fully intact, asked about by zero questions. The only strings in either are `winupdate.exe`. The image exists to deliver the beacon.
- **`unhappy-meal` as the C2 answer.** The operator's machine name, present in five NTLM 4022 events with `ClientIP 192.168.56.1` - the C2 host's own address. Defensible, distinctive, appears nowhere else in the evidence, and wrong. The question wanted the framework.
- **`AdaptixC2` and `192.168.56.1:8818` as the C2 answer.** Both correct descriptions, both rejected. `adaptix` took.
- **Cracking the NetNTLMv2 hash.** Recoverable and in the capture, but the plaintext `*Seash5lls*` is sitting in the `/upnpass:` argument of the BOF two minutes later. Check the tasking arguments before starting a crack.
- **Searching the binaries for a C2 domain.** There is none. All 278 requests carry `Host: 192.168.56.1:8818`; the second-stage agent's profile is byte-identical to the first; neither PE contains the string "Adaptix". Every hostname in the room is an AD host, not infrastructure.
- **Treating the argument block's leading length as an argument.** It is a total, not an element. Doing so silently truncates the embedded PE by four bytes and shifts every subsequent field, producing a 103,990-byte "PE" that `file` reports as `data`.
- **`0x00010000` as the profile size.** The size prefix is little-endian even though the beat is big-endian. Big-endian reads 65,536 and puts the key past end-of-file.



## 17. Open items

1. **`solves` omitted** - not read off the platform.
2. **`category: forensics` unverified** - inherited from the Sherlock siblings, not read off the Holmes platform page. Consistent with the other four notes' open item.
3. **The RDP session at 19:42:58 is unexplained.** `afenwick`'s credentials were used interactively from the C2 host fifty minutes before the beacon stole them, after one failure at 19:20:17. Either the operator already had the password and re-derived it for the CVE's RC4 pre-auth step, or two phases of the operation did not share notes. The artifacts do not distinguish these.
4. **`Tier0` group lookup returned "not found" and was not retried.** The operator probed for a tiering model, found none, and proceeded. What the negative result changed about his plan is not visible.
5. **`dc01.diogenes.htb` (`192.168.56.10`) was enumerated and never touched.** The parent domain's DC was resolved and queried for domain information at 20:40, two minutes before the DACL read, and then dropped. The capture ends before any cross-domain action.
6. **The uploaded service agent (`ae74305b36c450b8850e34599426d28a`) was not fully analysed.** Confirmed as an AdaptixC2 service-mode beacon with an identical profile; its persistence behaviour and whether it differs from `winupdate.exe` beyond `AgentService` was not examined.
7. **The capture ends 29 seconds after the DC beacon registers.** Three check-ins, no tasking. Whatever the operator did on DC02 is outside this evidence - presumably Sherlock 09.
8. **The `winupdate.exe` build's endianness inversion is uncharacterised.** Whether it is an older AdaptixC2 release, a fork, or the challenge author's modification was not determined. It matters only if another room in this event ships the same agent.



## Cross-references

- [[00_MOC-HTB-Holmes2026-Reichenbach-Directive-Event]] - event index; this room supplies §3.1's fourth instance (tool filename over technique name) and its first counter-example (§9, answer-format hint over artifact rendering)
- [[HTB-Holmes2026-Silent-Dividend-Electron-Preload-Dropper-Onchain-Key-Oracle]] - Sherlock 01; same "key lives outside the protected artifact" structure, third instance in the event
- [[HTB-Holmes2026-Bottle-Out-Wiped-Laptop-Gajim-XMPP-TacticalRMM]] - Sherlock 02; origin of the answer-format-is-literal rule
- [[HTB-Holmes2026-Paper-Ghost-Planted-USB-Spyware-Search-Index-Recovery]] - Sherlock 04; second instance of that rule, and the `DIOGENES` programme that this room's domain (`core.diogenes.htb`) belongs to
- [[HTB-Holmes2026-Iron-Feather-PX4-Encrypted-Dataman-ULog-Custom-KDF]] - Sherlock 07; third instance, and the "reimplement when the transform is closed over readable constants" rule applied here to the profile container
- [[00_ctf-writeup-standard]] - structure this note conforms to
- [[HTB]]



## Change Log

- 2026-09-20 - Note created. All twelve flags solved and recorded; scenario captured verbatim. Seven wrong submissions recorded in §15 and §16 (flag 1 ×4: `AdaptixC2`, `192.168.56.1:8818`, `192.168.56.1`, `unhappy-meal`; flag 6 ×3: `Internal Monologue`, `InternalMonologue`, `Internal Monologue Attack`) - **all seven were format or naming failures on correct findings**, extending the MOC §4.1 taxonomy class to eleven of thirteen wrong submissions across the event. `category` and `solves` marked unverified pending a read of the platform page (§17.1–2). T1003.001 flagged as a known-wrong mapping in §13.
