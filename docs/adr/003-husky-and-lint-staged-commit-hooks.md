---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/package.json", "{{ cookiecutter.github_project_name }}/.husky/pre-commit"]
summary: Use husky + lint-staged for commit hooks, running the full typecheck/test suite (not just staged-file lint) to match autohooks' thoroughness.
---

# 003: Use husky + lint-staged for Commit Hooks

## Context

cookiecutter-py's generated projects use `autohooks` (mode `pythonpath`,
not the `pre-commit` framework) to run `black`/`mypy`/`pytest`/`ruff` on
every commit — the *whole* suite, not just a diff of staged files.
`autohooks` is Python-specific tooling with no JS port.

## Decision

`husky` + `lint-staged`, the standard JS pairing. `lint-staged` alone only
lints/formats staged files, which is narrower than what `autohooks`
does — so `.husky/pre-commit` also runs the full `pnpm typecheck` and
`pnpm test` on every commit, matching `autohooks`' actual thoroughness
rather than lint-staged's usual (staged-files-only) convention.

## Consequences

- Commits are slower than a lint-staged-only setup would be (a full
  typecheck + test run, not just the staged diff) — an intentional
  trade-off for parity with cookiecutter-py's own commit-time guarantees.
- `package.json`'s `prepare` script (`husky`) installs the hook on
  `pnpm install`, mirroring `uv run autohooks activate` needing to be run
  once per clone for the Python template.
