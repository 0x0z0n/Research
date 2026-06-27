"""Cloud Security Championship platform — FastAPI entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from app import auth
from app.ctfs import cloudchampions
from app.routes import api, challenge

app = FastAPI(
    title="Cloud Security Championship",
    description="Wiz's year-long cloud security CTF",
    version="2026.5",
)

app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(challenge.router, prefix="/challenge", tags=["challenge"])

# CTF registration — auto-discovers modules under app.ctfs.
auth.init()
cloudchampions.register(app)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
