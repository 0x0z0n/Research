from cryptography.fernet import Fernet
import json
import os

key = b'Sk_LYVtT4BMC4J71E5cvaDLoH3JIU7f03QubERq8zoQ='
f = Fernet(key)

for filename in os.listdir("data"):
    if not filename.endswith(".secret"):
        continue

    try:
        with open(os.path.join("data", filename), "rb") as fh:
            env = json.loads(
                f.decrypt(fh.read())
            )["environment_variables"]

        if "FLAG" in env:
            print(f"{filename}: {env['FLAG']}")

    except Exception:
        pass
