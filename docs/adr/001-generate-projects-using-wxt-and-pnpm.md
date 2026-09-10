---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/package.json", "{{ cookiecutter.github_project_name }}/wxt.config.ts"]
summary: Generate browser-extension projects using WXT (a Vite-based cross-browser WebExtension framework) and pnpm, instead of a hand-maintained manifest.json plus web-ext.
---

# 001: Generate Projects Using WXT + pnpm Instead of Raw Manifest/web-ext

## Context

Firefox and Chromium diverge on Manifest V3 in ways a single hand-written
`manifest.json` can't paper over: Chromium requires
`background.service_worker`; Firefox, which doesn't support MV3 service
workers, requires `background.scripts`. A raw-manifest template would need
either two manifests or Jinja conditionals scattered through one, both of
which drift the moment a contributor edits only the browser they're testing
against.

## Options

### Option 1: Hand-maintained manifest.json + web-ext

Author `manifest.json` directly, using `web-ext build`/`web-ext run` for
Firefox packaging and a second, separately-maintained Chromium manifest.

**Pros:** No framework dependency; full manual control.
**Cons:** Two manifests (or one full of conditionals) to keep in sync by
hand; no bundler, so any non-trivial TypeScript/asset pipeline is
hand-rolled on top.
**Risks:** The exact failure mode this ADR exists to avoid — the two
manifests silently diverging.

### Option 2: WXT + pnpm (Accepted)

WXT is a Vite-based framework purpose-built for cross-browser
WebExtensions: one `entrypoints/` source tree, and `wxt build -b <target>`
emits the correct manifest shape per target from the same source. It also
generates TypeScript types for the WebExtension APIs and ships a Vitest
plugin (`wxt/testing/vitest-plugin`) for mocking `browser.*` in unit tests.

**Pros:** Single source tree for both browsers; built-in dev server with
hot reload; first-class TypeScript and testing support.
**Cons:** A framework dependency and its conventions to learn, instead of
the bare WebExtension APIs.
**Risks:** WXT is pre-1.0 (`0.x`); breaking changes are possible between
minor versions — mitigated by Renovate (ADR 006) surfacing them for review
rather than auto-merging silently.

## Decision

Option 2. pnpm is WXT's documented package manager of choice and the
fastest of the mainstream options; both are pinned via `package.json`'s
`packageManager` field (Corepack) so CI and contributors resolve the same
version.

## Consequences

- The generated project has no `manifest.json` of its own —
  `wxt.config.ts` is the single source WXT compiles into a manifest per
  build target.
- `browser_specific_settings.gecko.id` is required for a stable Firefox
  extension ID across rebuilds/AMO submissions; templated as
  `{{ cookiecutter.gecko_extension_id }}`. Firefox has also required
  `browser_specific_settings.gecko.data_collection_permissions` for new
  extensions since 3 November 2025 — confirmed by a real `wxt build -b
  firefox`, which warns without it; the placeholder extension declares
  `required: ["none"]` since it collects nothing.
- Contributors need `wxt prepare` (wired as `package.json`'s
  `postinstall`) before `tsc` can resolve WXT's generated types.
