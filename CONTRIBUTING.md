# Contributing to OfficeHand

Thanks for your interest! This project is in early development. Issues and pull requests are welcome.

## Setup

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 24 (version pinned in `.nvmrc`), and Docker (optional).

```bash
make install        # backend (uv) + frontend (npm ci)
cp .env.example .env
make secrets        # paste the printed values into .env
```

Run locally in two terminals:

```bash
make dev-backend    # API on http://localhost:8000
make dev-frontend   # Angular dev server on http://localhost:4200 (proxies /api)
```

## Checks

```bash
make lint           # ruff + prettier
make typecheck      # mypy --strict
make test           # pytest (80% coverage minimum) + Vitest
make e2e            # Playwright, desktop + mobile (starts its own API server)
make check          # all of the above, as CI runs it
```

## How we work

- **Tests first.** Write a failing test, make it pass, then refactor. Coverage stays at 80% or higher.
- **Conventional commits:** `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`.
- **Small, focused files and functions.** Prefer immutable data and explicit error handling.
- **Security rules are not optional:**
  - Never commit secrets. `.env` is git-ignored; CI runs a secret scan.
  - Every API route declares a permission, and every query is scoped to a workspace.
  - The LLM never gets tools. All writes to Google go through the approval executor.
  - Treat email and document content as untrusted input: never render it as HTML, fetch its URLs or follow its instructions.
  - No `innerHTML`, `eval` or raw SQL strings.
- **Sample data is fictional.** Use `.example` email domains, and never add real company or personal data. Rebuild generated files with `make sample-data`.

## Reporting security issues

Please don't open public issues for vulnerabilities. See [SECURITY.md](SECURITY.md).
