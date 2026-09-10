---
name: release
description: Use when preparing or publishing a new release of {{ cookiecutter.project_name }} — covers release notes, version bump, build, packaging for both browsers, GPG-signed artefacts, and GitHub release creation
---

# Release

## Phase 1 — Research & draft (before touching any files)

### 1. Gather changes since last release

```bash
gh release list --limit 1 --json tagName --jq '.[0].tagName'   # find last release tag
git log <last-tag>..HEAD --oneline                              # all commits since
```

### 2. Look up PR and issue context

For every merge commit, extract the PR number and fetch its description:

```bash
git log <last-tag>..HEAD --oneline --merges
gh pr view <number> --json title,body,labels
```

For every `#<number>` reference in commit messages, fetch the issue:

```bash
gh issue view <number> --json title,body,labels
```

### 3. Draft release notes

Using the commit list, PR descriptions, and issue context, draft the release notes following the _Writing Release Notes_ guide below. When a bullet relates to a GitHub issue, prefix it with `[#number]`. Run the `nz-english` skill on the draft, then present it to the developer for review and incorporate feedback before proceeding.

### 4. Recommend version number

Based on the changes, recommend a semver bump:

- **major** — breaking changes
- **minor** — new features or behaviour changes, fully backwards-compatible
- **patch** — bug fixes only

### 5. Gate: breaking changes require a migration guide

A **breaking change** is anything that makes previously-working code fail — at runtime, or under the type checker. Undocumented behaviour someone relied on still counts; "only a couple of users" measures blast radius, not compatibility. If this release has none, skip to the stop below.

**First, settle the version.** Step 4 defines minor and patch as _fully backwards-compatible_, so a breaking change in anything but a major contradicts it. When that happens, stop and put it to the developer: bump to major, or keep the smaller bump and record why in an ADR. Neither pick it for them nor draft around it.

**Then the guide.** One guide per major line, `docs/upgrading_to_v<major>.md` — never a per-minor page. `<major>` is the major being released, or, for a break shipped in a minor or patch, the major line it lands on.

It must:

- **cover _this_ release's breaking change.** A guide left over from an earlier release satisfies nothing.
- exist, and be linked from the upgrade-alert listing in `README.md` (this project's TypeDoc-generated docs site is API-only — it has no toctree/prose-page equivalent — so the guide lives in the repo and is reached via README, not via the docs site).
- follow _Writing a Migration Guide_ below.

**If any of that is missing, the release stops here** — write it first.

Release notes do not satisfy this gate. They are read once, by people who already know a release happened; the guide is what someone finds months later when their code breaks and they don't yet know why.

```bash
ls docs/upgrading_to_v<major>.md                    # exists
rg 'upgrading_to_v<major>' README.md                # linked from the alert listing
```

Then read the guide and confirm it covers this release's break. No command checks that for you.

**Stop here. Get explicit confirmation of the release notes and version number before continuing.**

---

## Phase 2 — Publish (after confirmation)

### 6. Bump version on `develop`

Edit `version` in `package.json` — WXT reads the manifest version from it,
so no separate manifest edit is needed. Commit the file and push to
`develop`.

### 7. Open release PR

```bash
gh pr create --base main --title "Release v<version>" --body-file release-<version>.md
```

**Stop here. Wait for the user to confirm the PR is merged before continuing.**

### 8. Switch to `main`

```bash
git checkout main && git pull
```

### 9. Build and package both targets

```bash
pnpm install --frozen-lockfile
rm -rf .output
pnpm build && pnpm build:firefox
pnpm zip && pnpm zip:firefox
```

Sync first — pulling `main` may have brought in dependency changes.
Artefacts land in `.output/*.zip` — `pnpm zip:firefox` also emits a
`*-sources.zip` (AMO's required source bundle for a minified build); it's
swept up by the same glob in the steps below, no separate handling needed.
Nothing under `.output/` is tracked, so removing the whole directory is
safe — and necessary: a stale build from a
previous version would otherwise sit alongside the new one.

### 10. Tag and push

```bash
git tag -a <version> -m "Release <version>"
git push origin <version>
```

`<version>` must match `package.json`'s `version` field.

### 11. Create GitHub release

**a. Append checksums to the release notes file:**

```bash
shasum -a 256 .output/*.zip >> release-<version>.md
```

**b. GPG-sign the document and each build artefact:**

```bash
GPG_KEY=$(git config user.email)
gpg --local-user "$GPG_KEY" --clearsign release-<version>.md   # → release-<version>.md.asc
for f in .output/*.zip; do gpg --local-user "$GPG_KEY" --detach-sign "$f"; done
```

**c. Build the release body** — concatenate the notes and the signed copy:

````
<contents of release-<version>.md>

---

```
<contents of release-<version>.md.asc>
```
````

Write this to `release-<version>-body.md`.

**d. Create the release and upload all artefacts:**

```bash
gh release create <version> .output/*.zip .output/*.sig \
  --title "{{ cookiecutter.project_name }} v<version>" \
  --notes-file release-<version>-body.md
```

### 12. Submit to the stores

**This step is a manual, developer-run action — it needs per-developer
store API credentials this skill cannot supply**, same spirit as a PyPI
release handing a missing token back to the developer rather than
assuming it's available.

- Submit `.output/*-firefox.zip` to [AMO](https://addons.mozilla.org/developers/) by hand.
- Submit `.output/*-chrome.zip` to the [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole) by hand.
- Once AMO returns the signed `.xpi`, optionally attach it to the release: `gh release upload <version> <path-to-signed.xpi>`.

**Stop here. Wait for the developer to confirm both submissions (or explicitly defer them) before continuing.**

### 13. Clean up

```bash
rm -f release-<version>.md release-<version>.md.asc release-<version>-body.md
rm -rf .output
git checkout develop && git pull
```

`-f` so a re-run does not fail on a file already removed.

### 14. Close related GitHub issues

For every issue referenced in the release notes, close it with a comment:

```bash
gh issue close <number> --comment "Implemented in [v<version>](https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/releases/tag/<version>)."
```

### 15. Rebase `develop` onto `main`

```bash
git rebase origin/main
git push
```

Because `develop` now contains all of `main`'s commits, the histories no longer diverge and a regular (non-force) push succeeds.

---

## Writing Release Notes

### Structure

```markdown
# {{ cookiecutter.project_name }} v<version>

<one-sentence summary of the release character>

> [!WARNING]
> **Breaking changes**
>
> - {what changed}
>   - {migration instructions}
>   - {error you'll see if you don't migrate}
>
> Full migration guide: [Upgrading to {{ cookiecutter.project_name }} v{major}](https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/blob/main/docs/upgrading_to_v{major}.md)

## New features

## Enhancements

## Bug fixes

> [!NOTE]
> **Verifying release artefacts**
>
> 1. Import the signing key: `curl https://github.com/{{ cookiecutter.github_username }}.gpg | gpg --import`
> 2. Download the `.zip` and its matching `.sig` file from the release assets
> 3. Verify: `gpg --verify <name>-<version>-chrome.zip.sig <name>-<version>-chrome.zip`
>
> Key fingerprint: run `gpg --fingerprint {{ cookiecutter.author_email }}` to look it up

# SHA256 Checksums
```

Only include the `[!WARNING]` block if there are breaking changes — but when it is present, the migration guide link is **required**, not optional. Omit any section that has no entries.

### Grouping related items

- **2–4 related bullets:** nest as a hierarchical sublist under the parent bullet
- **5+ related bullets:** promote to a `###` subheading within the section

### Content filter

**Always include**

- New capabilities developers can use
- Architectural decisions
- Behaviour changes
- Breaking changes

**Usually omit**

- Technical details of how something works internally
- Configuration consolidation (unless it changes developer-facing behaviour)
- Code organisation changes
- Dependency updates (include only if resolving a critical or high-severity vulnerability)
- Improvements to coding agent instructions

**Always omit**

- Formatting, linting, minor refactoring
- Test coverage updates

---

## Writing a Migration Guide

`docs/upgrading_to_v<major>.md`, linked from the upgrade-alert listing in `README.md`.

One page covers a whole major line: the move onto it, and any break shipped later within it. Say so in the opening paragraph. Breaks after the major boundary get their own `Changes in v<version>` section; the major boundary itself is the page's main content.

Write for someone who upgraded, hit an error, and does not yet know a release caused it. They arrive by searching the error text — not by reading release notes.

Each breaking change needs four things:

1. **What changed**, in terms of what the developer wrote, not what the internals do.
2. **The error they'll actually see** — copy it verbatim from the tool. Never paraphrase a compiler; they match on this text.
3. **The fix**, as code.
4. **Whether runtime behaviour changed.** If it didn't, say so plainly and early — it converts a panic into a chore.

Then add what the fix leads them into next:

- **Second-order traps.** A fix that lands people in a subtler failure needs that failure documented beside it, with its error text.
- **Facts stranded in ADRs.** ADRs are not linked from anywhere a migrating developer would land. If an ADR holds the only explanation of something they need, the guide is where it goes.

Verify every code sample and every error message by running it.

Before wiring the guide in, run two passes over the draft:

### Audience-surrogate review

Dispatch one subagent on the main model (a reasoning task, not a cheap one), given only the draft and cast as the reader above. It must resolve its problem from the guide alone and flag every place it stays stuck: an error string it can't match verbatim against what a tool emits, a fix it can't apply without knowledge the guide assumes, unexplained jargon, a missing second-order trap or stranded-ADR fact. Address the feedback before continuing.

### Conciseness pass

Tighten the reviewed draft: cut repetition, merge overlapping fixes, drop hedging and prose that restates a code sample. Never trim two things for length: **verbatim error text and code fixes** — readers match on them — and any **migration step**. Then, since this project uses NZ English, run `phx:nz-english` over the result.
