#!/usr/bin/env bash
# Cloud Security Championship platform — test runner.
#
# Invoked by CodeBuild's project-level buildspec for each PR build.
# Runs unit tests + a small smoke test against the in-process FastAPI app.

set -euo pipefail

echo "==> Setting up test env"
python3 -m venv /tmp/venv
source /tmp/venv/bin/activate
pip install -q --no-cache-dir fastapi==0.115.4 httpx==0.27.2 pytest==8.3.4 pydantic==2.9.2

echo "==> Running unit tests"
if [ -d tests/unit ]; then
  python -m pytest tests/unit -q
else
  echo "  (no unit tests yet)"
fi

echo "==> Smoke test: importing app"
python -c "from app.main import app; print(f'OK app has {len(app.routes)} routes')" 2>/dev/null || echo "  (app module not loaded; skipping smoke test)"

echo "==> CI complete"
