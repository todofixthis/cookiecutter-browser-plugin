[![CI](https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/actions/workflows/build.yml/badge.svg)](https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/actions/workflows/build.yml)
[![Docs](https://readthedocs.org/projects/{{ cookiecutter.package_name }}/badge/?version=latest)](https://{{ cookiecutter.package_name }}.readthedocs.io/)

# {{ cookiecutter.project_name }}

{{ cookiecutter.project_short_description }}

Targets Manifest V3 on both Firefox (primary) and Chromium.

## Getting Started

TODO

## Maintainers

To install for local development:

1. [Install pnpm](https://pnpm.io/installation) (only needs to be done once).
2. Install dependencies: `pnpm install` (also installs the pre-commit hook via husky).

### Running Tests and Type Checker

```bash
pnpm test        # unit tests (vitest)
pnpm test:e2e     # e2e tests (Playwright, Chromium only — see docs/adr/004)
pnpm typecheck
```

### Building

```bash
pnpm build            # Chromium
pnpm build:firefox    # Firefox
```

### Documentation

```bash
pnpm typedoc
```

## Releases

See the `release` agent skill (`.agents/skills/release/SKILL.md`) for the
full process — version bump, packaging for both browsers, GPG-signed
artefacts, and GitHub release creation. Store submission (AMO, Chrome Web
Store) is a manual, developer-run step.
