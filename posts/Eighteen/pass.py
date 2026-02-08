#!/usr/bin/env python3
import hashlib
from multiprocessing import Pool, cpu_count

# ---- Hash components ----
SALT = "AMtzteQIG7yAbZIa"
ITERATIONS = 600000
TARGET_HASH = "0673ad90a0b4afb19d662336f0fce3a9edd0b7b19193717be28ce4d66c887133"

# ---- Your wordlist path ----
WORDLIST = "/usr/share/wordlists/rockyou.txt"


def check_password(password: bytes):
    """Check one password candidate."""
    try:
        computed = hashlib.pbkdf2_hmac(
            'sha256',
            password,
            SALT.encode(),
            ITERATIONS
        )
        if computed.hex() == TARGET_HASH:
            return password.decode(errors="ignore")
    except Exception:
        pass
    return None


def main():
    print(f"[+] Using wordlist: {WORDLIST}")
    print("[+] Starting PBKDF2-SHA256 cracking...")

    with open(WORDLIST, "rb") as f:
        passwords = (line.strip() for line in f)

        with Pool(cpu_count()) as pool:
            for result in pool.imap_unordered(
                check_password, passwords, chunksize=500
            ):
                if result:
                    print(f"[+] PASSWORD FOUND: {result}")
                    pool.terminate()
                    return

    print("[-] No match found.")


if __name__ == "__main__":
    main()
