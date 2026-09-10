---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/.github/workflows/build.yml"]
summary: CI runs a single pinned Node LTS version, not a support matrix — Node is this project's build tooling, not the runtime the shipped extension runs under.
---

# 002: Support a Single Pinned Node Version, Not a Matrix

## Context

cookiecutter-py's generated projects test against a rolling 3-version
Python matrix (its own docs/adr/001) because the *shipped artefact* — a
Python package — runs directly on whichever Python its users have
installed. A browser extension's shipped artefact is the built
`.output/*` bundle, which runs inside the browser's own JavaScript
engine; Node only builds it. There is no equivalent "which Node does the
user have" question a matrix would answer.

## Decision

Pin a single Node version (`cookiecutter.node_version`, templated into
`package.json`'s `engines.node`, CI's `node-version`, and
`.readthedocs.yaml`'s `tools.nodejs`), kept current by the
`rotate-node-version` skill rather than tested across a range.

## Consequences

- CI has no Python-ADR-001-style version matrix — `build.yml`'s jobs each
  run once, against the one pinned Node version.
- A contributor building with a different local Node version than the
  pin isn't validated by CI either way; `engines.node` in `package.json`
  is advisory (npm/pnpm warn, don't block) unless `engine-strict` is set,
  which this template doesn't set — matching how cookiecutter-py doesn't
  hard-block an out-of-range local Python either.
