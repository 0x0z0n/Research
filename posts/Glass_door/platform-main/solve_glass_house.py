import os
import hmac
import hashlib
import subprocess
import sys

CHALLENGE_ID = 12


def compute_flag(signing_key: str, email: str) -> str:
    msg = f"{CHALLENGE_ID}:{email.strip().lower()}".encode()
    digest = hmac.new(
        signing_key.encode(),
        msg,
        hashlib.sha256
    ).hexdigest()
    return f"WIZ_CTF{{{digest[:24]}}}"


def check_repo():
    print("[*] Checking repo layout...\n")

    required = ["app", "scripts", "tests", "buildspec.yml"]
    for r in required:
        print(f" - {r}: {'OK' if os.path.exists(r) else 'MISSING'}")

    print("\n[*] Tests directory contents:")
    os.system("ls -R tests || true")


def try_local_emulation():
    print("\n[*] Trying safe local CI simulation...\n")

    # CI does:
    # python -c "from app.main import app"
    try:
        import app.main  # noqa
        print("[+] app imports successfully (CI simulation OK)")
    except Exception as e:
        print("[-] app import failed:", e)


def main():
    print("\n=== Glass House Solver (CTF workflow helper) ===\n")

    check_repo()
    try_local_emulation()

    print("\n[*] If you already extracted the signing key from CI, enter it:")
    key = input("Signing key (or blank to exit): ").strip()
    if not key:
        print("[-] No key provided. Exiting.")
        sys.exit(0)

    email = input("Your email: ").strip()

    flag = compute_flag(key, email)

    print("\n=== FINAL FLAG ===")
    print(flag)


if __name__ == "__main__":
    main()
