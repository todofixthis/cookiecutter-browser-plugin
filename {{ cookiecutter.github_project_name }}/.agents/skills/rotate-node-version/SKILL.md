---
name: rotate-node-version
description: Use when moving to a new Node LTS release — updating .nvmrc, package.json's engines and @types/node, ReadTheDocs' nodejs version, and docs.
---

# Rotate Node Version

This project pins the current Node LTS major. `.nvmrc` is the source of truth: every CI job reads it via `node-version-file`. The locations below can't read `.nvmrc`, so keep them on the same major.

## Locations to update

- **`.nvmrc`** — the Node major
- **`package.json`** — `engines.node`, and `@types/node` to the latest release of the same major; then `pnpm install` and commit the updated `pnpm-lock.yaml` with it, or CI's `--frozen-lockfile` install fails
- **`.readthedocs.yaml`** — `tools.nodejs`
- **`README.md`** — any stated Node requirement

## After editing

Before committing, search for the old major (read from the last committed `.nvmrc`) to catch anything left behind:

```bash
rg --hidden -n "\b$(git show HEAD:.nvmrc)\b" -g '!pnpm-lock.yaml' -g '!.git' || echo "none left"
```

Unrelated hits (e.g. `ubuntu-24.04`) can stay.

Then verify everything still passes:

```bash
pnpm install
pnpm verify
```

`verify` in `package.json` is the single source of truth for "test all the things" — update it there, not here, if the set of checks changes.
