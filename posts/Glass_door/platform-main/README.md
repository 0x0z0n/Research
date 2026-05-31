# Cloud Security Championship — Platform

This is the open-sourced source code for the Cloud Security Championship
platform that runs at <https://cloudsecuritychampionship.com>.

We open-sourced it as the final challenge of the year. We're confident in
how we built it, but we know nothing is perfect — see if you can spot
anything that shouldn't be there.

## What's in this repo

```
app/                  FastAPI backend serving the platform
  ctfs/               CTF definitions (challenge metadata + flag logic)
  routes/             HTTP endpoints
  verifier.py         HMAC-based flag verification for external-solve challenges
scripts/              Operator tooling
  mark_solve.py       Compute a participant's flag for a given challenge
tests/                CI test scripts
buildspec.yml         Build manifest (legacy; CodeBuild project uses inline spec)
```

Infrastructure (Terraform for AWS resources, GitLab admin config) lives in a
separate private repo. Reach out to @nir for access if you need it.

## Local dev setup

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Contributing

External contributions welcome — open an MR against `main`. CI runs the test
suite via AWS CodeBuild on push and on every merge request update.

Code review is required from a member of the Wiz CTF team before merge.

## Maintainers

- @nir (CTF lead, infra)

## License

Apache 2.0. See LICENSE.
