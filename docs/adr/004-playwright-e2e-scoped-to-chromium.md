---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/playwright.config.ts", "{{ cookiecutter.github_project_name }}/test/e2e/"]
summary: Playwright e2e coverage is Chromium-only — Playwright cannot load unpacked WebExtensions in Firefox. Firefox behaviour is covered by unit tests plus manual/web-ext run smoke-testing, not automated e2e.
---

# 004: Scope Playwright e2e to Chromium Only

## Context

Playwright's documented extension-testing pattern —
`chromium.launchPersistentContext()` with `--load-extension` — is
Chromium-specific. Playwright does not support loading an unpacked
WebExtension into its Firefox build the same way; this is a Playwright
limitation, not a WXT one; WXT itself builds a correct Firefox target
either way.

## Decision

Scope `test/e2e/` to Chromium only, rather than silently having no e2e
coverage at all or claiming Firefox coverage that doesn't exist. Firefox
behaviour is exercised by the shared Vitest unit tests (which don't
depend on either browser's extension-loading mechanics) plus manual
`web-ext run`/AMO review-queue smoke-testing before a release.

## Consequences

- `build.yml`'s `e2e` job builds and tests Chromium only; there is no
  Firefox equivalent job to add later without new tooling (e.g.
  Selenium/geckodriver), which is out of scope for this template.
- The `release` skill has no Firefox e2e step to reference, and none to
  add — Firefox correctness ahead of a release rests on the shared unit
  tests plus `pnpm build:firefox` succeeding, not on an automated e2e
  gate the skill could point to.
