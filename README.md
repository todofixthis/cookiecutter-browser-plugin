# cookiecutter-browser-plugin

[![CI](https://github.com/todofixthis/cookiecutter-browser-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-browser-plugin/actions/workflows/ci.yml)
[![Generate and Validate](https://github.com/todofixthis/cookiecutter-browser-plugin/actions/workflows/generate-and-validate.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-browser-plugin/actions/workflows/generate-and-validate.yml)

A [cookiecutter](https://cookiecutter.readthedocs.io/) template for new browser extension projects, wired up with `WXT`, `pnpm`, Playwright, TypeDoc/ReadTheDocs docs, and the shared `phx` agent tooling from the start. Firefox is the primary target; Chromium is also supported.

## Usage

```bash
uv tool install cookiecutter  # once
cookiecutter gh:todofixthis/cookiecutter-browser-plugin
```

You'll be prompted for a project name, a short description, and an author name/email (defaults to Phoenix Zerin's); the current year is filled in automatically.

## After creating the GitHub repo

- **Renovate.** If Renovate is installed for selected repositories only, add the repo at <https://github.com/settings/installations> → Renovate → Configure → Repository access. Until then the repo gets no dependency updates, and nothing says so.
- **Watching.** Unless the repo already shows as watched, click Watch → All Activity on it. A watch belongs to a person, not the repo, so the todofixthis Terraform module leaves it out by design ([its ADR 005](https://github.com/todofixthis/terraform-github-repository/blob/develop/docs/adr/005-keep-personal-preferences-out-of-the-module.md)).

## What you get

- `WXT` (Vite-based, cross-browser Manifest V3) + `pnpm` packaging, `vitest` unit tests, `eslint`/`prettier` (via `husky` + `lint-staged`, run in full on every commit — not just staged files)
- Playwright e2e tests against the built Chromium extension (Firefox e2e isn't automatable — see `docs/adr/004`)
- TypeDoc docs on ReadTheDocs, GitHub Actions CI (lint, type-check, unit test, build both targets, e2e, docs), Renovate for dependency/Action updates
- `AGENTS.md`/`CLAUDE.md`, an ADR workflow under `docs/adr/`, and the `phx@todofixthis` skill marketplace enabled out of the box
- A guided `release` skill covering version bumps, GPG-signed release artefacts, and packaging for both the Chrome Web Store and Mozilla AMO (store submission itself stays a manual, developer-run step)

## Developing this template

See `AGENTS.md` for the dev workflow (`uv sync --group=dev`, `uv run pytest` bakes the template and checks the output, `uv run mypy hooks test`, `uv run ruff check hooks test`).
