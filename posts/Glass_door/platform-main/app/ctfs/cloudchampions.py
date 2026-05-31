"""Cloud Security Championship — challenge registry (excerpt).

This file is heavily redacted in the public repo. The full year of
challenges is defined here; for the open-source release we ship only the
last challenge's metadata as an example of the schema.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI


cloudchampions: dict[str, Any] = {
    "name": "cloudchampions",
    "ctf_type": "monthly",
    "challenges": [
        # Challenges 1-11 redacted for the public release.
        {
            "challenge_id": "f0e7d28a-7c1a-4c41-8a13-ec5119e8a2ee",
            "title": "Glass House",
            "summary": "For our finale we open-sourced the platform. Find the bug we shipped.",
            "description": [
                "We open-sourced this CTF platform's source code as the year-closing challenge.",
                "Browse the repo at https://git.cloudsecuritychampionship.com/cloudsecuritychampionship/platform",
                "Find a way to make the platform itself acknowledge that you've solved this challenge.",
            ],
            "flag_format": "WIZ_CTF{...}",
            "flag_verifier": "hmac",  # see app/verifier.py
            "points": 50,
        },
    ],
}


def register(app: FastAPI) -> None:
    """Register CTF routes / metadata with the app."""
    app.state.ctfs = {cloudchampions["name"]: cloudchampions}
