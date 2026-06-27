"""HMAC-based flag verifier for external-solve challenges.

External-solve challenges (currently only #12) bind their flag to the
participant's registered email so that each participant has a unique flag
string. This module loads the signing key from SSM once at startup and
exposes `verify(challenge, email, submitted)` for the flag-submission path.

See scripts/mark_solve.py for the generator side.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from functools import lru_cache


@lru_cache(maxsize=8)
def _signing_key(challenge: int) -> str:
    # Production fetches from SSM via boto3. Local dev can override.
    override = os.environ.get(f"CTF_CHALLENGE_{challenge}_SIGNING_KEY")
    if override:
        return override
    import boto3
    ssm = boto3.client("ssm")
    return ssm.get_parameter(
        Name=f"/ctf/challenge-{challenge}/signing-key",
        WithDecryption=True,
    )["Parameter"]["Value"]


def _expected_flag(challenge: int, email: str) -> str:
    msg = f"{challenge}:{email.strip().lower()}".encode("utf-8")
    digest = hmac.new(
        _signing_key(challenge).encode("utf-8"), msg, hashlib.sha256
    ).hexdigest()
    return f"WIZ_CTF{{{digest[:24]}}}"


def verify(challenge: int, email: str, submitted: str) -> bool:
    return hmac.compare_digest(_expected_flag(challenge, email), submitted.strip())
