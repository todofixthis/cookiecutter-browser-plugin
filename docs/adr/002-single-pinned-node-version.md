---
status: Accepted
date: 2026-09-10
scope: ["cookiecutter.json", "{{ cookiecutter.github_project_name }}/.github/workflows/build.yml", "{{ cookiecutter.github_project_name }}/.nvmrc", "{{ cookiecutter.github_project_name }}/.readthedocs.yaml", "{{ cookiecutter.github_project_name }}/package.json"]
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

Pin a single Node version — the current LTS major — kept current by the
`rotate-node-version` skill rather than tested across a range.
`cookiecutter.node_version` drives it: a generated project gets it as
`.nvmrc`, which every CI job reads via `node-version-file`, and as
`package.json`'s `engines.node` and `.readthedocs.yaml`'s `tools.nodejs`,
which can't read `.nvmrc`. The one exception is `@types/node`, a literal
version whose major must match — bumping it means regenerating
`pnpm-lock.yaml`, which pins the exact release.

## Consequences

- The `rotate-node-version` skill is for generated projects; don't follow
  it in this repo, where `.nvmrc` and `package.json` hold Jinja. Here, a
  rotation bumps `cookiecutter.node_version` and the template's
  `@types/node`, then regenerates the template's `pnpm-lock.yaml` by baking
  a project to a scratch directory, running `pnpm install` there, and
  copying `pnpm-lock.yaml` (and `pnpm-workspace.yaml`) back. Running pnpm in
  the unrendered template directory would leave `node_modules` behind, and
  cookiecutter renders every file it finds on the next bake.

- CI has no Python-ADR-001-style version matrix — `build.yml`'s jobs each
  run once, against the one pinned Node version.
- A contributor building with a different local Node version than the
  pin isn't validated by CI either way; `engines.node` in `package.json`
  is advisory (npm/pnpm warn, don't block) unless `engine-strict` is set,
  which this template doesn't set — matching how cookiecutter-py doesn't
  hard-block an out-of-range local Python either.
