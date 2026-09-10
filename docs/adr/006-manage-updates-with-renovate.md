---
status: Accepted
date: 2026-09-10
scope: [renovate.json, "{{ cookiecutter.github_project_name }}/renovate.json"]
summary: Manage dependency and GitHub Action updates via Renovate, matching cookiecutter-py and its sibling repos.
---

# 006: Manage Updates with Renovate

## Context

cookiecutter-py (its own docs/adr/003) and its sibling repos use a single
`renovate.json` extending `config:recommended` plus
`helpers:pinGitHubActionDigests`, which pins Actions to commit SHAs (with
a version-tag comment) rather than floating tags — matching the SHA pins
already used in this repo's and the templated project's own CI workflows
(Tasks 3, 4, 5, 7, 8).

## Decision

Same config, in both this repo's own root and the generated project:
`{"extends": ["config:recommended", "helpers:pinGitHubActionDigests"]}`.
`config:recommended` covers the npm ecosystem (the templated project's
`package.json`) the same way it already covers cookiecutter-py's own
`pyproject.toml` and the templated Python project's dependencies — no
npm-specific Renovate configuration is needed.

## Consequences

- Renovate needs the GitHub App installed on this repo (and, once
  generated projects exist, on each of those too) — a one-time, per-repo
  setup step outside this template's own files.
- The SHA pins already in `ci.yml`/`build.yml` are a snapshot Renovate
  will keep moving forward from here.
