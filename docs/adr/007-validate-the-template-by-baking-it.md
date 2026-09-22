---
status: Accepted
date: 2026-09-10
scope: [test/, .github/workflows/generate-and-validate.yml]
summary: Validate the template by actually baking a project with cookiecutter and running its own lint/type-check/unit-test/build(-both-targets)/e2e/docs-build, not just static checks on the template files — matching cookiecutter-py's docs/adr/004.
---

# 007: Validate the Template by Baking It

## Context

`test/test_bake.py` (Task 2) checks the raw baked output's shape —
valid `package.json`, the right files present, symlinks intact — but
never actually installs dependencies or runs the generated project's own
tooling. A change to `package.json`'s dependency versions, `wxt.config.ts`,
or any CI/docs config could silently break what
`cookiecutter gh:todofixthis/cookiecutter-browser-plugin` produces, the
same gap cookiecutter-py's own docs/adr/004 closed for the Python
template.

## Decision

Add `.github/workflows/generate-and-validate.yml`: bakes a real project
and runs *that project's own* `pnpm install`, `pnpm lint`, `pnpm
typecheck`, `pnpm test`, `pnpm build`/`pnpm build:firefox`, `pnpm exec
playwright install --with-deps chromium` + `pnpm test:e2e`, and `pnpm
typedoc` — the same commands a human maintainer of a generated project
would run. `test/test_bake.py` stays the fast, always-run check; this
workflow is the slower, end-to-end one.

## Consequences

- CI now depends on network access to install the generated project's
  npm dependencies and Playwright's browser binary mid-run.
- Future changes to the templated project's `package.json`/CI/docs need
  to keep working under this workflow, not just render without Jinja
  errors.
