#!/usr/bin/env python3
"""
mark_solve.py - Compute a participant's flag for a Cloud Security Championship
challenge.

Flags for "external-solve" challenges (challenges that ship a piece of the
solve logic outside the platform itself) are bound to the participant's email
via an HMAC over the signing key. This means each participant gets a unique
flag string, and the platform verifies by recomputing the HMAC for the
logged-in user's registered email.

The signing key lives in AWS SSM Parameter Store under
    /ctf/challenge-<N>/signing-key
as a SecureString. Only the relevant CodeBuild service role has
ssm:GetParameter on that path.

Usage:
    # Inside a CI build (uses build's IAM role to fetch from SSM):
    python scripts/mark_solve.py --challenge 12 --email alice@example.com

    # Locally with a manually-provided key (for verification / debugging):
    python scripts/mark_solve.py --challenge 12 --email alice@example.com \\
        --secret <signing-key-hex>

The platform applies the same HMAC computation in app/verifier.py to validate
submitted flags.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import sys


def get_signing_key_from_ssm(challenge: int) -> str:
    """Fetch the signing key from SSM Parameter Store."""
    import boto3
    ssm = boto3.client("ssm")
    resp = ssm.get_parameter(
        Name=f"/ctf/challenge-{challenge}/signing-key",
        WithDecryption=True,
    )
    return resp["Parameter"]["Value"]


def compute_flag(signing_key: str, challenge: int, email: str) -> str:
    msg = f"{challenge}:{email.strip().lower()}".encode("utf-8")
    digest = hmac.new(signing_key.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return f"WIZ_CTF{{{digest[:24]}}}"


def main() -> int:
    p = argparse.ArgumentParser(description="Compute a per-participant CTF flag.")
    p.add_argument("--challenge", type=int, required=True, help="Challenge number (e.g. 12)")
    p.add_argument("--email", required=True, help="Participant's registered email")
    p.add_argument(
        "--secret",
        help="Signing key (hex). If omitted, fetched from SSM via boto3.",
    )
    args = p.parse_args()

    secret = args.secret or get_signing_key_from_ssm(args.challenge)
    print(compute_flag(secret, args.challenge, args.email))
    return 0


if __name__ == "__main__":
    sys.exit(main())
