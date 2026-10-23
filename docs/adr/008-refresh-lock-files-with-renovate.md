---
status: Accepted
date: 2026-10-22
scope: [pyproject.toml, renovate.json, "{{ cookiecutter.github_project_name }}/renovate.json"]
summary: Renovate's lock-file maintenance refreshes pnpm-lock.yaml and this repo's uv.lock weekly and automerges on green, with uv resolving only releases at least 3 days old and pnpm keeping its 1-day default; override a transitive dependency only as a stopgap, with a comment naming when to remove it.
revisit-when: Lock-refresh PRs repeatedly fail CI or sit unmerged; a regression from a refresh can't be traced to the package that caused it; Renovate gains targeted updates for transitive dependencies in pnpm-lock.yaml or uv.lock.
---

# 008: Refresh Lock Files with Renovate

## Context

[006-manage-updates-with-renovate.md][] set both `renovate.json` files to
`config:recommended` plus `helpers:pinGitHubActionDigests`. That opens PRs for
direct dependencies only; `config:recommended` leaves lock-file maintenance off.

pnpm and uv both keep a locked transitive version while it still satisfies its
dependents' ranges, so a fix in a transitive dependency reaches a project only
when some direct bump happens to re-resolve that package. cookiecutter-py hit
this with filelock and turned lock-file maintenance on instead of pinning it
([cookiecutter-py ADR 013][]). This repo has three locks: its own `uv.lock`,
the template's `pnpm-lock.yaml`, which every new project starts from, and
each generated project's copy of it. The root `renovate.json` covers the
first two, since Renovate already manages the template's `package.json`.

## Options

### Option 1: Do nothing

**Pros:** No extra PRs.
**Cons:** A transitive fix reaches a project only by accident, and new projects start from a template lock that only moves when a direct dependency does.

### Option 2: Lock-file maintenance (Accepted)

`lockFileMaintenance` enabled, with `automerge`, in both `renovate.json` files.
Renovate regenerates the locks before 4am UTC on Mondays, in one PR per
repository, and merges it once every check on it has passed.

**Pros:** Covers every transitive dependency, not just the ones someone noticed.
**Cons:** A refresh moves many versions at once, transitive majors included, with no PR of their own to announce them; it also conflicts with any open direct-update PR on the same lock, which Renovate then rebases.
**Risks:** A refresh that fails CI for a reason unrelated to any fix blocks every later refresh until someone fixes it; in this repo one PR carries both locks, so a failure on either side holds back both.

### Option 3: Override each fix

Raise the floor of each transitive package needing a fix, with `overrides` in
the generated project's `pnpm-workspace.yaml` (where pnpm 12 keeps its
settings) or `[tool.uv] constraint-dependencies`.

**Pros:** The fix arrives in the PR that adds the override, with no wait, and adds no dependency.
**Cons:** Each override stays long after every dependent's floor has passed the fix, unless someone remembers to remove it.
**Risks:** Only bugs someone has already hit get fixed.

## Decision

Option 2, matching cookiecutter-py and keeping Option 3 as a stopgap only.
Option 2 fixes the cause, a lock that never moves, where Option 3 treats one
symptom at a time. Where a fix can't wait for the next refresh, add an
override with a comment beside it naming the fixed version and saying to
remove it once the lock holds that version. A fix that recent is usually
younger than the cooldown below, so exempt the package from it too, and remove
both together.

Automerge, since nobody meaningfully reviews a whole-lock diff and CI is the
real check.

Renovate's `minimumReleaseAge` can't delay what a refresh picks up: the
package manager does the resolving, so the delay lives there. pnpm skips
releases younger than a day by default, and Renovate's lock maintenance
regenerates `pnpm-lock.yaml` from scratch under that rule. uv has no default,
so `exclude-newer = "3 days"` in this repo's `pyproject.toml` gives the
harness the delay cookiecutter-py's projects have. Renovate's
`minimumReleaseAge` does gate a direct-update PR that raises a range, so the
configs extend `security:minimumReleaseAgeNpm`, and the root
`security:minimumReleaseAgePypi` too, holding those PRs for 3 days; otherwise
one raising a range to a day-old release would fail to lock under uv's
cooldown, or lean on pnpm's fallback. The presets exempt in-range lock updates, most of this repo's npm
PRs, which rest on pnpm's own 1-day check and its fallback below.

## Consequences

- Each repository gets a weekly refresh PR, which merges itself once its checks pass; a red one waits for the maintainer. Renovate merges it on a later run rather than through GitHub's auto-merge, which this repository leaves off.
- Renovate commits only `pnpm-lock.yaml` from a refresh. Where nothing old enough satisfies a range, pnpm falls back to a younger release and records it in `pnpm-workspace.yaml`'s `minimumReleaseAgeExclude`, and that entry is lost. Whether CI's install then fails or passes is untested.
- Every lock-maintenance PR carries the presets' note that Renovate can't check release age during a refresh. That's expected: pnpm and uv apply the delay themselves.
- 006 still decides Renovate; its quoted config gains these settings.

[006-manage-updates-with-renovate.md]: 006-manage-updates-with-renovate.md
[cookiecutter-py ADR 013]: https://github.com/todofixthis/cookiecutter-py/blob/develop/docs/adr/013-refresh-lock-files-with-renovate-not-direct-pins.md
