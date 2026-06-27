"""Per-challenge routes (description, hints, etc.)."""
from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/{challenge_id}")
async def describe(challenge_id: int, request: Request) -> dict:
    ctfs = getattr(request.app.state, "ctfs", {})
    for ctf in ctfs.values():
        for ch in ctf["challenges"]:
            if ch.get("number") == challenge_id:
                return ch
    return {"error": "not found"}
