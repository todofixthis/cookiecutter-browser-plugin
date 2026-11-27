---
status: Accepted
date: 2026-11-27
scope: [.github/workflows/generate-and-validate.yml, AGENTS.md, renovate.json, test/test_bake.py, "{{ cookiecutter.github_project_name }}/.github/workflows/build.yml", "{{ cookiecutter.github_project_name }}/AGENTS.md", "{{ cookiecutter.github_project_name }}/renovate.json"]
summary: Required CI (this repo's generate job; a generated project's renovate job, which gate needs) runs renovate-config-validator --strict via npx at a pinned version, from the directory holding each renovate.json, after checking the file exists; the pin's minor and patch bumps are monthly and automerged, majors reviewed; not a JSON-schema check, a lockfile-pinned install, or checking the Dependency Dashboard after merge.
revisit-when: The pin's monthly bumps repeatedly fail CI or sit unmerged; the validator becomes the slowest step of the jobs that run it.
---

# 011: Validate Renovate config in CI with Renovate's own validator

## Context

This repo ships two Renovate configs: its own `renovate.json`, and the template's, which every
new project receives. Nothing checks either before merge. A fault, such as an unknown option,
a regex that doesn't compile or an option needing migration, surfaces only after merge, on the
Dependency Dashboard, if anyone looks. A fault in the template's config reaches each project
baked before it is fixed; cookiecutter projects never take template updates. Generated
projects can edit their own `renovate.json`, and nothing checks those edits either.

Renovate's validator ships only inside the `renovate` npm package, whose `engines` field
limits the Node versions it runs on (`^24.11.0 || ^26.13.0` at 44.x). This repo's `generate`
job and every generated project already run Node, at the major `.nvmrc` pins (ADR 002). The
validator checks the config files in its working directory, and finding none, exits 0 having
checked nothing. Given a file argument, it validates that file as global self-hosted config
unless also given `--no-global`. Of this repo's own CI, the default branch's ruleset requires
`test`, `type-check` and `generate`.

## Options

### Option 1: Do nothing

Check the Dependency Dashboard after merge.

**Pros:** No CI time.
**Cons:** A faulty config merges, and a template fault ships to every project baked until
someone notices.
**Risks:** Renovate stops bumping a dependency and nobody notices, because nothing fails.

### Option 2: Run `renovate-config-validator --strict` in required CI via `npx` (Accepted)

Run it with `npx --package renovate@<version>`, where the version is a `RENOVATE_VERSION` env
pin with a `# renovate:` comment that a regex manager tracks. Here it runs in the `generate`
job, against the root config and the baked project's. In the template's `build.yml`, a
`renovate` job that `gate` needs runs it against the project's own, under the Node `.nvmrc`
pins.

**Pros:** It runs the same checks Renovate itself does: it compiles every regex, and
`--strict` also fails a config that only needs migration.
**Cons:** The pin fixes only the top-level package: npm resolves its 400-odd dependencies
afresh within their ranges, outside pnpm's `minimumReleaseAge` (ADR 008), and runs their
install scripts. Every push of every project downloads about 360 MB from a cold cache.
**Risks:** The pin trails the hosted Renovate app, so a config valid for the app could fail
an older validator, or the reverse. Without `re2`'s install script, Renovate falls back to
JavaScript regexes and accepts patterns the hosted app rejects. A `node_version` answer below
the validator's floor fails a project's `gate` for a reason unrelated to its config.

### Option 3: Install the validator from the project's lockfile

Add `renovate` to `package.json`'s dev dependencies, so pnpm installs it from the frozen lock.

**Pros:** Every transitive dependency is pinned, aged by pnpm's `minimumReleaseAge`, and
refreshed by lock-file maintenance (ADR 008).
**Cons:** Every job's `pnpm install` gains 400-odd packages that only one job uses, and this
repo's own CI has no `package.json` to hold them.
**Risks:** Renovate's dependency ranges then constrain the project's own, so a validator bump
can block an unrelated upgrade.

### Option 4: Check the config against Renovate's JSON schema

**Pros:** Lighter than installing Renovate.
**Cons:** The schema checks shape, not meaning. It types `matchStrings` as an array of
strings, so a regex that doesn't compile passes, and it can't tell when a config needs
migration.
**Risks:** A green check that misses the faults most likely to stop updates.

## Decision

Option 2. Only Renovate's own validator catches the faults that silently stop updates, and
`--strict` turns a deprecation into a failure while it is still cheap to fix. Option 3 would
tie a CI tool's dependency tree to the shipped extension's. Here the validator runs in
`generate`, which already bakes the project and sets up its Node, and which the ruleset
requires; a job of its own would merge red. It runs with no file argument, from the directory
holding each config, so it checks the file a project receives. Each step first checks
`renovate.json` exists, since the validator passes on a directory without one. Install
scripts stay on, for `re2`.

Renovate releases several times a day. So every config that tracks the pin bumps its minor
and patch releases monthly, at least three days old (`security:minimumReleaseAgeNpm`), and
automerges them once CI passes: a bump that breaks the job fails CI, not a project. A major
can change `engines` or the config schema, so it waits for review.

todofixthis/cookiecutter-py made the same decision in its ADR 026.

## Consequences

- Generated projects gain a `renovate` job in `build.yml`, and `gate` needs it (ADR 010).
- Rotating `node_version` (ADR 002) must keep it within the validator's `engines`.
- Agent sessions need a Node version Renovate's `engines` field accepts to run the validator
  locally. Cloud sessions have one, and todofixthis/config-paddock's baseline image installs
  one.
- This repo's `renovate.json` tracks both its own pin in `generate-and-validate.yml` and the
  template's copy, so one PR bumps both, and a test fails if they differ. Another test fails if
  either config's regex manager stops extracting its workflow's pin.
