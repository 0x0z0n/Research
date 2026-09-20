#!/usr/bin/env bash
#
# collect_evidence.sh
#
# Purpose: Assemble a chain-of-custody evidence bundle documenting the
# offensive actions performed against the Scaffold engagement
# (target 10.129.246.248 / scaffold.htb) from the attack workstation side.
#
# This script is DEFENSIVE/DOCUMENTATION tooling. It does not attack
# anything - it only copies, hashes, and manifests files that were
# already produced during the engagement, plus optionally pulls a small
# set of read-only forensic artifacts back from the target over an
# existing authenticated WinRM session (if creds are supplied), so the
# final report can show both attacker-side and target-side evidence.
#
# Usage:
#   ./collect_evidence.sh [--with-target-evidence]
#
# Run this FROM your attack box, in the directory tree where your
# engagement working files live (nmap outputs, exploit scripts, certs,
# msi files, python scripts, bloodhound json, etc). Adjust SEARCH_DIRS
# below if your files are scattered elsewhere.

set -uo pipefail

# ---------------------------------------------------------------------
# Configuration - edit these for your environment
# ---------------------------------------------------------------------
ENGAGEMENT_NAME="Scaffold"
TARGET_IP="10.129.246.248"
TARGET_DOMAIN="scaffold.htb"
ATTACKER_IP="10.10.17.121"

# Directories to search for engagement artifacts. Add/remove as needed.
SEARCH_DIRS=(
    "$HOME"
    "$(pwd)"
    "$HOME/z0n/z0n/posts/Scaffold"
    "$HOME/MDT-XXE-exploit"
)

# File name / extension patterns considered "evidence" for this engagement
PATTERNS=(
    "*.pfx" "*.p12"                       # stolen/forged certificates
    "*nmap*" "*.nmap" "*.gnmap" "*.xml"   # recon scan output
    "*.msi"                               # payload artifacts
    "evil*.ps1" "Invoke-PowerShellTcp*"   # shell payloads
    "exploit.py" "*xxe*"                  # XXE tooling
    "upload_msi.py" "approve_msi.py"      # portal exploitation scripts
    "users.txt" "passwords.txt" "hash"    # spray/crack wordlists & hashes
    "*.ccache"                            # kerberos ticket cache from certipy
    "*_users.json" "*_groups.json" "*_computers.json" "*_domains.json"
    "*_ous.json" "*_gpos.json" "*_containers.json"   # bloodhound collection
    "mdt_wsdl.xml"                        # WSDL pulled from MDT service
    "scaffold_src.zip"                    # exfiltrated portal source
    "*_src.zip"
    "root.txt" "user.txt"                 # flags
)

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTDIR="./evidence_${ENGAGEMENT_NAME}_${TIMESTAMP}"
MANIFEST="${OUTDIR}/MANIFEST.csv"
TIMELINE="${OUTDIR}/TIMELINE.md"
REPORT="${OUTDIR}/SUMMARY.md"

WITH_TARGET_EVIDENCE=false
if [[ "${1:-}" == "--with-target-evidence" ]]; then
    WITH_TARGET_EVIDENCE=true
fi

echo "[*] Starting evidence collection for engagement: ${ENGAGEMENT_NAME}"
echo "[*] Output bundle: ${OUTDIR}"
mkdir -p "${OUTDIR}/artifacts"

# ---------------------------------------------------------------------
# 1. Collect matching files from attacker workstation
# ---------------------------------------------------------------------
echo "[*] Searching for engagement artifacts on attack workstation..."

FOUND_FILES=()
for dir in "${SEARCH_DIRS[@]}"; do
    [[ -d "$dir" ]] || continue
    for pattern in "${PATTERNS[@]}"; do
        while IFS= read -r -d '' f; do
            FOUND_FILES+=("$f")
        done < <(find "$dir" -maxdepth 6 -type f -iname "$pattern" -print0 2>/dev/null)
    done
done

# De-duplicate
mapfile -t FOUND_FILES < <(printf '%s\n' "${FOUND_FILES[@]}" | sort -u)

echo "[*] Found ${#FOUND_FILES[@]} candidate evidence files."

# ---------------------------------------------------------------------
# 2. Copy files preserving relative structure, compute hashes
# ---------------------------------------------------------------------
echo "path,sha256,size_bytes,mtime_utc" > "${MANIFEST}"

for src in "${FOUND_FILES[@]}"; do
    [[ -f "$src" ]] || continue
    base="$(basename "$src")"
    dest="${OUTDIR}/artifacts/${base}"
    # avoid clobbering same-named files from different dirs
    n=1
    while [[ -e "$dest" ]]; do
        dest="${OUTDIR}/artifacts/${base%.*}_${n}.${base##*.}"
        n=$((n+1))
    done
    cp -p "$src" "$dest" 2>/dev/null || continue

    sha256=$(sha256sum "$dest" | awk '{print $1}')
    size=$(stat -c%s "$dest" 2>/dev/null || stat -f%z "$dest")
    mtime=$(date -u -r "$dest" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || stat -c %y "$dest")

    echo "${src} -> artifacts/$(basename "$dest"),${sha256},${size},${mtime}" >> "${MANIFEST}"
    echo "    [+] $(basename "$dest")  sha256=${sha256:0:16}..."
done

# ---------------------------------------------------------------------
# 3. Pull recent relevant shell history (best-effort, current session only)
# ---------------------------------------------------------------------
echo "[*] Exporting recent shell history relevant to the target IP/domain..."
HIST_OUT="${OUTDIR}/artifacts/shell_history_extract.txt"
{
    echo "# Extracted lines from shell history mentioning ${TARGET_IP} / ${TARGET_DOMAIN}"
    echo "# Collected: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo
    for histfile in "$HOME/.bash_history" "$HOME/.zsh_history"; do
        [[ -f "$histfile" ]] || continue
        echo "## From: ${histfile}"
        grep -aE "${TARGET_IP}|${TARGET_DOMAIN}" "$histfile" 2>/dev/null
        echo
    done
} > "${HIST_OUT}"
echo "path,sha256,size_bytes,mtime_utc" >> /dev/null # noop to keep manifest format
sha256=$(sha256sum "${HIST_OUT}" | awk '{print $1}')
size=$(stat -c%s "${HIST_OUT}" 2>/dev/null || stat -f%z "${HIST_OUT}")
echo "(generated),${sha256},${size},$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "${MANIFEST}"

# ---------------------------------------------------------------------
# 4. Optional: pull minimal read-only target-side evidence over WinRM
#    (only if the operator explicitly asks for it and evil-winrm/creds
#    are available - this is READ-ONLY, no destructive/hiding actions)
# ---------------------------------------------------------------------
if $WITH_TARGET_EVIDENCE; then
    echo "[*] --with-target-evidence flag set."
    echo "[*] This step requires you to supply working creds/hash interactively."
    read -rp "    Target username (DOMAIN\\user or user): " TGT_USER
    read -rsp "    Password (leave blank to use NT hash instead): " TGT_PASS
    echo
    read -rp "    NT hash (leave blank if using password): " TGT_HASH

    TARGET_EVID_DIR="${OUTDIR}/artifacts/target_side"
    mkdir -p "${TARGET_EVID_DIR}"

    AUTH_ARGS=()
    if [[ -n "$TGT_HASH" ]]; then
        AUTH_ARGS=(-u "$TGT_USER" -H "$TGT_HASH")
    else
        AUTH_ARGS=(-u "$TGT_USER" -p "$TGT_PASS")
    fi

    echo "[*] Pulling engine/validator/watcher logs (read-only) for the report timeline..."
    # These are documentation pulls only - reading logs the engine itself
    # already wrote, not modifying anything on the target.
    nxc smb "${TARGET_IP}" "${AUTH_ARGS[@]}" \
        --get-file 'Software\Logs\Engine\*' "${TARGET_EVID_DIR}/" 2>/dev/null \
        || echo "    [-] Could not pull engine logs automatically; pull manually via evil-winrm 'download'."

    echo "[*] NOTE: for a full report, also manually 'download' via evil-winrm:"
    echo "        C:\\Software\\Logs\\Engine\\DeployEngine_*.log"
    echo "        C:\\Software\\Logs\\Validator\\ScaffoldPortal_*.log"
    echo "        C:\\Users\\<compromised_user>\\Desktop\\*.txt   (flags, as proof of impact)"
fi

# ---------------------------------------------------------------------
# 5. Write a timeline reconstructed from this engagement's narrative
#    (edit dates/times to match your actual session timestamps if you
#    want a precise chain of custody - placeholders shown here map to
#    the steps performed in this session)
# ---------------------------------------------------------------------
cat > "${TIMELINE}" << 'EOF'
# Engagement Timeline — Scaffold (10.129.246.248 / scaffold.htb)

| Phase | Action | Tooling | Result |
|---|---|---|---|
| Recon | Full TCP port scan | nmap, rustscan | Discovered AD DC + custom portal (443) + MDT MonitorService (9800/9801) |
| Foothold | Validated provided creds j.harris | nxc smb | Confirmed valid, listed SMB shares (DeploymentShare$, REMINST, Y$) |
| Recon | LDAP description field enumeration | nxc ldap -M get-desc-users | Leaked m.carter temp password (account disabled) |
| Recon | RID cycling / user enumeration | impacket-lookupsid | Built full user/group list, surfaced key group names |
| Recon | BloodHound collection | bloodhound-python | Mapped ACL abuse chain (r.wilson -> Helpdesk operator -> m.carter) |
| Exploitation | XXE against MDT MonitorService | custom exploit.py | Leaked svc_deploy/svc_mdt credentials from CustomSettings.ini / Bootstrap.ini |
| Exploitation | Password spray with proof | nxc smb --continue-on-success | Confirmed password reuse: svc_deploy == r.wilson |
| Privesc | ACL abuse: enable + de-quarantine m.carter | bloodyad, impacket-dacledit | m.carter account enabled and usable |
| Privesc | Group nesting for DCOM rights | bloodyad | m.carter added to Endpoint Remote Management via IT |
| Access | Remote code execution via DCOM | impacket-dcomexec | Reverse shell as m.carter; USER FLAG captured |
| Credential theft | PFX certificate exfiltration + cracking | evil-winrm download, pfx2john, john | Cracked shared PFX password |
| Privesc | Certipy PKINIT auth | certipy-ad auth | Retrieved d.cooper NT hash via UnPAC-the-hash |
| Access | Pass-the-hash WinRM | evil-winrm | Interactive shell as d.cooper (Package_Developers, Remote Management Users) |
| Recon | Source code review of ScaffoldPortal | manual review of Services.cs | Identified checklist-bypass logic flaw in ApprovePackageAsync |
| Recon | Deploy engine review | manual review of Deploy-Engine.ps1 | Identified exact Subject/Issuer/ProductCode trust requirements |
| Privesc | AD CS template abuse (ESC-style) | certipy-ad find | Identified PackagingCodeSigning template: EnrolleeSuppliesSubject + Domain Computers enrollable |
| Privesc | Delegated OU abuse (bypass MachineAccountQuota=0) | impacket-dacledit, bloodyad | Created rogue computer account evilpc$ under Dev_Machines OU |
| Privesc | Certificate forgery | certipy-ad req | Issued cert with forged Subject=CN=Package_Developers, legitimately signed by scaffold-DC-CA |
| Weaponization | Malicious MSI construction | msfvenom, msitools (msibuild), osslsigncode | Built and signed trojanized "PuTTY" MSI passing all engine checks |
| Exploitation | Portal API abuse | custom python (NTLM upload/approve scripts) | Uploaded as d.cooper, approved as m.chen (hash reuse), bypassing checklist enforcement |
| Impact | Automatic SYSTEM execution | Deploy-Engine.ps1 (target-scheduled) | SYSTEM reverse shell; ROOT FLAG captured |

EOF
echo "[*] Timeline written to ${TIMELINE}"

# ---------------------------------------------------------------------
# 6. Write a summary report header
# ---------------------------------------------------------------------
cat > "${REPORT}" << EOF
# Evidence Bundle Summary

**Engagement:** ${ENGAGEMENT_NAME}
**Target:** ${TARGET_IP} (${TARGET_DOMAIN})
**Attacker IP:** ${ATTACKER_IP}
**Collection timestamp (UTC):** ${TIMESTAMP}
**Collected by:** $(whoami)@$(hostname)

## Contents

- \`artifacts/\` — all recon output, exploit scripts, stolen/forged certificates,
  payloads, wordlists, hash files, exfiltrated source code, and captured flags
  found on the attack workstation.
- \`MANIFEST.csv\` — SHA-256 hash, size, and modification time of every file in
  this bundle, for chain-of-custody purposes.
- \`TIMELINE.md\` — reconstructed phase-by-phase timeline of the engagement,
  mapping each action to the tooling used and the result obtained.

## Chain of custody note

All files in \`artifacts/\` were copied (not moved) from their original
locations with \`cp -p\` to preserve original modification timestamps.
Hashes in MANIFEST.csv should be independently re-verified before this
bundle is submitted as part of a formal report, and the bundle itself
should be hashed as a whole (e.g. \`tar czf - ${OUTDIR} | sha256sum\`)
once finalized, with that hash recorded separately (e.g. in the report
body or an email to the client) to prove the bundle was not altered
after collection.

## Sensitive content warning

This bundle contains cleartext and hashed credentials discovered during
the engagement (users.txt / passwords.txt / hash / *.ccache / *.pfx),
private keys, and full source code exfiltrated from the target
(scaffold_src.zip). Handle per your engagement's data handling policy —
encrypt at rest, restrict access, and delete per the agreed retention
period after report delivery and client acceptance.
EOF

echo
echo "[+] Evidence collection complete."
echo "[+] Bundle: ${OUTDIR}"
echo "[+] Files collected: ${#FOUND_FILES[@]}"
echo "[+] Manifest: ${MANIFEST}"
echo
echo "[*] To seal the bundle for chain of custody:"
echo "    tar czf ${OUTDIR}.tar.gz ${OUTDIR}"
echo "    sha256sum ${OUTDIR}.tar.gz > ${OUTDIR}.tar.gz.sha256"
