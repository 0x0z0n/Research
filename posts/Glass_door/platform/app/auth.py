"""Firebase-backed auth for the platform.

This is the externalized shim; production wires Firebase Admin SDK in
init() via FIREBASE_SERVICE_ACCOUNT_JSON. Sessions are stored in Redis.
"""
from __future__ import annotations

import os


_initialized = False


def init() -> None:
    global _initialized
    if _initialized:
        return
    sa = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not sa:
        return
    _initialized = True


def current_user_email() -> str | None:
    """Resolve the email of the currently authenticated user."""
    return None
