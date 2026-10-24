---
status: Accepted
date: 2026-10-24
scope: [renovate.json, "{{ cookiecutter.github_project_name }}/package.json", "{{ cookiecutter.github_project_name }}/renovate.json"]
summary: Pin the template's typescript as the tilde range ~6.0.3, so Renovate replaces rather than widens it, and have Renovate withhold TypeScript 7, rather than adopting TypeScript 7 or letting the range span both majors.
revisit-when: typescript-eslint accepts TypeScript 7 as a peer; typedoc accepts TypeScript 7 as a peer; either tool leaves the template; a fix the template needs ships only in TypeScript 7.
---

# 009: Hold TypeScript at 6.0.x

## Context

The template's `package.json` pinned `typescript` to `>=6.0.3 <6.1.0`, since
TypeScript minors can break. Renovate opened [#22][] for 7.0.2, widening that
range to `>=6.0.3 <7.1.0`. CI passed only because `pnpm-lock.yaml` still
resolved 6.0.3; merged, the next weekly lock refresh
(008-refresh-lock-files-with-renovate.md) would have resolved 7.0.2.

The widening comes from Renovate's range strategy. Neither `renovate.json`
sets `rangeStrategy`, so `config:recommended`'s `auto` applies, and Renovate
44.180.0 (which opened #22) turns `auto` into `widen` for any npm range with
more than one comparator, and into `update-lockfile` otherwise
([`range.ts`][]).

TypeScript 7 is the native port. Its npm package exports only `version` and
`./unstable/*` entry points, not the compiler API. Baking the template with
`typescript@~7.0.2` on 2026-10-24: `tsc --noEmit` passed, but `pnpm lint`
failed with "typescript-eslint does not support TS 7.0" and `pnpm typedoc`
crashed. The latest [typescript-eslint][] (8.72.0) declares peer `typescript`
`>=4.8.4 <6.1.0`; the latest [typedoc][] (0.28.20) stops at `6.0.x`.

## Options

### Option 1: Do nothing

Merge #22 as is.

**Cons:** The range admits a major that breaks lint and docs; the first lock refresh resolving it goes red, and blocks every later refresh until fixed.

### Option 2: Hold at 6.0.x (Accepted)

Pin `~6.0.3`, and add a Renovate `packageRules` entry with
`allowedVersions: "<7.0.0"` for `typescript` in both `renovate.json` files.

**Cons:** Generated projects miss TypeScript 7's faster type-checking until upstream catches up, and stay on a line that may get no further patches.

### Option 3: Run 6 and 7 side by side

Keep 6.0.x as `typescript` for typescript-eslint and typedoc, and install 7
under an npm alias for `tsc`.

**Pros:** Faster `pnpm typecheck` now.
**Cons:** Both packages install a `tsc` binary, so scripts must name one explicitly; two compilers can disagree on what type-checks.

### Option 4: Adopt ~7.0.2

**Cons:** Lint and docs break in every generated project.

## Decision

Option 2. Only Option 2 keeps every generated-project command working without
a second compiler.

`~6.0.3` allows the same versions as the old range but has one comparator, so
Renovate treats it as `update-lockfile`, which replaces a range it can't
satisfy whole (`~6.0.3` to `~7.0.0`) rather than widening it. Setting
`rangeStrategy` instead wouldn't help: `replace` drops the lower bound
(`<7.1.0`), and `bump` falls back to `widen` for a multi-comparator range.

The rule targets 7, not typescript-eslint's `<6.1.0` cap, because no 6.1 is
published or planned and CI would reject one in its own PR. It lives in the
root `renovate.json`, which manages the template's `package.json`, and in the
template's own, which every generated project inherits.

## Consequences

- Once this merges, Renovate closes #22 on its next run, provided nobody has pushed to its branch, and opens no TypeScript 7 PR while the rule stands. Closing #22 by hand instead tells Renovate to ignore TypeScript 7 updates, so lifting the hold would bring no PR.
- Patch releases within 6.0.x still arrive, through lock refreshes or Renovate's in-range lock updates.
- Lifting the hold means removing the rule from both `renovate.json` files; Renovate then opens the `~7` bump.

[#22]: https://github.com/todofixthis/cookiecutter-browser-plugin/pull/22
[`range.ts`]: https://github.com/renovatebot/renovate/blob/main/lib/modules/manager/npm/range.ts
[typedoc]: https://github.com/TypeStrong/typedoc
[typescript-eslint]: https://github.com/typescript-eslint/typescript-eslint
