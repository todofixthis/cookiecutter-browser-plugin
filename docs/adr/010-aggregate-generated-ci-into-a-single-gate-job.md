---
status: Accepted
date: 2026-11-17
scope: ["{{ cookiecutter.github_project_name }}/.github/workflows/", test/test_bake.py]
summary: "A generated project's CI has a gate job that needs every other job, runs with if: always() and fails on any failure, cancellation or skip, and is the only required check, rather than the module requiring each job's check by name."
revisit-when: todofixthis/terraform-github-repository stops requiring a check named gate; GitHub lets a ruleset require every check a workflow reports.
---

# 010: Aggregate Generated CI into a Single Gate Job

## Context

Every todofixthis repo is to be provisioned through the
[terraform module][], whose rulesets on `develop` and `main` require one
status check, `gate`, reported by GitHub Actions and run against a branch that
is up to date with its base. The generated project's [`build.yml`][] has no
job by that name. Its jobs are `lint`, `type-check`, `test`, `build`, `e2e`
and `docs`, and `build` is a matrix whose checks report as `build (chrome)`
and `build (firefox)`. So applying the module to a generated project would
block every PR.

The workflow runs on `push` alone, so its checks attach to the pushed commit,
and a PR picks them up from its head commit.

## Options

### Option 1: Do nothing

**Pros:** No change.
**Cons:** A generated project can't adopt the module without hand-editing its workflow, and each would do it its own way.

### Option 2: A `gate` job aggregating every other job (Accepted)

`gate` `needs` every other job, runs with `if: always()`, and fails if any of
them reports `failure`, `cancelled` or `skipped`. A bake test checks that its
`needs` lists every other job.

**Cons:** One more runner start per push, and a job added later blocks nothing until it joins `needs`.
**Risks:** Leaving out `if: always()` turns a failure into a pass: a failed dependency skips the gate, and GitHub counts a skipped required check as passing.

### Option 3: Require each job's check by name in the module

**Pros:** No aggregator job; each failed check blocks the merge directly.
**Cons:** The shared module would need a per-repo list of check names, and the set of matrix check names, such as `build (chrome)`, changes whenever a target is added or renamed.

## Decision

Option 2, the same as [cookiecutter-py ADR 009][], so the module requires one
name across both templates. Option 3 puts each project's job list into
shared Terraform, so every new or renamed job would need a module input
changed and a plan run.

`skipped` fails the gate because no generated job is skipped by design, so a
skip means a dependency failed.

## Consequences

- Every job added to `build.yml` must be added to `gate`'s `needs`, or it stops blocking merges. [`test_bake.py`][] fails until it is.
- `needs` reaches only jobs in the same workflow, so blocking checks go in `build.yml`. A job in a new workflow file would never block a merge, so `test_bake.py` fails if `build.yml` stops being the only workflow.
- A job skipped on purpose by an `if:` condition still goes in `gate`'s `needs`. The fail step then tests that job's `needs.<job>.result` alone, tolerating `skipped` for it, rather than `contains(needs.*.result, 'skipped')`, and `test_bake.py`'s gate test changes with it.
- A workflow-level `paths:` or `branches:` filter would skip `gate` too, leaving the required check unreported and the PR blocked.
- This decision binds generated projects only. This repo's own CI stays as it is, under its hand-made `default` ruleset, which requires `test`, `type-check` and `generate` on `main`. Bringing this repo under the module is a separate decision.
- A PR from a fork gets no `gate`, since its pushes run in the fork, so it can't merge without an admin bypass.
- Projects already generated don't get the job, since cookiecutter has no update path. Add it by hand before applying the module to one.

[cookiecutter-py ADR 009]: https://github.com/todofixthis/cookiecutter-py/blob/develop/docs/adr/009-gate-adr-ci-and-the-phx-pin.md
[terraform module]: https://github.com/todofixthis/terraform-github-repository
[`build.yml`]: <../../{{ cookiecutter.github_project_name }}/.github/workflows/build.yml>
[`test_bake.py`]: ../../test/test_bake.py
