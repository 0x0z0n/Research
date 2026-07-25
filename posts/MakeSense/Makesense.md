# MakeSense

```
Difficulty: Easy
Operating System: Linux
Services: SSH, internal OCR web application (127.0.0.1:8001, HTTP Basic Auth)
```

## Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :-: | :- | : | :- |
| 1 | walter (SSH creds) | **SSH local port-forward** | Exposed the internal-only OCR web app (`127.0.0.1:8001`) locally via `ssh -L`. |
| 2 | walter | **PHP payload rendered as image** | Drew `<?php system($_GET['c']); ?>` onto a PNG canvas for OCR ingestion. |
| 3 | walter | **OCR submission** | Submitted the image to the OCR endpoint, obtaining an `ocr_id` for the recognized text. |
| 4 | walter | **Unrestricted file upload via "save output"** | Saved the OCR-recognized text (the PHP payload) to a web-accessible path with an executable extension (`.php`/`.phtml`/`.php5`/`.pht`). |
| 5 | www-data (web service) | **Webshell RCE** | Requested the saved file directly, confirming and using command execution as the web service account. |




## 1. Summary

`walter`'s SSH credentials provide access to the box, but the interesting attack surface - an internal OCR (optical character recognition) web application - is bound to `127.0.0.1:8001` and not reachable directly from outside. An SSH local port‑forward exposes that internal service locally.

The OCR app accepts an uploaded image, performs OCR against it, and offers a "save output" feature that writes the recognized text to a filename of the user's choosing under a web‑accessible `saved/` directory. By rendering PHP code as an image (so OCR faithfully transcribes it back into text) and saving the result with a `.php`/`.phtml`/`.php5`/`.pht` extension, the app can be tricked into writing an executable PHP webshell to disk, which is then invoked directly for remote code execution.



## 2. Enumeration

- **SSH (22/tcp)** - valid credentials known for user `walter`.
- **Internal service, `127.0.0.1:8001`** - an OCR web application, bound to loopback only, so it is not exposed externally; requires SSH access to the box to reach it (local port‑forward).
- **Authentication** - the OCR app itself is protected by HTTP Basic Auth (same `walter` credentials in this case).
- **Functionality identified:**
  - Image upload (`canvas_image`, base64‑encoded PNG data URI) -> returns an `ocr_id`.
  - A "save output" action (`ocr_id`, `filename`, `save_output=1`) that writes the OCR‑recognized text of that image to `saved/<filename>` under the web root.



## 3. Access Setup - SSH Local Port‑Forward

Since the OCR app is bound to `127.0.0.1:8001` on the target itself, it's only reachable through an SSH tunnel:
```
ssh -L 8001:127.0.0.1:8001 walter@makesense.htb
```
This makes the internal app available at `http://127.0.0.1:8001/` on the attacker's machine, with all traffic proxied through the SSH session. The automation script manages this tunnel as a background subprocess, polling the local port until the forward is confirmed live before proceeding.



## 4. Exploitation - OCR‑to‑Webshell RCE

### 4.1 Vulnerability

The OCR "save output" feature writes attacker‑influenced *content* (the OCR‑recognized text of an uploaded image) to an attacker‑chosen *filename* inside a directory served directly by the web server. Two separate weaknesses combine here:

1. **Arbitrary content injection** - OCR is a text‑recognition engine, not a sanitizer; if you render exactly the PHP code you want as legible text in an image, OCR will transcribe it back out verbatim (or close enough) as the "recognized" text.
2. **Arbitrary filename / extension control** - the save endpoint lets the client pick both the base filename and, effectively, the extension, with no server‑side restriction preventing an executable extension (`.php`, `.phtml`, `.php5`, `.pht`) in a web‑accessible upload directory.

Together, this is a classic **unrestricted file upload -> RCE** pattern, just routed through an OCR pipeline instead of a raw file‑upload form.

### 4.2 Exploit steps
1. **Render the payload as an image.** Draw the text `<?php system($_GET['c']); ?>` onto a blank PNG canvas using a monospace font, so OCR can reliably read it back as text.
2. **Submit the image** to the OCR endpoint (`canvas_image` field, base64 data URI) and parse the returned `ocr_id` from the response HTML.
3. **Trigger "save output"** with that `ocr_id` and a candidate filename, iterating over PHP‑executable extensions (`.php`, `.phtml`, `.php5`, `.pht`) until one is accepted and not blocked by any server‑side filter.
4. **Verify RCE** by requesting `saved/<filename>?c=id` and checking for `uid=...` in the response, confirming the webshell executes.
5. **Use the shell** - issue arbitrary commands via `?c=<cmd>`, either one‑shot or in an interactive read‑eval loop.



## 5. Root Cause Analysis

| Stage | Root Cause | CWE |
||||
| Internal app reachable only via SSH tunnel | Expected network segmentation (not itself a bug) - but relies on `walter`'s credentials being the only gate | N/A |
| OCR‑to‑webshell RCE | Uploaded/recognized content written to an attacker‑chosen filename with an executable extension inside a web‑servable directory, with no content‑type or extension allow‑listing | CWE‑434 (Unrestricted Upload of File with Dangerous Type) |
| No output sanitization | OCR text output trusted and written to disk verbatim, with no encoding/escaping for the destination context (a PHP‑interpreted file) | CWE‑95 (Improper Neutralization of Directives in Dynamically Evaluated Code) |



Once a working extension is confirmed, arbitrary commands are executed via `saved/<filename>?c=<cmd>`, either as a single one-shot request or in an interactive read-execute loop, all still tunneled through the SSH port-forward established in the access-setup phase.

# Defensive Operations

## Strategic Overview

* **1.1 Definition:** Exploitation of an unrestricted-file-upload vulnerability in an internal OCR web application, where OCR-recognized text is written verbatim to a web-servable path with a client-controlled, unfiltered extension, enabling remote code execution.
* **1.2 Impact:** Remote Code Execution as the web service account (scope limited to what this chain confirms; further privesc, if present, is out of scope for this script).
* **1.3 The Scenario:** An actor holding valid SSH credentials tunnels into an internal-only OCR tool not otherwise reachable from the network. By rendering PHP source code as a legible image and relying on OCR to transcribe it back to text, the actor abuses the tool's "save recognized text" feature to plant an executable PHP file directly inside the web root, achieving code execution.

## System Architecture & Theory

* **2.1 Environment:** Linux, SSH, an internal Flask/PHP-style web application performing OCR, a web-servable `saved/` output directory.
* **2.2 Attack Logic Flow:**

> [SSH Credentials] -> [Local Port-Forward to 127.0.0.1:8001] -> [PHP Payload Rendered as Image] -> [OCR Submission] -> [Save Output with Executable Extension] -> [Webshell RCE]

* **2.3 Theoretical Analogy:** Handing a photocopier a photo of a signed blank check and asking it to "type up what it sees" into a document it then files directly into the company's outgoing-payments folder, extension and all, without anyone checking whether that document should be allowed to run as an instruction rather than just be read.

## Attack Vector

| Attribute | Technical Details |
| :-- | :- |
| **Primary Identifiers** | Internal OCR app, loopback-only `127.0.0.1:8001`<br>`canvas_image` submission endpoint<br>"Save output" action (`ocr_id`, `filename`, `save_output=1`)<br>Web-servable `saved/` directory |
| **Critical Vulnerability** | **Unrestricted file upload with dangerous type** - OCR-recognized content written to a client-chosen filename/extension inside a web-executable directory, with no content or extension filtering. |
| **Offensive Action** | SSH tunnel to internal app -> PHP-as-image OCR submission -> save-output extension abuse -> direct webshell invocation |

### Prerequisites

* **Access Level:** Valid SSH credentials (initial access); no further privilege required to reach the internal app once tunneled.
* **Connectivity:** SSH (22/tcp) externally; loopback `8001/tcp` on the target itself.
* **Target State:** OCR "save output" feature accepts arbitrary filenames/extensions and writes to a location the web server will execute as PHP.

## Threat Hunting & Anomaly Analysis

* **Hunt Hypothesis:** Adversaries exploiting this chain will authenticate via SSH and immediately establish a local port-forward to an otherwise-unused local port, followed shortly by a burst of near-identical `POST` requests to an OCR save-output endpoint trying multiple file extensions, and finally a `GET` request to a newly-created file inside the OCR output directory carrying a suspicious query parameter (e.g., `?c=`).
* **Behavioral Outliers:** SSH sessions establishing `-L` forwards to internal-only application ports shortly after authentication. Repeated save-output requests differing only by file extension. New `.php`/`.phtml`/`.php5`/`.pht` files appearing in an "OCR output" directory that should only ever contain recognized-text artifacts.
* **Toxic Combinations:** An internal tool reachable only via SSH tunnel, treated as implicitly trusted, combined with a save feature that performs no server-side validation of either content or destination extension.

## Detection Engineering

* **Telemetry Gap Analysis:** SSH session/port-forward auditing (`sshd` logs with `AllowTcpForwarding` visibility), web server access logs for the OCR app, file-integrity monitoring on the `saved/` output directory, web server process telemetry for PHP execution of newly-written files.
* **Detection-as-Code (KQL):**

```kql
// Detect a new PHP-executable file appearing in an OCR "saved output" directory
DeviceFileEvents
| where FolderPath has "/saved/"
| where FileName endswith ".php" or FileName endswith ".phtml"
       or FileName endswith ".php5" or FileName endswith ".pht"
| project Timestamp, DeviceName, FolderPath, FileName, InitiatingProcessFileName
```

```kql
// Detect the web server process executing a freshly created file in that same directory
// within a short window of its creation
DeviceProcessEvents
| where ProcessCommandLine has "/saved/" and ProcessCommandLine has ".php"
| project Timestamp, DeviceName, InitiatingProcessFileName, ProcessCommandLine
```

* **Resilience Test:** An adversary could use a less common but still-executable extension not covered by a fixed detection list (e.g., a server-specific handler mapping), or rename the payload to blend with expected OCR-output filenames, evading a strict extension-based rule.
* **Sub-Rule:** Alert on *any* write to a designated "output/results" directory whose content, on inspection, contains `<?php` or other script-engine open tags, regardless of the extension used - content-based detection is more resilient than extension-based detection alone.

## Toolkit & Implementation

* **Automation:** Custom Python exploit script - managed SSH tunnel subprocess (`Popen` + polling, with `atexit` teardown), Pillow-based PHP-as-image renderer, `requests`-based OCR submission and save-output brute-forcer across candidate extensions, one-shot and interactive command execution against the resulting webshell.
* **OPSEC Analysis:** Tunneling all traffic through the existing SSH session avoids opening any new listening port on the attacker side that the target could observe; iterating extensions via the same authenticated session blends the attack traffic in with normal authenticated app usage rather than triggering a fresh, unauthenticated scanning signature.
* **Post-Exploitation:** The webshell is used directly via HTTP GET parameters (`?c=`) rather than establishing a reverse shell, minimizing additional outbound connections from the target.

## Defensive Mitigation

* **Technical Hardening:**
  1. Restrict "save output" filenames to a strict allow-list of non-executable extensions (e.g., `.txt`, `.json`) and reject/strip any others server-side, regardless of client input.
  2. Store OCR output outside the web root, or explicitly disable script execution (e.g., PHP engine off) for that directory at the web server configuration level, independent of extension.
  3. Treat OCR-recognized text as untrusted user-supplied content and apply the same upload/content validation used elsewhere in the application.
  4. Scope SSH `AllowTcpForwarding` and internal-app authentication independently - don't rely on "reachable only via tunnel" as a security boundary.
  5. Avoid credential/password reuse between SSH accounts and internal application authentication.
* **Personnel Focus:** Train development teams that any feature which "saves recognized/generated content to a filename" is a file-upload feature in disguise, and must go through the same extension/content controls as a traditional upload form.

## Quick Action Playbook

| Step | Objective | Technical Command / Logic |
| :--: | :-- | : |
| **01** | **Reach the internal app** | `ssh -L 8001:127.0.0.1:8001 walter@<target>` |
| **02** | **Render & submit payload** | POST base64 PNG of `<?php system($_GET['c']); ?>` to OCR `canvas_image` endpoint |
| **03** | **Escalate to RCE** | POST `save_output=1` with filename `shell.php`/`.phtml`/`.php5`/`.pht`, then `GET saved/<filename>?c=id` |
