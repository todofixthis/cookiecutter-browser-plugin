---
name: rotate-node-version
description: Use when bumping the minimum supported Node version — updating package.json's engines field, CI's node-version, and docs.
---

# Rotate Node Version

Update the pinned Node floor consistently when bumping it.

## Locations to update

- **`package.json`** — `engines.node`
- **`.github/workflows/build.yml`** and **`.readthedocs.yaml`** — the `node-version`/`tools.nodejs` value
- **`README.md`** — any stated Node requirement

## After editing

Search for stray references:

```bash
rg '"node": ">=' --glob "package.json"
rg "node-version|nodejs:" --glob "*.yml" --glob "*.yaml"
```

Then verify everything still passes:

```bash
pnpm install
pnpm lint && pnpm typecheck && pnpm test && pnpm build && pnpm build:firefox
```
