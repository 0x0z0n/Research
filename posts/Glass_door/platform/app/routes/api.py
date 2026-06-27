"""Public API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import auth, verifier


router = APIRouter()


def get_user_email() -> str:
    email = auth.current_user_email()
    if not email:
        raise HTTPException(status_code=401, detail="not authenticated")
    return email


@router.post("/submit-flag")
async def submit_flag(challenge: int, flag: str, email: str = Depends(get_user_email)) -> dict:
    """Accept a flag submission, validate against the per-challenge rule."""
    # For external-solve challenges (Challenge 12 family), the flag is
    # HMAC'd against the participant's email; recompute and compare.
    if verifier.verify(challenge, email, flag):
        return {"ok": True, "challenge": challenge}
    raise HTTPException(status_code=400, detail="incorrect flag")
