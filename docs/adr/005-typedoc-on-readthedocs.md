---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/typedoc.json", "{{ cookiecutter.github_project_name }}/.readthedocs.yaml"]
summary: Host TypeDoc-generated API docs on ReadTheDocs via a custom Node build, keeping the same hosting capability as cookiecutter-py's Sphinx docs instead of switching to GitHub Pages.
---

# 005: Host TypeDoc API Docs on ReadTheDocs via a Custom Build

## Context

ReadTheDocs' built-in support targets Sphinx and MkDocs; TypeDoc is
neither. RTD's v2 config schema still supports a project that provisions
its own toolchain (here, Node via `tools.nodejs`) and overrides the
"generate HTML" step (`build.jobs.build.html`) with an arbitrary command,
while RTD continues to manage everything else (the build environment,
versioned URLs, PR previews).

## Decision

`.readthedocs.yaml` sets `tools.nodejs`, installs dependencies via
`jobs.post_install` (`corepack enable && pnpm install --frozen-lockfile`),
and overrides `jobs.build.html` to run
`pnpm exec typedoc --out $READTHEDOCS_OUTPUT/html` — the same shape as
cookiecutter-py's `.readthedocs.yaml`, which sets `tools.python` and a
`post_install` job, just with TypeDoc's own output flag standing in for
Sphinx's `make html`.

## Consequences

- Docs hosting stays like-for-like with cookiecutter-py (same platform,
  same badge, same versioned-docs URL shape) rather than moving to GitHub
  Pages.
- TypeDoc only documents the TypeScript source under `entryPoints`
  (`entrypoints/background.ts`, `entrypoints/popup/main.ts`) — unlike
  Sphinx, it has no toctree/prose-page mechanism, so anything that would
  have been a Sphinx `.rst` page (a migration guide, for instance) lives
  in the repo and is linked from `README.md` instead (see the `release`
  skill).
