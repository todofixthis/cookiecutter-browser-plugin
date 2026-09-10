# cookiecutter-browser-plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `todofixthis/cookiecutter-browser-plugin`, a cookiecutter template that generates Firefox-primary/Chromium-supported WebExtension projects with capabilities matching `todofixthis/cookiecutter-py` (packaging, commit hooks, unit tests, CI, docs, ADR workflow, agent tooling, release process), plus Playwright e2e scaffolding the Python template has no equivalent of.

**Architecture:** Same two-part split as cookiecutter-py: this repo's own dev tooling stays Python (`uv`, `pytest`, `mypy`, `ruff`, `autohooks`), while `{{ cookiecutter.github_project_name }}/` holds the templated WXT + pnpm + TypeScript extension project (Playwright e2e, Vitest unit tests, TypeDoc docs on ReadTheDocs, husky + lint-staged commit hooks). Validated two ways: `test/test_bake.py` (fast structural checks) and `.github/workflows/generate-and-validate.yml` (bakes a real project and runs its own lint/type-check/test/build/e2e/docs-build).

**Tech Stack:** Own repo — `uv`, `pytest`, `mypy`, `ruff`, `autohooks`, `cookiecutter`. Generated project — `pnpm`, `wxt` (Vite-based), `typescript`, `eslint`/`prettier`, `vitest`, `@playwright/test`, `typedoc`, `husky`/`lint-staged`.

**Spec:** `docs/superpowers/specs/2026-09-10-browser-plugin-template-design.md` — this plan implements it in full; read both together.

**Worktree:** `/home/user/cookiecutter-browser-plugin` (branch: `claude/nice-heisenberg-jjtab6`) — this is a cloud/remote Claude Code session already running in an isolated, ephemeral container on its one designated branch (per the session's own harness instructions, which take precedence over `using-git-worktrees`' default of creating a second nested worktree). Do not create an additional worktree; work directly in this checkout and push to this branch.

**Completed pre-work (already committed on this branch, do not redo or add as tasks):**
- `AGENTS.md` (this repo's own root guidance) + `CLAUDE.md` symlink — commits `7f58afa`, `982b042`.
- `docs/superpowers/specs/2026-09-10-browser-plugin-template-design.md` — commit `eb5a89f`.

## Global Constraints

- Node floor: `>=22` (WXT's own engine requirement; matches this sandbox's installed Node).
- `typescript` must stay `>=6.0.3 <6.1.0` — `typescript-eslint@^8.70.0`'s peer range is `>=4.8.4 <6.1.0`; anything at or past `6.1.0`/`7.x` breaks typed linting.
- Package manager: `pnpm`, pinned via `package.json`'s `packageManager` field (Corepack) — never `npm`/`yarn` in any generated command.
- Manifest V3 for both browsers; Firefox is the primary target, Chromium is also supported — WXT resolves the `background.scripts` (Firefox) vs `background.service_worker` (Chromium) split per build target.
- Playwright e2e is Chromium-only (Playwright cannot load unpacked WebExtensions in Firefox) — never claim or scaffold Firefox e2e coverage.
- NZ English; incorporate Te Reo Māori where natural. Comments precede the code they document, never trail it.
- A significant tooling decision gets an ADR (`docs/adr/`, via the `writing-adrs` skill format) before the task that implements it — several tasks below start with an ADR-writing step for exactly this reason.
- The `CLAUDE.md` → `AGENTS.md` and `.claude/skills` → `../.agents/skills` symlink pairs (both at this repo's root and inside `{{ cookiecutter.github_project_name }}/`) must survive `git add`/commit as real symlinks and survive cookiecutter's baking process (verified by `test/test_bake.py`).
- **Any local `pnpm` command (`install`, `build`, `test:e2e`, `typedoc`, ...) run inside the tracked `{{ cookiecutter.github_project_name }}/` directory itself — as opposed to a `/tmp/baked` copy — leaves `node_modules/`, `.wxt/`, `.output/`, `docs/_build/`, etc. on disk.** These are `.gitignore`d, but cookiecutter's own bake walk does *not* consult `.gitignore` — it opens every file under the template root and Jinja-renders it, so a leftover binary file (e.g. `node_modules/**/*.node`/`*.wasm`) crashes the *next* `cookiecutter()` call (`test/test_bake.py`'s fixture, or `uv run pytest` via `autohooks.plugins.pytest` on the next commit) with a `UnicodeDecodeError`, not a test failure. Every step that runs such a command must remove the generated directories again — `rm -rf node_modules .wxt .output coverage docs/_build playwright-report test-results` (never `pnpm-lock.yaml` — that's tracked) — before the task's next bake-dependent step or its Commit step. The steps below say so explicitly at each occurrence; this bullet is the one place the *why* is spelled out.
- Every commit uses the `creative-commits` skill (per this session's global instructions) and is followed by `git push`.

## File Map

Own repo (this repo's own dev tooling — Python):
- `pyproject.toml`, `.gitignore`, `.claude/settings.json`, `renovate.json` — repo config
- `scripts/adr/generate_index.py`, `.autohooks/adr_index.py` — ADR index tooling (ported verbatim from cookiecutter-py)
- `cookiecutter.json`, `hooks/pre_prompt.py`, `hooks/post_gen_project.py` — the template's prompts and hooks
- `test/test_bake.py` — bakes the template, asserts the output is well-formed
- `docs/adr/*.md` — this repo's own ADRs
- `.github/workflows/ci.yml`, `.github/workflows/generate-and-validate.yml` — this repo's own CI
- `README.md` — this repo's own README

Templated project (everything under `{{ cookiecutter.github_project_name }}/` — TypeScript/WXT):
- `package.json`, `wxt.config.ts`, `tsconfig.json`, `eslint.config.js`, `.prettierrc.json`, `.prettierignore`, `vitest.config.ts`, `playwright.config.ts`, `typedoc.json`, `.readthedocs.yaml`, `.gitignore`, `renovate.json`, `LICENCE.txt`, `AGENTS.md`/`CLAUDE.md`, `README.md`
- `entrypoints/background.ts`, `entrypoints/popup/index.html`, `entrypoints/popup/main.ts` — the placeholder extension
- `test/unit/popup.test.ts` — Vitest
- `test/e2e/fixtures.ts`, `test/e2e/popup.spec.ts` — Playwright, Chromium-only
- `.husky/pre-commit` — commit hook
- `.agents/skills/release/SKILL.md`, `.agents/skills/rotate-node-version/SKILL.md` (symlinked from `.claude/skills`)
- `.claude/settings.json`
- `.github/workflows/build.yml`

---

### Task 1: Own-repo Python tooling bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.claude/settings.json`
- Create: `scripts/__init__.py`
- Create: `scripts/adr/__init__.py`
- Create: `scripts/adr/generate_index.py`
- Create: `.autohooks/adr_index.py`

**Interfaces:**
- Produces: `scripts.adr.generate_index.generate(adr_dir: Path, repo_root: Path) -> int` and `scripts.adr.generate_index.main(argv, adr_dir, repo_root) -> int` — every later ADR-writing step runs `uv run python -m scripts.adr.generate_index` to regenerate `docs/adr/INDEX.md`, and Task 3's `ci.yml` runs the same module in its `adr-index` job.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "cookiecutter-browser-plugin"
version = "0.0.0"
description = "Cookiecutter template for todofixthis browser extension projects"
requires-python = ">=3.12"

[dependency-groups]
dev = [
    "autohooks>=26,<27",
    "autohooks-plugin-black>=23,<24",
    "autohooks-plugin-mypy>=23,<24",
    "autohooks-plugin-pytest>=23,<24",
    "autohooks-plugin-ruff>=25,<26",
    "cookiecutter>=2,<3",
    "mypy>=2,<3",
    "pytest>=9,<10",
    "pyyaml>=6.0.3,<7.0.0",
    "types-pyyaml>=6.0.12.20260518,<7.0.0.0",
]
ci = [
    "cookiecutter>=2,<3",
    "mypy>=2,<3",
    "pytest>=9,<10",
    "pyyaml>=6.0.3,<7.0.0",
    "types-pyyaml>=6.0.12.20260518,<7.0.0.0",
]

[tool.uv]
# This repo is a cookiecutter template, not a Python package — nothing here
# gets built or published, so uv shouldn't try to.
package = false

[tool.ruff]
# The templated project directory has no Python of its own (it's a
# TypeScript/WXT project) — see hooks/scripts/test/ AGENTS.md note for why
# this scoping is still worth keeping explicit.
extend-exclude = ["{{ cookiecutter.github_project_name }}"]

[tool.autohooks]
mode = "pythonpath"
pre-commit = [
    "adr_index",
    "autohooks.plugins.black",
    "autohooks.plugins.mypy",
    "autohooks.plugins.pytest",
    "autohooks.plugins.ruff",
]

[tool.mypy]
strict = true

[[tool.mypy.overrides]]
# cookiecutter ships no py.typed marker or stubs package.
module = "cookiecutter.*"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["test"]
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
# Agent worktrees
.claude/worktrees/

# Byte-compiled / optimized / DLL files
__pycache__
*.pyc

# Linting cache
.ruff_cache

# Pytest cache
.pytest_cache

# Virtual environments
venv
.venv
```

- [ ] **Step 3: Write `.claude/settings.json`**

```json
{
  "enabledPlugins": {
    "phx@todofixthis": true
  },
  "extraKnownMarketplaces": {
    "todofixthis": {
      "source": {
        "source": "github",
        "repo": "todofixthis/phx-claude-siat"
      }
    }
  }
}
```

- [ ] **Step 4: Write `scripts/__init__.py` and `scripts/adr/__init__.py`**

Both empty files (they exist only so `scripts.adr.generate_index` is an
importable module path):

```python
```

- [ ] **Step 5: Write `scripts/adr/generate_index.py`**

Ported verbatim from `todofixthis/cookiecutter-py`'s `scripts/adr/generate_index.py`
— it's ADR-format tooling with no Python-project-specific logic, so
nothing needs adapting:

```python
#!/usr/bin/env python3
"""Regenerates docs/adr/INDEX.md from ADR frontmatter, or reports what binds a path.

Run automatically by autohooks on pre-commit when ADR files change.
Run manually: uv run python scripts/adr/generate_index.py

    uv run python scripts/adr/generate_index.py --for src/class_registry/base.py

reports the decisions scoping that path. The hook runs it over the staged paths,
which is the direction INDEX.md cannot serve: the index reaches a reader who already
suspects a decision exists, where this reaches one who does not.
"""

import re
import sys
from pathlib import Path
from typing import Any

import yaml

# Resolved from this file rather than the working directory: a path relative to the
# caller's cwd points at whichever directory they happen to be standing in, and scope
# entries are checked against it. Every function below takes the root explicitly, so
# none can fall back to this file's own repo.
REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = Path("docs") / "adr"
ADR_INDEX_FILENAME = "INDEX.md"

STATUSES = ("Accepted", "Archived", "Superseded")

# Statuses still in force, and so still worth checking and still worth surfacing to
# whoever is editing a path one of them scopes. Superseded is neither: it is history,
# and "supersede, don't edit" means a stale path in one could not be fixed anyway.
BINDING_STATUSES = ("Accepted", "Archived")

# Kept out of the index an agent loads by default: Superseded because a later ADR
# replaced it, Archived because something other than a reader carries it. Both keep
# their full text in the repo, and an Archived decision is as binding as an Accepted
# one.
HIDDEN_STATUSES = ("Archived", "Superseded")

# Frontmatter each status requires and the others refuse, so a status changed without
# its companion field fails here rather than leaving stale metadata behind.
STATUS_FIELDS = {"Archived": "archived-because", "Superseded": "superseded-by"}

# The revisit trigger and the ADR that spent it. These pair with each other rather
# than with a status: either sits with any status, and a discharge names something to
# spend, so it cannot stand alone.
REVISIT_WHEN_FIELD = "revisit-when"
REVISIT_DISCHARGED_BY_FIELD = "revisit-discharged-by"

# The paths where a breach of a decision would be authored, so it reaches whoever
# edits one of them. Entries are exact file paths or directory prefixes ending in
# `/`, never globs.
SCOPE_FIELD = "scope"

# Replaced by `scope` (see docs/adr/004). Named here so a stale field fails rather
# than being silently ignored, which is what would otherwise let a half-finished
# migration pass in both directions.
TAGS_FIELD = "tags"

INDEX_HEADER = (
    "<!-- Auto-generated by scripts/adr/generate_index.py — do not edit manually. -->\n"
    "\n"
    "# ADR Index\n"
)
TABLE_HEADER = (
    "| # | Status | Title | Scope | Summary | Revisit |\n"
    "|---|--------|-------|-------|---------|---------|\n"
)

# An empty table reads as a file that was truncated. Say so instead.
EMPTY_NOTE = "_No decisions are recorded yet._\n"

RE_ADR_FILENAME = re.compile(r"^\d+-.*\.md$")
RE_FILE_NUMBER = re.compile(r"^(\d+)")
RE_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
RE_H1_TITLE = re.compile(r"^# (.+)$", re.MULTILINE)
RE_NUMBER_PREFIX = re.compile(r"^\d+:\s*")


def parse_adr(content: str) -> tuple[dict[str, Any], str, list[str]]:
    """Extract (frontmatter, title, problems) from one ADR document.

    Every rule a document must satisfy to be an ADR is checked here rather than
    split with the caller, which then only decides what to do with a file that has
    problems. `problems` is empty only when both other values are complete; on any
    problem, the fields and title carry whatever could still be read, for an error
    message to name.
    """
    match = RE_FRONTMATTER.match(content)
    if not match:
        return {}, "", ["has no frontmatter block"]

    try:
        fields = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        return {}, "", [f"has invalid YAML frontmatter: {error}"]
    if not isinstance(fields, dict):
        return {}, "", ["frontmatter is not a mapping of `key: value` pairs"]

    problems: list[str] = []

    title_match = RE_H1_TITLE.search(match.group(2))
    if title_match:
        title = RE_NUMBER_PREFIX.sub("", title_match.group(1).strip())
    else:
        title = ""
        problems.append("has no level-one title heading")

    status = fields.get("status")
    if status not in STATUSES:
        problems.append(f"has status {status!r}; expected one of {', '.join(STATUSES)}")
    for owner, field in STATUS_FIELDS.items():
        if status == owner and not fields.get(field):
            problems.append(f"is {owner} but declares no `{field}`")
        elif status != owner and fields.get(field):
            problems.append(
                f"declares `{field}` but its status is {status!r}, not {owner}"
            )

    if fields.get(REVISIT_DISCHARGED_BY_FIELD) and not fields.get(REVISIT_WHEN_FIELD):
        problems.append(
            f"declares `{REVISIT_DISCHARGED_BY_FIELD}` but no `{REVISIT_WHEN_FIELD}` to spend"
        )

    if TAGS_FIELD in fields:
        problems.append(
            f"declares `{TAGS_FIELD}`, which `{SCOPE_FIELD}` replaced; name the paths the "
            "decision binds instead of the words someone might search for"
        )

    # Absent and empty are different answers, so the field is required and `[]` says
    # the decision binds no path. An optional field's absence would carry no more
    # than the missing tags it replaced: unfilled and deliberate look identical.
    if SCOPE_FIELD not in fields:
        problems.append(
            f"declares no `{SCOPE_FIELD}`; list the paths it binds, or `[]` where it binds none"
        )
    elif not isinstance(fields[SCOPE_FIELD], list):
        problems.append(
            f"declares `{SCOPE_FIELD}` as a scalar; write it as an inline list, e.g. "
            f"`{SCOPE_FIELD}: [scripts/, CHANGELOG.md]`"
        )

    return fields, title, problems


def scope_problems(entries: list[str], repo_root: Path) -> list[str]:
    """Return a problem per scope entry that no longer names anything on disk.

    Separate from `parse_adr` because this is the one rule needing the filesystem,
    which keeps every other rule checkable against a string alone.
    """
    problems = []
    for entry in entries:
        # A glob is the natural thing to reach for, and the error for one would
        # otherwise be "nothing matches", which reads as a wrong path rather than as
        # syntax that was never supported.
        if any(char in entry for char in "*?["):
            problems.append(
                f"scopes `{entry}`, which reads as a glob; scope takes exact paths and "
                "directory prefixes ending in `/`, nothing else"
            )
            continue
        target = repo_root / entry
        if not target.exists():
            problems.append(
                f"scopes `{entry}`, which nothing matches; correct it, or drop it where "
                "the code it named is gone for good"
            )
        elif target.is_dir() and not entry.endswith("/"):
            problems.append(f"scopes `{entry}`, a directory; write it as `{entry}/`")
    return problems


def scope_matches(entry: str, path: str) -> bool:
    """Whether a scope entry covers a path: the file itself, or anything beneath it."""
    return path == entry or (entry.endswith("/") and path.startswith(entry))


def cell(value: Any) -> str:
    """Render a frontmatter value for a Markdown table cell, escaping pipes."""
    if isinstance(value, list):
        value = ", ".join(value)
    return str(value).replace("|", "\\|")


def generate(adr_dir: Path, repo_root: Path) -> int:
    """Regenerate INDEX.md from ADR frontmatter. Returns 0 on success, 1 on error.

    Neither directory is defaulted: the caller supplies both, so a test that forgot
    its fixture cannot rewrite this repository's own index.
    """
    index_file = adr_dir / ADR_INDEX_FILENAME

    rows = []
    has_errors = False
    for path in sorted(adr_dir.iterdir()):
        # Dot-files are editor and tooling debris, not documents anyone filed here.
        if path.name.startswith(".") or path.name == ADR_INDEX_FILENAME:
            continue
        # The directory holds ADRs and the index, nothing else, so an unrecognised
        # name is either a document misfiled here or an ADR named wrongly — and the
        # second would drop out of the index silently.
        if not RE_ADR_FILENAME.match(path.name):
            print(
                f"Error: {path.name} is neither an ADR nor {ADR_INDEX_FILENAME}; "
                "rename it NNN-slug.md or move it elsewhere under docs/",
                file=sys.stderr,
            )
            has_errors = True
            continue

        fields, title, problems = parse_adr(path.read_text(encoding="utf-8"))
        # Scope is checked for every decision still in force, Archived ones
        # included: they are out of the index but not out of effect, and their
        # paths rot the same way. A Superseded ADR is left alone, since editing one
        # is forbidden.
        if not problems and fields["status"] in BINDING_STATUSES:
            problems = scope_problems(fields[SCOPE_FIELD], repo_root)
        if problems:
            for problem in problems:
                print(f"Error: {path.name} {problem}", file=sys.stderr)
            has_errors = True
            continue
        if fields["status"] in HIDDEN_STATUSES:
            continue

        # A discharged trigger leaves the index the way a Superseded ADR does: the
        # condition is spent, so carrying it costs every reader context for
        # something nobody can act on. The pair stays in the ADR's own frontmatter
        # as the record.
        revisit = (
            ""
            if fields.get(REVISIT_DISCHARGED_BY_FIELD)
            else fields.get(REVISIT_WHEN_FIELD, "")
        )

        # RE_ADR_FILENAME already required a leading number, so this always matches.
        number_match = RE_FILE_NUMBER.match(path.name)
        assert number_match is not None
        number = number_match.group(1)
        rows.append(
            f"| [{number}]({path.name}) | {cell(fields['status'])} "
            f"| {cell(title)} | {cell(fields[SCOPE_FIELD])} "
            f"| {cell(fields.get('summary', ''))} | {cell(revisit)} |\n"
        )

    if has_errors:
        print("Fix the errors above before committing.", file=sys.stderr)
        return 1

    body = TABLE_HEADER + "".join(rows) if rows else EMPTY_NOTE
    index_file.write_text(f"{INDEX_HEADER}\n{body}", encoding="utf-8")
    print(f"Generated {index_file} ({len(rows)} entries)")
    return 0


def relative_to_repo(path: str, repo_root: Path) -> str:
    """Return `path` as the repo-relative form scope entries are written in.

    An absolute path is what an editor or an agent has to hand, and left alone it
    matches no scope entry — so the lookup would answer "nothing binds this file"
    for a file several decisions bind. A confident false negative is worse than an
    error, which is why a path outside the repository raises rather than returning
    nothing.
    """
    candidate = Path(path)
    if not candidate.is_absolute():
        return path
    try:
        return str(candidate.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        raise SystemExit(f"Error: {path} is outside {repo_root.resolve()}")


def report_scoped_to(paths: list[str], adr_dir: Path, repo_root: Path) -> int:
    """Print the binding decisions covering any of `paths`. Always returns 0.

    This is the direction the index cannot serve. A reader scanning INDEX.md has to
    already suspect a decision exists; this answers the question they actually
    hold — which decisions bind the file in front of me — reaching them through the
    work rather than through a search they had to think to run. It reports Archived
    decisions too, which is the whole point of them: in force, out of the index,
    and met at the moment someone edits what they bind.
    """
    subjects = [relative_to_repo(path, repo_root) for path in paths]
    for path in sorted(adr_dir.iterdir()):
        if path.name.startswith(".") or not RE_ADR_FILENAME.match(path.name):
            continue
        fields, title, problems = parse_adr(path.read_text(encoding="utf-8"))
        # Say so rather than skipping: a malformed ADR silently binds nothing, and
        # this is the one place the lookup speaks, so an invisible gap here reads
        # as "no decision covers your change".
        if problems:
            print(
                f"Warning: {path.name} could not be read, so it binds nothing here",
                file=sys.stderr,
            )
            continue
        if fields["status"] not in BINDING_STATUSES:
            continue
        if any(
            scope_matches(entry, subject)
            for entry in fields[SCOPE_FIELD]
            for subject in subjects
        ):
            number_match = RE_FILE_NUMBER.match(path.name)
            assert number_match is not None
            print(
                f"{number_match.group(1)} ({fields['status']}): {title} — docs/adr/{path.name}"
            )
    return 0


def main(argv: list[str], adr_dir: Path, repo_root: Path) -> int:
    """Regenerate the index, or with `--for`, report the decisions binding some paths."""
    if argv[:1] == ["--for"]:
        if len(argv) < 2:
            print("Error: --for needs at least one path", file=sys.stderr)
            return 1
        return report_scoped_to(argv[1:], adr_dir, repo_root)
    if argv:
        print(f"Error: unrecognised arguments {argv}", file=sys.stderr)
        return 1
    return generate(adr_dir, repo_root)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], REPO_ROOT / ADR_DIR, REPO_ROOT))
```

- [ ] **Step 6: Write `.autohooks/adr_index.py`**

Ported verbatim from `todofixthis/cookiecutter-py`'s `.autohooks/adr_index.py`:

```python
"""Autohooks plugin: regenerate ADR index when ADR files are staged."""

import re
import sys
from pathlib import Path
from typing import Optional

from autohooks.api import ok
from autohooks.api.git import get_staged_status, stage_files
from autohooks.config import Config
from autohooks.precommit.run import ReportProgress

# Add project root to sys.path so scripts.adr.generate_index is importable
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.adr.generate_index import (  # noqa: E402
    ADR_DIR,
    ADR_INDEX_FILENAME,
    REPO_ROOT,
    generate,
)

RE_STAGED_ADR = re.compile(r"docs/adr/[0-9]+-.*\.md$")


def precommit(
    config: Optional[Config] = None,
    report_progress: Optional[ReportProgress] = None,
    **kwargs: object,
) -> int:
    """Regenerate ADR index when ADR files are staged."""
    staged = [f for f in get_staged_status() if RE_STAGED_ADR.search(str(f.path))]

    if not staged:
        ok("No staged ADR files.")
        return 0

    result = generate(REPO_ROOT / ADR_DIR, REPO_ROOT)
    if result == 0:
        stage_files([ADR_DIR / ADR_INDEX_FILENAME])
        ok("Generated ADR index.")
    return result
```

- [ ] **Step 7: Sync deps and verify**

Run: `uv sync --group=dev`
Expected: creates `.venv` and `uv.lock`, exits 0.

Run: `uv run mypy scripts`
Expected: `Success: no issues found`. (`hooks` and `test` don't exist yet — Tasks 2 and 4 create them; `AGENTS.md`'s full `mypy hooks scripts test` command works from Task 4 onward.)

- [ ] **Step 8: Commit**

Run `git status` to catch any related unstaged or untracked files (e.g. `uv.lock`), then use the `creative-commits` skill.

---

### Task 2: ADR 001 — WXT + pnpm toolchain, cookiecutter scaffold, and agent skills

**Files:**
- Create: `docs/adr/001-generate-projects-using-wxt-and-pnpm.md`
- Create: `cookiecutter.json`
- Create: `hooks/pre_prompt.py`
- Create: `hooks/post_gen_project.py`
- Create: `{{ cookiecutter.github_project_name }}/package.json`
- Create: `{{ cookiecutter.github_project_name }}/wxt.config.ts`
- Create: `{{ cookiecutter.github_project_name }}/tsconfig.json`
- Create: `{{ cookiecutter.github_project_name }}/eslint.config.js`
- Create: `{{ cookiecutter.github_project_name }}/.prettierrc.json`
- Create: `{{ cookiecutter.github_project_name }}/.prettierignore`
- Create: `{{ cookiecutter.github_project_name }}/entrypoints/background.ts`
- Create: `{{ cookiecutter.github_project_name }}/entrypoints/popup/index.html`
- Create: `{{ cookiecutter.github_project_name }}/entrypoints/popup/main.ts`
- Create: `{{ cookiecutter.github_project_name }}/LICENCE.txt`
- Create: `{{ cookiecutter.github_project_name }}/.gitignore`
- Create: `{{ cookiecutter.github_project_name }}/README.md`
- Create: `{{ cookiecutter.github_project_name }}/AGENTS.md`
- Create: `{{ cookiecutter.github_project_name }}/CLAUDE.md` (symlink to `AGENTS.md`)
- Create: `{{ cookiecutter.github_project_name }}/.claude/settings.json`
- Create: `{{ cookiecutter.github_project_name }}/.claude/skills` (symlink to `../.agents/skills`)
- Create: `{{ cookiecutter.github_project_name }}/.agents/skills/release/SKILL.md`
- Create: `{{ cookiecutter.github_project_name }}/.agents/skills/rotate-node-version/SKILL.md`
- Create: `test/test_bake.py`

**Interfaces:**
- Consumes: none (first task to touch the templated project).
- Produces: a bakeable template with `github_project_name`/`package_name`/`gecko_extension_id`/`node_version` context values later tasks' CI/docs/skills files reference by these exact names; `entrypoints/background.ts` and `entrypoints/popup/{index.html,main.ts}` as the placeholder extension later unit/e2e tests exercise; `test/test_bake.py`'s `baked_project` fixture, which every later `test_bake.py` addition reuses.

- [ ] **Step 1: Write ADR 001**

````markdown
---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/package.json", "{{ cookiecutter.github_project_name }}/wxt.config.ts"]
summary: Generate browser-extension projects using WXT (a Vite-based cross-browser WebExtension framework) and pnpm, instead of a hand-maintained manifest.json plus web-ext.
---

# 001: Generate Projects Using WXT + pnpm Instead of Raw Manifest/web-ext

## Context

Firefox and Chromium diverge on Manifest V3 in ways a single hand-written
`manifest.json` can't paper over: Chromium requires
`background.service_worker`; Firefox, which doesn't support MV3 service
workers, requires `background.scripts`. A raw-manifest template would need
either two manifests or Jinja conditionals scattered through one, both of
which drift the moment a contributor edits only the browser they're testing
against.

## Options

### Option 1: Hand-maintained manifest.json + web-ext

Author `manifest.json` directly, using `web-ext build`/`web-ext run` for
Firefox packaging and a second, separately-maintained Chromium manifest.

**Pros:** No framework dependency; full manual control.
**Cons:** Two manifests (or one full of conditionals) to keep in sync by
hand; no bundler, so any non-trivial TypeScript/asset pipeline is
hand-rolled on top.
**Risks:** The exact failure mode this ADR exists to avoid — the two
manifests silently diverging.

### Option 2: WXT + pnpm (Accepted)

WXT is a Vite-based framework purpose-built for cross-browser
WebExtensions: one `entrypoints/` source tree, and `wxt build -b <target>`
emits the correct manifest shape per target from the same source. It also
generates TypeScript types for the WebExtension APIs and ships a Vitest
plugin (`wxt/testing/vitest-plugin`) for mocking `browser.*` in unit tests.

**Pros:** Single source tree for both browsers; built-in dev server with
hot reload; first-class TypeScript and testing support.
**Cons:** A framework dependency and its conventions to learn, instead of
the bare WebExtension APIs.
**Risks:** WXT is pre-1.0 (`0.x`); breaking changes are possible between
minor versions — mitigated by Renovate (ADR 006) surfacing them for review
rather than auto-merging silently.

## Decision

Option 2. pnpm is WXT's documented package manager of choice and the
fastest of the mainstream options; both are pinned via `package.json`'s
`packageManager` field (Corepack) so CI and contributors resolve the same
version.

## Consequences

- The generated project has no `manifest.json` of its own —
  `wxt.config.ts` is the single source WXT compiles into a manifest per
  build target.
- `browser_specific_settings.gecko.id` is required for a stable Firefox
  extension ID across rebuilds/AMO submissions; templated as
  `{{ cookiecutter.gecko_extension_id }}`. Firefox has also required
  `browser_specific_settings.gecko.data_collection_permissions` for new
  extensions since 3 November 2025 — confirmed by a real `wxt build -b
  firefox`, which warns without it; the placeholder extension declares
  `required: ["none"]` since it collects nothing.
- Contributors need `wxt prepare` (wired as `package.json`'s
  `postinstall`) before `tsc` can resolve WXT's generated types.
````

- [ ] **Step 3: Write `cookiecutter.json`**

```json
{
  "author_email": "phx@phx.nz",
  "author_name": "Phoenix Zerin",
  "project_name": "My Browser Plugin",
  "github_project_name": "{{ cookiecutter.project_name.lower().replace(' ', '-') }}",
  "github_username": "todofixthis",
  "package_name": "{{ cookiecutter.project_name.lower().replace(' ', '-') }}",
  "project_short_description": "A short description of the project",
  "gecko_extension_id": "{{ cookiecutter.package_name }}@{{ cookiecutter.github_username }}",
  "node_version": "22",
  "this_year": "(see hooks/pre_prompt.py)",
  "version": "0.1.0"
}
```

- [ ] **Step 4: Write `hooks/pre_prompt.py`**

```python
from datetime import UTC, datetime
from json import dump, load


def main() -> None:
    context_filename = "cookiecutter.json"

    with open(context_filename, "r") as f_in:
        context_data: dict[str, str] = load(f_in)

    context_data.update(
        {
            "this_year": str(datetime.now(tz=UTC).date().year),
        }
    )

    with open(context_filename, "w") as f_out:
        dump(context_data, f_out, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Write `hooks/post_gen_project.py`**

Ported verbatim from `todofixthis/cookiecutter-py`'s `hooks/post_gen_project.py`
— it fixes up symlinks cookiecutter's own copy step dereferences, which is
unrelated to Python vs. TypeScript:

```python
"""Fixes up files cookiecutter copies as independent files but should be symlinks.

cookiecutter's own file-copy mechanism doesn't preserve symlinks, so a
symlink in the template is baked into the generated project as an
independent duplicate of its target instead. This hook restores the
symlinks the generated project actually wants once generation finishes.
"""

import shutil
from pathlib import Path


def main() -> None:
    project_root = Path.cwd()

    claude_md = project_root / "CLAUDE.md"
    claude_md.unlink()
    claude_md.symlink_to("AGENTS.md")

    claude_skills = project_root / ".claude" / "skills"
    shutil.rmtree(claude_skills)
    claude_skills.symlink_to(Path("..") / ".agents" / "skills")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Write `{{ cookiecutter.github_project_name }}/package.json`**

```json
{
  "name": "{{ cookiecutter.package_name }}",
  "private": true,
  "type": "module",
  "version": "{{ cookiecutter.version }}",
  "packageManager": "pnpm@12.3.4",
  "engines": {
    "node": ">={{ cookiecutter.node_version }}"
  },
  "scripts": {
    "dev": "wxt",
    "dev:firefox": "wxt -b firefox",
    "build": "wxt build",
    "build:firefox": "wxt build -b firefox",
    "zip": "wxt zip",
    "zip:firefox": "wxt zip -b firefox",
    "postinstall": "wxt prepare",
    "prepare": "husky",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "lint": "eslint . && prettier --check .",
    "format": "eslint --fix . && prettier --write .",
    "typecheck": "tsc --noEmit",
    "typedoc": "typedoc --out docs/_build/html"
  },
  "devDependencies": {
    "@eslint/js": "^10.0.1",
    "@playwright/test": "^1.63.0",
    "@types/node": "^22.20.2",
    "eslint": "^10.10.0",
    "eslint-config-prettier": "^10.1.8",
    "globals": "^17.12.0",
    "happy-dom": "^20.14.3",
    "husky": "^9.1.7",
    "lint-staged": "^17.5.0",
    "prettier": "^3.9.6",
    "typedoc": "^0.28.20",
    "typescript": ">=6.0.3 <6.1.0",
    "typescript-eslint": "^8.70.0",
    "vitest": "^5.0.0",
    "wxt": "^0.21.4"
  },
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{js,cjs,mjs,json,md,html,css}": [
      "prettier --write"
    ]
  }
}
```

- [ ] **Step 7: Write `{{ cookiecutter.github_project_name }}/wxt.config.ts`**

```typescript
import { defineConfig } from 'wxt';

// Manifest V3 for both targets — WXT resolves the Firefox
// (background.scripts) vs. Chromium (background.service_worker) split per
// build target from this one config (see docs/adr/001).
export default defineConfig({
  manifestVersion: 3,
  manifest: {
    name: '{{ cookiecutter.project_name }}',
    description: '{{ cookiecutter.project_short_description }}',
    browser_specific_settings: {
      gecko: {
        id: '{{ cookiecutter.gecko_extension_id }}',
        // Required for new Firefox extensions since 3 November 2025; this
        // placeholder collects nothing, so "none" is accurate as shipped —
        // update it if a real entrypoint starts collecting data.
        data_collection_permissions: {
          required: ['none'],
        },
      },
    },
  },
});
```

- [ ] **Step 8: Write `{{ cookiecutter.github_project_name }}/tsconfig.json`**

```json
{
  "extends": "./.wxt/tsconfig.json",
  "compilerOptions": {
    "strict": true
  },
  "include": [
    ".wxt/types",
    "entrypoints",
    "test",
    "wxt.config.ts",
    "vitest.config.ts",
    "playwright.config.ts"
  ]
}
```

`include` is not merged across `extends` — this array replaces
`.wxt/tsconfig.json`'s own `include`, so `.wxt/types` (declaring the
ambient `browser` global and `defineBackground`) must be listed
explicitly or `tsc`/typed ESLint fail on the placeholder code itself.

- [ ] **Step 9: Write `{{ cookiecutter.github_project_name }}/eslint.config.js`**

```javascript
// @ts-check
import js from '@eslint/js';
import eslintConfigPrettier from 'eslint-config-prettier';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: [
      '.output/**',
      '.wxt/**',
      'node_modules/**',
      'coverage/**',
      'docs/_build/**',
    ],
  },
  js.configs.recommended,
  tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
      globals: {
        ...globals.browser,
        ...globals.webextensions,
      },
    },
  },
  eslintConfigPrettier,
  {
    // eslint.config.js itself (and any other plain .js file) isn't part of
    // the typed program tsconfig.json describes — drop typed-linting rules
    // for it rather than have projectService fail to place it in a project.
    files: ['**/*.js'],
    ...tseslint.configs.disableTypeChecked,
  },
);
```

- [ ] **Step 10: Write `{{ cookiecutter.github_project_name }}/.prettierrc.json`**

```json
{
  "singleQuote": true,
  "semi": true,
  "trailingComma": "all"
}
```

- [ ] **Step 10a: Write `{{ cookiecutter.github_project_name }}/.prettierignore`**

Prettier v3 doesn't read `.gitignore` automatically — without this,
`prettier --check .` (part of `pnpm lint`) fails on WXT's own generated
build metadata:

```gitignore
.output/
.wxt/
node_modules/
coverage/
docs/_build/
pnpm-lock.yaml
```

- [ ] **Step 11: Write the placeholder extension**

`{{ cookiecutter.github_project_name }}/entrypoints/background.ts`:

```typescript
export default defineBackground(() => {
  // Placeholder startup log, matching cookiecutter-py's placeholder test:
  // just enough to prove the scaffold works.
  console.log('{{ cookiecutter.project_name }} background started', {
    id: browser.runtime.id,
  });
});
```

`{{ cookiecutter.github_project_name }}/entrypoints/popup/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>{{ cookiecutter.project_name }}</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="./main.ts"></script>
  </body>
</html>
```

`{{ cookiecutter.github_project_name }}/entrypoints/popup/main.ts`:

```typescript
const app = document.querySelector<HTMLDivElement>('#app');
if (app) {
  app.textContent = 'Hello from {{ cookiecutter.project_name }}!';
}
```

- [ ] **Step 12: Write `{{ cookiecutter.github_project_name }}/LICENCE.txt`**

```
MIT Licence

Copyright (c) {{ cookiecutter.this_year }} {{ cookiecutter.author_name }}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 13: Write `{{ cookiecutter.github_project_name }}/.gitignore`**

```gitignore
# Agent worktrees
.claude/worktrees/

# Build output
.output/
.wxt/

# Dependencies
node_modules/

# dotenv
.env

# Docs build
docs/_build/

# Playwright
playwright-report/
test-results/

# Coverage
coverage/
```

- [ ] **Step 13a: Write `{{ cookiecutter.github_project_name }}/README.md`**

Needed by the `release` skill (Step 18, below), which links breaking-change
migration guides from this file's upgrade-alert listing.

````markdown
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
````

- [ ] **Step 14: Write `{{ cookiecutter.github_project_name }}/AGENTS.md`**

````markdown
## Getting Started

Before writing code, check:

- `docs/adr/INDEX.md` — prior decisions (don't re-litigate)
- `docs/superpowers/plans/` — current implementation plan, if one exists

## Architecture Decision Records

When making significant decisions — choosing between libraries, patterns, tools, or conventions — you **must** write an ADR before implementing the decision. Use the `writing-adrs` skill for the format and conventions. ADRs live in `docs/adr/`. Before writing, run `ls docs/adr/` to find the highest existing number and increment it.

## Commands

```bash
pnpm install                 # install deps, generates WXT types (postinstall) and the husky hook (prepare)
pnpm dev                     # dev server, Chromium
pnpm dev:firefox             # dev server, Firefox
pnpm build && pnpm build:firefox   # production build, both targets
pnpm test                    # unit tests (vitest)
pnpm test:e2e                # e2e tests (Playwright, Chromium only — see docs/adr/004)
pnpm lint                    # eslint + prettier --check
pnpm typecheck                # tsc --noEmit
pnpm typedoc                 # build API docs (TypeDoc) into docs/_build/html
```

**In a worktree:** the shell can silently reset to the main checkout, so always prefix state-mutating commands (`pnpm add`/`install`/`run`) with `cd <worktree> &&` to ensure they hit the worktree.

## Architecture

- `entrypoints/` — WXT convention: one file/folder per extension entrypoint (`background.ts`, `popup/`). WXT compiles this into a manifest per build target (`wxt build -b chrome|firefox`); there's no hand-maintained `manifest.json`.
- `test/unit/` — Vitest, using `wxt/testing/vitest-plugin` to resolve WXT's virtual imports and mock `browser.*`.
- `test/e2e/` — Playwright, loading the _built_ Chromium extension via a persistent browser context.
- `docs/` — TypeDoc output and config; hosted on ReadTheDocs.

## Docstrings

TSDoc (`/** ... */` with `@param`/`@returns`) on exported functions — TypeDoc renders these into the API docs.

## Tests

Every test has a name stating the behaviour it verifies.

## Code Comments

Place comments on the line preceding the code they document, not as trailing comments.

## Language and Style

- NZ English; incorporate Te Reo Māori where natural (e.g. "mahi", "kaupapa")
- Use "Initialises" not "Initializes"

### Writing for coding agents

- Do not document information that already exists in the coding agent's training data or could be easily discovered by reading the code.
- Do not list individual files; list high-level directories so the agent knows where to look.
- Aim for concise style that optimises token count without sacrificing clarity.

## Branches

- `main` — releases only; merge from `develop` via PR
- `develop` — main development branch
- Feature branches off `develop` for all new work

## Git Worktrees

Use the `using-git-worktrees` skill; it creates worktrees via the native `EnterWorktree` tool under `.claude/worktrees/` (gitignored). Don't hand-roll `git worktree add` when the native tool is available. Keep `.claude/` a real directory (only `.claude/skills` is a symlink into `.agents/skills`) — the native tool refuses to run if `.claude` itself is a symlink.
````

- [ ] **Step 15: Symlink `{{ cookiecutter.github_project_name }}/CLAUDE.md` to `AGENTS.md`**

Run: `ln -s AGENTS.md "{{ cookiecutter.github_project_name }}/CLAUDE.md"`

- [ ] **Step 16: Write `{{ cookiecutter.github_project_name }}/.claude/settings.json`**

```json
{
  "enabledPlugins": {
    "phx@todofixthis": true
  },
  "extraKnownMarketplaces": {
    "todofixthis": {
      "source": {
        "source": "github",
        "repo": "todofixthis/phx-claude-siat"
      }
    }
  }
}
```

- [ ] **Step 17: Symlink `{{ cookiecutter.github_project_name }}/.claude/skills` to `../.agents/skills`**

Run: `mkdir -p "{{ cookiecutter.github_project_name }}/.agents/skills"` then `ln -s ../.agents/skills "{{ cookiecutter.github_project_name }}/.claude/skills"`

- [ ] **Step 18: Write the `release` skill**

`{{ cookiecutter.github_project_name }}/.agents/skills/release/SKILL.md`:

`````markdown
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
`````

- [ ] **Step 19: Write the `rotate-node-version` skill**

`{{ cookiecutter.github_project_name }}/.agents/skills/rotate-node-version/SKILL.md`:

````markdown
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
````

- [ ] **Step 19a: Install JS dependencies and commit the lockfile**

Run: `cd "{{ cookiecutter.github_project_name }}" && pnpm install`
Expected: exits 0, generates `pnpm-lock.yaml` and `.wxt/` (via the
`postinstall` script). This must happen before Task 4 commits
`build.yml` — that workflow's `pnpm install --frozen-lockfile` and
`actions/setup-node`'s `cache: pnpm` both require a committed
`pnpm-lock.yaml` to exist; without this step, Task 4's own commit would
push a CI run against jobs that fail at "Install dependencies" before
Task 5 gets a chance to add the lockfile.

`pnpm-lock.yaml` is not in `.gitignore` — it must be committed alongside
the rest of Task 2's files in Step 23, below.

Run: `rm -rf "{{ cookiecutter.github_project_name }}/node_modules" "{{ cookiecutter.github_project_name }}/.wxt"`
This must happen before Step 20's `test/test_bake.py` runs (Step 21) or
Step 23 commits — see the Global Constraints note on why leftover
`pnpm install` output breaks the next bake. `pnpm-lock.yaml` stays; only
the generated directories go.

- [ ] **Step 20: Write `test/test_bake.py`**

```python
"""Bakes the template with default answers and checks the output is well-formed."""

import json
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

# Anything of this shape surviving in a baked file means cookiecutter's Jinja
# pass missed it — the whole point of baking is that none of this remains.
RE_UNRENDERED_JINJA = re.compile(r"\{\{.*cookiecutter[^}]*\}\}")

# Binary/generated files a text scan for unrendered Jinja shouldn't open.
SKIP_SUFFIXES = {".png", ".ico"}


@pytest.fixture
def baked_project(tmp_path: Path) -> Iterator[Path]:
    """Bakes the template with its default answers into a temp directory."""
    output_dir = cookiecutter(
        str(TEMPLATE_ROOT),
        no_input=True,
        output_dir=str(tmp_path),
    )
    yield Path(output_dir)


def test_bakes_without_error(baked_project: Path) -> None:
    """The template renders into a directory that actually exists."""
    assert baked_project.is_dir()


def test_leaves_no_unrendered_jinja(baked_project: Path) -> None:
    """No `{{ cookiecutter.* }}` markers survive rendering in any generated file."""
    offenders = [
        str(path.relative_to(baked_project))
        for path in baked_project.rglob("*")
        if path.is_file()
        and path.suffix not in SKIP_SUFFIXES
        and not path.is_symlink()
        and RE_UNRENDERED_JINJA.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_generates_valid_package_json(baked_project: Path) -> None:
    """The generated project's package.json parses and names the extension."""
    with (baked_project / "package.json").open(encoding="utf-8") as f_in:
        data = json.load(f_in)
    assert data["name"] == "my-browser-plugin"
    assert data["private"] is True


def test_generates_expected_entrypoints_layout(baked_project: Path) -> None:
    """The generated project's placeholder entrypoints both exist."""
    assert (baked_project / "entrypoints" / "background.ts").is_file()
    assert (baked_project / "entrypoints" / "popup" / "index.html").is_file()
    assert (baked_project / "entrypoints" / "popup" / "main.ts").is_file()


def test_generates_licence(baked_project: Path) -> None:
    """The generated project ships an MIT licence file."""
    licence_text = (baked_project / "LICENCE.txt").read_text(encoding="utf-8")
    assert "MIT" in licence_text


def test_generates_readme(baked_project: Path) -> None:
    """The generated project ships its own README, distinct from AGENTS.md."""
    readme_text = (baked_project / "README.md").read_text(encoding="utf-8")
    assert "My Browser Plugin" in readme_text


def test_claude_md_stays_a_symlink(baked_project: Path) -> None:
    """CLAUDE.md survives baking as a real symlink to AGENTS.md, not a copy.

    cookiecutter's own file-copy mechanism dereferences symlinks in the
    template into independent copies; hooks/post_gen_project.py restores
    this one so AGENTS.md stays the single canonical source.
    """
    claude_md = baked_project / "CLAUDE.md"
    assert claude_md.is_symlink()
    assert claude_md.readlink() == Path("AGENTS.md")


def test_claude_skills_stays_a_symlink(baked_project: Path) -> None:
    """.claude/skills survives baking as a real symlink into .agents/skills."""
    claude_skills = baked_project / ".claude" / "skills"
    assert claude_skills.is_symlink()
    assert claude_skills.readlink() == Path("..") / ".agents" / "skills"
```

- [ ] **Step 21: Run the test suite**

Run: `uv run pytest`
Expected: 8 passed.

- [ ] **Step 22: Lint and type-check**

Run: `uv run ruff check hooks scripts test`
Expected: `All checks passed!`

Run: `uv run mypy hooks scripts test`
Expected: `Success: no issues found`.

- [ ] **Step 22a: Regenerate the ADR index**

Run: `uv run python -m scripts.adr.generate_index`
Expected: `Generated docs/adr/INDEX.md (1 entries)`, creating
`docs/adr/INDEX.md`. Run only now, not right after Step 1 — ADR 001's
`scope` names `package.json` and `wxt.config.ts`, which weren't written
until Steps 6–7; the ADR index generator hard-errors on a scope entry
that doesn't exist on disk yet.

- [ ] **Step 23: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

---

### Task 3: Own-repo CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `scripts.adr.generate_index` (Task 1), `test/test_bake.py` (Task 2).

- [ ] **Step 1: Write `.github/workflows/ci.yml`**

```yaml
# https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
name: CI

on:
  push: ~

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version-file: "pyproject.toml"
      - name: Install dependencies
        run: uv sync --group ci
      - name: Run tests
        run: uv run pytest

  type-check:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version-file: "pyproject.toml"
      - name: Install dependencies
        run: uv sync --group ci
      - name: Type checking
        run: uv run mypy hooks scripts test

  adr-index:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version-file: "pyproject.toml"
      - name: Install dependencies
        run: uv sync --group ci
      - name: Regenerate the ADR index
        run: uv run python -m scripts.adr.generate_index
      - name: Check the index is up to date
        run: git diff --exit-code docs/adr/INDEX.md
```

- [ ] **Step 2: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

---

### Task 4: ADR 002 — single pinned Node version, and templated CI (lint/type-check/build)

**Files:**
- Create: `docs/adr/002-single-pinned-node-version.md`
- Create: `{{ cookiecutter.github_project_name }}/.github/workflows/build.yml`

**Interfaces:**
- Consumes: `package.json` scripts `lint`/`typecheck`/`build`/`build:firefox` (Task 2).
- Produces: `build.yml`'s job names (`lint`, `type-check`, `build`) that Tasks 5, 6, 7, 8 each add a step or job to — later tasks must not rename these jobs.

- [ ] **Step 1: Write ADR 002**

````markdown
---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/.github/workflows/build.yml"]
summary: CI runs a single pinned Node LTS version, not a support matrix — Node is this project's build tooling, not the runtime the shipped extension runs under.
---

# 002: Support a Single Pinned Node Version, Not a Matrix

## Context

cookiecutter-py's generated projects test against a rolling 3-version
Python matrix (its own docs/adr/001) because the *shipped artefact* — a
Python package — runs directly on whichever Python its users have
installed. A browser extension's shipped artefact is the built
`.output/*` bundle, which runs inside the browser's own JavaScript
engine; Node only builds it. There is no equivalent "which Node does the
user have" question a matrix would answer.

## Decision

Pin a single Node version (`cookiecutter.node_version`, templated into
`package.json`'s `engines.node`, CI's `node-version`, and
`.readthedocs.yaml`'s `tools.nodejs`), kept current by the
`rotate-node-version` skill rather than tested across a range.

## Consequences

- CI has no Python-ADR-001-style version matrix — `build.yml`'s jobs each
  run once, against the one pinned Node version.
- A contributor building with a different local Node version than the
  pin isn't validated by CI either way; `engines.node` in `package.json`
  is advisory (npm/pnpm warn, don't block) unless `engine-strict` is set,
  which this template doesn't set — matching how cookiecutter-py doesn't
  hard-block an out-of-range local Python either.
````

- [ ] **Step 2: Write `{{ cookiecutter.github_project_name }}/.github/workflows/build.yml`**

```yaml
# https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-nodejs
name: CI

on:
  push: ~

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Set up pnpm
        uses: pnpm/action-setup@d9184bf108216479bc5a137cc391f4d7b14c870b # v6.1.0
      - name: Set up Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: '{{ cookiecutter.node_version }}'
          cache: pnpm
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      - name: Lint
        run: pnpm lint

  type-check:
    runs-on: ubuntu-latest
    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Set up pnpm
        uses: pnpm/action-setup@d9184bf108216479bc5a137cc391f4d7b14c870b # v6.1.0
      - name: Set up Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: '{{ cookiecutter.node_version }}'
          cache: pnpm
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      - name: Type checking
        run: pnpm typecheck

  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        target: [chrome, firefox]
    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Set up pnpm
        uses: pnpm/action-setup@d9184bf108216479bc5a137cc391f4d7b14c870b # v6.1.0
      - name: Set up Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: '{{ cookiecutter.node_version }}'
          cache: pnpm
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      - name: Build
        run: pnpm exec wxt build -b ${% raw %}{{ matrix.target }}{% endraw %}
```

- [ ] **Step 3: Regenerate the ADR index**

Run: `uv run python -m scripts.adr.generate_index`
Expected: `Generated docs/adr/INDEX.md (2 entries)`. Run only now, not
right after Step 1 — ADR 002's `scope` names `build.yml`, which Step 2
only just created.

- [ ] **Step 4: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

---

### Task 5: Unit tests (Vitest)

**Files:**
- Create: `{{ cookiecutter.github_project_name }}/vitest.config.ts`
- Create: `{{ cookiecutter.github_project_name }}/test/unit/popup.test.ts`
- Modify: `{{ cookiecutter.github_project_name }}/.github/workflows/build.yml` — add a `test` job

**Interfaces:**
- Consumes: `entrypoints/popup/main.ts` (Task 2).
- Produces: the `build.yml` `test` job name — Task 10's `generate-and-validate.yml` runs the same `pnpm test` command it wraps.

- [ ] **Step 1: Write `{{ cookiecutter.github_project_name }}/vitest.config.ts`**

```typescript
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';

export default defineConfig({
  plugins: [WxtVitest()],
  test: {
    environment: 'happy-dom',
    include: ['test/unit/**/*.test.ts'],
  },
});
```

- [ ] **Step 2: Write the failing test**

`{{ cookiecutter.github_project_name }}/test/unit/popup.test.ts`:

```typescript
import { describe, expect, it } from 'vitest';

describe('popup', () => {
  it('renders a greeting into #app', async () => {
    document.body.innerHTML = '<div id="app"></div>';
    await import('../../entrypoints/popup/main');
    const app = document.querySelector('#app');
    expect(app?.textContent).toBe(
      'Hello from {{ cookiecutter.project_name }}!',
    );
  });
});
```

- [ ] **Step 3: Run the test**

Run: `cd "{{ cookiecutter.github_project_name }}" && pnpm install`
Expected: exits 0 (dependencies already installed in Task 2 Step 19a; this
re-run just confirms nothing has drifted since).

Run: `pnpm test`
Expected: 1 passed.

Run: `cd .. && rm -rf "{{ cookiecutter.github_project_name }}/node_modules" "{{ cookiecutter.github_project_name }}/.wxt"`
Per the Global Constraints note — must happen before Step 5's commit.

- [ ] **Step 4: Add the `test` job to `build.yml`**

Insert a new job (after `type-check`, before `build`) in
`{{ cookiecutter.github_project_name }}/.github/workflows/build.yml`:

```yaml
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Set up pnpm
        uses: pnpm/action-setup@d9184bf108216479bc5a137cc391f4d7b14c870b # v6.1.0
      - name: Set up Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: '{{ cookiecutter.node_version }}'
          cache: pnpm
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      - name: Run tests
        run: pnpm test
```

- [ ] **Step 5: Commit**

Run `git status` to catch any related unstaged or untracked files (`pnpm-lock.yaml` included — it must be committed), then use the `creative-commits` skill.

---

### Task 6: ADR 003 — husky + lint-staged commit hooks

**Files:**
- Create: `docs/adr/003-husky-and-lint-staged-commit-hooks.md`
- Create: `{{ cookiecutter.github_project_name }}/.husky/pre-commit`

**Interfaces:**
- Consumes: `package.json` scripts `typecheck`/`test` (Tasks 2, 5) and the `lint-staged` config block (Task 2).

- [ ] **Step 1: Write ADR 003**

````markdown
---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/package.json", "{{ cookiecutter.github_project_name }}/.husky/pre-commit"]
summary: Use husky + lint-staged for commit hooks, running the full typecheck/test suite (not just staged-file lint) to match autohooks' thoroughness.
---

# 003: Use husky + lint-staged for Commit Hooks

## Context

cookiecutter-py's generated projects use `autohooks` (mode `pythonpath`,
not the `pre-commit` framework) to run `black`/`mypy`/`pytest`/`ruff` on
every commit — the *whole* suite, not just a diff of staged files.
`autohooks` is Python-specific tooling with no JS port.

## Decision

`husky` + `lint-staged`, the standard JS pairing. `lint-staged` alone only
lints/formats staged files, which is narrower than what `autohooks`
does — so `.husky/pre-commit` also runs the full `pnpm typecheck` and
`pnpm test` on every commit, matching `autohooks`' actual thoroughness
rather than lint-staged's usual (staged-files-only) convention.

## Consequences

- Commits are slower than a lint-staged-only setup would be (a full
  typecheck + test run, not just the staged diff) — an intentional
  trade-off for parity with cookiecutter-py's own commit-time guarantees.
- `package.json`'s `prepare` script (`husky`) installs the hook on
  `pnpm install`, mirroring `uv run autohooks activate` needing to be run
  once per clone for the Python template.
````

- [ ] **Step 2: Write `{{ cookiecutter.github_project_name }}/.husky/pre-commit`**

```sh
pnpm exec lint-staged
pnpm run typecheck
pnpm run test
```

- [ ] **Step 3: Regenerate the ADR index**

Run: `uv run python -m scripts.adr.generate_index`
Expected: `Generated docs/adr/INDEX.md (3 entries)`. Run only now, not
right after Step 1 — ADR 003's `scope` names `.husky/pre-commit`, which
Step 2 only just created.

- [ ] **Step 4: Make the hook executable and verify it installs**

Run: `chmod +x "{{ cookiecutter.github_project_name }}/.husky/pre-commit"`

Run: `cd "{{ cookiecutter.github_project_name }}" && pnpm install`
Expected: exits 0; `pnpm prepare`'s `husky` step runs without error (a git repo with a `.git` directory is required for husky to install the hook — if this fails because the templated directory isn't its own git repo, that's expected in this plan's own worktree since it's a subdirectory, not a generated project's real checkout; verify instead that `.husky/pre-commit` is present and executable, which is what a real generated project's `pnpm install` activates).

Run: `cd .. && rm -rf "{{ cookiecutter.github_project_name }}/node_modules" "{{ cookiecutter.github_project_name }}/.wxt"`
Per the Global Constraints note — must happen before Step 5's commit.

- [ ] **Step 5: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

---

### Task 7: ADR 004 — Playwright e2e scoped to Chromium, and e2e scaffold

**Files:**
- Create: `docs/adr/004-playwright-e2e-scoped-to-chromium.md`
- Create: `{{ cookiecutter.github_project_name }}/playwright.config.ts`
- Create: `{{ cookiecutter.github_project_name }}/test/e2e/fixtures.ts`
- Create: `{{ cookiecutter.github_project_name }}/test/e2e/popup.spec.ts`
- Modify: `{{ cookiecutter.github_project_name }}/.github/workflows/build.yml` — add an `e2e` job

**Interfaces:**
- Consumes: `entrypoints/popup/index.html` (Task 2), the `build` job's `wxt build -b chrome` output directory `.output/chrome-mv3` (Task 4).
- Produces: `test/e2e/fixtures.ts`'s `test`/`expect` exports (extending Playwright's own `test` with a `context`/`extensionId` fixture) — any future e2e spec imports from here, not from `@playwright/test` directly.

- [ ] **Step 1: Write ADR 004**

````markdown
---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/playwright.config.ts", "{{ cookiecutter.github_project_name }}/test/e2e/"]
summary: Playwright e2e coverage is Chromium-only — Playwright cannot load unpacked WebExtensions in Firefox. Firefox behaviour is covered by unit tests plus manual/web-ext run smoke-testing, not automated e2e.
---

# 004: Scope Playwright e2e to Chromium Only

## Context

Playwright's documented extension-testing pattern —
`chromium.launchPersistentContext()` with `--load-extension` — is
Chromium-specific. Playwright does not support loading an unpacked
WebExtension into its Firefox build the same way; this is a Playwright
limitation, not a WXT one; WXT itself builds a correct Firefox target
either way.

## Decision

Scope `test/e2e/` to Chromium only, rather than silently having no e2e
coverage at all or claiming Firefox coverage that doesn't exist. Firefox
behaviour is exercised by the shared Vitest unit tests (which don't
depend on either browser's extension-loading mechanics) plus manual
`web-ext run`/AMO review-queue smoke-testing before a release.

## Consequences

- `build.yml`'s `e2e` job builds and tests Chromium only; there is no
  Firefox equivalent job to add later without new tooling (e.g.
  Selenium/geckodriver), which is out of scope for this template.
- The `release` skill has no Firefox e2e step to reference, and none to
  add — Firefox correctness ahead of a release rests on the shared unit
  tests plus `pnpm build:firefox` succeeding, not on an automated e2e
  gate the skill could point to.
````

- [ ] **Step 2: Write `{{ cookiecutter.github_project_name }}/playwright.config.ts`**

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'test/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
});
```

- [ ] **Step 3: Write `{{ cookiecutter.github_project_name }}/test/e2e/fixtures.ts`**

```typescript
import { test as base, chromium, type BrowserContext } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dirname = path.dirname(fileURLToPath(import.meta.url));
// Built by `pnpm build` (wxt's default Chromium/MV3 output directory).
const EXTENSION_PATH = path.resolve(dirname, '../../.output/chrome-mv3');

export const test = base.extend<{
  context: BrowserContext;
  extensionId: string;
}>({
  // Playwright's test.extend() requires a literal object-destructuring
  // pattern here, even unused — the directive below must sit on the line
  // immediately above the code it covers, or it silently disables nothing.
  // eslint-disable-next-line no-empty-pattern
  context: async ({}, use) => {
    const context = await chromium.launchPersistentContext('', {
      headless: true,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    await use(context);
    await context.close();
  },
  extensionId: async ({ context }, use) => {
    let [worker] = context.serviceWorkers();
    if (!worker) {
      worker = await context.waitForEvent('serviceworker');
    }
    // Not `.split('/')[2]` — `.wxt/tsconfig.json` sets
    // noUncheckedIndexedAccess, which types that as `string | undefined`.
    const extensionId = new URL(worker.url()).hostname;
    await use(extensionId);
  },
});

export const expect = test.expect;
```

- [ ] **Step 4: Write `{{ cookiecutter.github_project_name }}/test/e2e/popup.spec.ts`**

```typescript
import { expect, test } from './fixtures';

test('popup renders a greeting', async ({ context, extensionId }) => {
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  await expect(page.locator('#app')).toHaveText(
    'Hello from {{ cookiecutter.project_name }}!',
  );
});
```

- [ ] **Step 5: Regenerate the ADR index**

Run: `uv run python -m scripts.adr.generate_index`
Expected: `Generated docs/adr/INDEX.md (4 entries)`. Run only now, not
right after Step 1 — ADR 004's `scope` names `playwright.config.ts` and
`test/e2e/`, which Steps 2–4 only just created.

- [ ] **Step 6: Build the extension and run the e2e test**

WXT reads `package.json`'s `version` field to build the manifest, and
that field is still the literal, unrendered `{{ cookiecutter.version }}`
in the tracked template directory — `wxt build` can't parse that as
semver. Like Task 8 Step 5, this needs a baked copy:

```bash
rm -rf /tmp/plan-verify
uvx "cookiecutter>=2,<3" . --no-input --output-dir /tmp/plan-verify
cd /tmp/plan-verify/my-browser-plugin
pnpm install
pnpm build
pnpm exec playwright install --with-deps chromium
pnpm test:e2e
```
Expected: every command exits 0 (`pnpm build` creates `.output/chrome-mv3/`;
`pnpm test:e2e` reports 1 passed). Playwright's browser install may need
system packages this sandbox doesn't grant — if `playwright install`
can't complete, `pnpm test:e2e` still fails with a clear "browser not
found" error, distinct from a real test failure. Nothing here touches
the tracked template directory, so no cleanup step is needed afterward.

- [ ] **Step 7: Add the `e2e` job to `build.yml`**

Insert a new job (after `build`) in
`{{ cookiecutter.github_project_name }}/.github/workflows/build.yml`:

```yaml
  e2e:
    runs-on: ubuntu-latest
    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Set up pnpm
        uses: pnpm/action-setup@d9184bf108216479bc5a137cc391f4d7b14c870b # v6.1.0
      - name: Set up Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: '{{ cookiecutter.node_version }}'
          cache: pnpm
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      - name: Build Chromium extension
        run: pnpm exec wxt build -b chrome
      - name: Install Playwright browsers
        run: pnpm exec playwright install --with-deps chromium
      - name: Run e2e tests
        run: pnpm test:e2e
```

- [ ] **Step 8: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

---

### Task 8: ADR 005 — TypeDoc on ReadTheDocs, and docs job

**Files:**
- Create: `docs/adr/005-typedoc-on-readthedocs.md`
- Create: `{{ cookiecutter.github_project_name }}/typedoc.json`
- Create: `{{ cookiecutter.github_project_name }}/.readthedocs.yaml`
- Modify: `{{ cookiecutter.github_project_name }}/.github/workflows/build.yml` — add a `docs` job

**Interfaces:**
- Consumes: `entrypoints/background.ts`, `entrypoints/popup/main.ts` (Task 2) as TypeDoc entry points; `package.json`'s `typedoc` script (Task 2).

- [ ] **Step 1: Write ADR 005**

````markdown
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
````

- [ ] **Step 2: Write `{{ cookiecutter.github_project_name }}/typedoc.json`**

```json
{
  "entryPoints": ["entrypoints/background.ts", "entrypoints/popup/main.ts"],
  "name": "{{ cookiecutter.project_name }}",
  "tsconfig": "./tsconfig.json"
}
```

- [ ] **Step 3: Write `{{ cookiecutter.github_project_name }}/.readthedocs.yaml`**

```yaml
# https://docs.readthedocs.io/en/stable/config-file/v2.html
version: 2

build:
  os: ubuntu-24.04
  tools:
    nodejs: '{{ cookiecutter.node_version }}'

  jobs:
    post_install:
      - corepack enable
      - pnpm install --frozen-lockfile
    build:
      html:
        - pnpm exec typedoc --out $READTHEDOCS_OUTPUT/html
```

- [ ] **Step 4: Regenerate the ADR index**

Run: `uv run python -m scripts.adr.generate_index`
Expected: `Generated docs/adr/INDEX.md (5 entries)`. Run only now, not
right after Step 1 — ADR 005's `scope` names `typedoc.json` and
`.readthedocs.yaml`, which Steps 2–3 only just created.

- [ ] **Step 5: Build the docs locally**

`typedoc`'s glob-based entry-point discovery can't handle the literal
`{{ }}` characters in `{{ cookiecutter.github_project_name }}`'s own
directory name, so — unlike `pnpm install`/`test`/`lint` — this needs a
baked copy, not the tracked template directory directly:

```bash
rm -rf /tmp/plan-verify
uvx "cookiecutter>=2,<3" . --no-input --output-dir /tmp/plan-verify
cd /tmp/plan-verify/my-browser-plugin
pnpm install
pnpm typedoc
```
Expected: every command exits 0, creates `docs/_build/html/index.html`
inside `/tmp/plan-verify/my-browser-plugin`. Nothing here touches the
tracked template directory, so no cleanup step is needed afterward.

- [ ] **Step 6: Add the `docs` job to `build.yml`**

Insert a new job (after `e2e`) in
`{{ cookiecutter.github_project_name }}/.github/workflows/build.yml`:

```yaml
  docs:
    runs-on: ubuntu-latest
    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Set up pnpm
        uses: pnpm/action-setup@d9184bf108216479bc5a137cc391f4d7b14c870b # v6.1.0
      - name: Set up Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: '{{ cookiecutter.node_version }}'
          cache: pnpm
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      - name: Check docs build
        run: pnpm typedoc
```

- [ ] **Step 7: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

---

### Task 9: ADR 006 — Renovate, and renovate.json (both repos)

**Files:**
- Create: `docs/adr/006-manage-updates-with-renovate.md`
- Create: `renovate.json` (this repo's own root)
- Create: `{{ cookiecutter.github_project_name }}/renovate.json`

- [ ] **Step 1: Write ADR 006**

````markdown
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
````

- [ ] **Step 2: Write `renovate.json`**

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "helpers:pinGitHubActionDigests"
  ]
}
```

- [ ] **Step 3: Write `{{ cookiecutter.github_project_name }}/renovate.json`**

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", "helpers:pinGitHubActionDigests"]
}
```

- [ ] **Step 4: Regenerate the ADR index**

Run: `uv run python -m scripts.adr.generate_index`
Expected: `Generated docs/adr/INDEX.md (6 entries)`. Run only now, not
right after Step 1 — ADR 006's `scope` names both `renovate.json` files,
which Steps 2–3 only just created.

- [ ] **Step 5: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

---

### Task 10: ADR 007 — validate the template by baking it, and generate-and-validate.yml

**Files:**
- Create: `docs/adr/007-validate-the-template-by-baking-it.md`
- Create: `.github/workflows/generate-and-validate.yml`

**Interfaces:**
- Consumes: every `package.json` script wired into `build.yml` across Tasks 2, 4, 5, 6, 7, 8 (`lint`, `typecheck`, `test`, `build`/`build:firefox`, `test:e2e`, `docs`) — this task runs the same commands against a freshly baked project rather than the checked-in templated directory.

- [ ] **Step 1: Write ADR 007**

````markdown
---
status: Accepted
date: 2026-09-10
scope: [test/, .github/workflows/generate-and-validate.yml]
summary: Validate the template by actually baking a project with cookiecutter and running its own lint/type-check/unit-test/build(-both-targets)/e2e/docs-build, not just static checks on the template files — matching cookiecutter-py's docs/adr/004.
---

# 007: Validate the Template by Baking It

## Context

`test/test_bake.py` (Task 2) checks the raw baked output's shape —
valid `package.json`, the right files present, symlinks intact — but
never actually installs dependencies or runs the generated project's own
tooling. A change to `package.json`'s dependency versions, `wxt.config.ts`,
or any CI/docs config could silently break what
`cookiecutter gh:todofixthis/cookiecutter-browser-plugin` produces, the
same gap cookiecutter-py's own docs/adr/004 closed for the Python
template.

## Decision

Add `.github/workflows/generate-and-validate.yml`: bakes a real project
and runs *that project's own* `pnpm install`, `pnpm lint`, `pnpm
typecheck`, `pnpm test`, `pnpm build`/`pnpm build:firefox`, `pnpm exec
playwright install --with-deps chromium` + `pnpm test:e2e`, and `pnpm
docs` — the same commands a human maintainer of a generated project would
run. `test/test_bake.py` stays the fast, always-run check; this workflow
is the slower, end-to-end one.

## Consequences

- CI now depends on network access to install the generated project's
  npm dependencies and Playwright's browser binary mid-run.
- Future changes to the templated project's `package.json`/CI/docs need
  to keep working under this workflow, not just render without Jinja
  errors.
````

- [ ] **Step 2: Write `.github/workflows/generate-and-validate.yml`**

```yaml
# Bakes a real project from this template with cookiecutter and validates the
# result the same way a maintainer of a generated project would: lint,
# type-check, test, build both targets, e2e-test the Chromium build, and
# build its docs.
name: Generate and Validate

on:
  push: ~

permissions:
  contents: read

jobs:
  generate:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version-file: "pyproject.toml"
      - name: Set up pnpm
        uses: pnpm/action-setup@d9184bf108216479bc5a137cc391f4d7b14c870b # v6.1.0
      - name: Set up Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: "22"
          # No `cache: pnpm` here — the project this job bakes doesn't exist
          # yet at this point in the job, so there's no pnpm-lock.yaml for
          # actions/setup-node to key a cache off (unlike build.yml's jobs,
          # which cache against the templated project's own committed
          # lockfile).
      - name: Bake a project with default answers
        run: uvx "cookiecutter>=2,<3" . --no-input --output-dir /tmp/baked
      - name: Install the generated project's dependencies
        run: pnpm install
        working-directory: /tmp/baked/my-browser-plugin
      - name: Lint the generated project
        run: pnpm lint
        working-directory: /tmp/baked/my-browser-plugin
      - name: Type-check the generated project
        run: pnpm typecheck
        working-directory: /tmp/baked/my-browser-plugin
      - name: Test the generated project
        run: pnpm test
        working-directory: /tmp/baked/my-browser-plugin
      - name: Build the generated project (both targets)
        run: pnpm build && pnpm build:firefox
        working-directory: /tmp/baked/my-browser-plugin
      - name: Install Playwright browsers
        run: pnpm exec playwright install --with-deps chromium
        working-directory: /tmp/baked/my-browser-plugin
      - name: e2e-test the generated project
        run: pnpm test:e2e
        working-directory: /tmp/baked/my-browser-plugin
      - name: Build the generated project's docs
        run: pnpm typedoc
        working-directory: /tmp/baked/my-browser-plugin
```

- [ ] **Step 3: Verify the generate-and-validate steps locally**

Run, from the repo root:
```bash
rm -rf /tmp/baked
uvx "cookiecutter>=2,<3" . --no-input --output-dir /tmp/baked
cd /tmp/baked/my-browser-plugin
pnpm install
pnpm lint && pnpm typecheck && pnpm test
pnpm build && pnpm build:firefox
pnpm exec playwright install --with-deps chromium
pnpm test:e2e
pnpm typedoc
```
Expected: every command exits 0 — this is the actual sequence
`generate-and-validate.yml` runs, exercised locally before trusting CI to
catch a mistake.

- [ ] **Step 4: Regenerate the ADR index**

Run, from the repo root: `uv run python -m scripts.adr.generate_index`
Expected: `Generated docs/adr/INDEX.md (7 entries)`. Run only now, not
right after Step 1 — ADR 007's `scope` names
`.github/workflows/generate-and-validate.yml`, which Step 2 only just
created; the ADR index generator hard-errors on a scope entry that
doesn't exist on disk yet.

- [ ] **Step 5: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

---

### Task 11: Own-repo README, final verification, and plan cleanup

**Files:**
- Create: `README.md`
- Modify: this plan file (deleted in the final step)

- [ ] **Step 1: Write `README.md`**

````markdown
# cookiecutter-browser-plugin

[![CI](https://github.com/todofixthis/cookiecutter-browser-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-browser-plugin/actions/workflows/ci.yml)
[![Generate and Validate](https://github.com/todofixthis/cookiecutter-browser-plugin/actions/workflows/generate-and-validate.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-browser-plugin/actions/workflows/generate-and-validate.yml)

A [cookiecutter](https://cookiecutter.readthedocs.io/) template for new browser extension projects, wired up with `WXT`, `pnpm`, Playwright, TypeDoc/ReadTheDocs docs, and the shared `phx` agent tooling from the start. Firefox is the primary target; Chromium is also supported.

## Usage

```bash
uv tool install cookiecutter  # once
cookiecutter gh:todofixthis/cookiecutter-browser-plugin
```

You'll be prompted for a project name, a short description, and an author name/email (defaults to Phoenix Zerin's); the current year is filled in automatically.

## What you get

- `WXT` (Vite-based, cross-browser Manifest V3) + `pnpm` packaging, `vitest` unit tests, `eslint`/`prettier` (via `husky` + `lint-staged`, run in full on every commit — not just staged files)
- Playwright e2e tests against the built Chromium extension (Firefox e2e isn't automatable — see `docs/adr/004`)
- TypeDoc docs on ReadTheDocs, GitHub Actions CI (lint, type-check, unit test, build both targets, e2e, docs), Renovate for dependency/Action updates
- `AGENTS.md`/`CLAUDE.md`, an ADR workflow under `docs/adr/`, and the `phx@todofixthis` skill marketplace enabled out of the box
- A guided `release` skill covering version bumps, GPG-signed release artefacts, and packaging for both the Chrome Web Store and Mozilla AMO (store submission itself stays a manual, developer-run step)

## Developing this template

See `AGENTS.md` for the dev workflow (`uv sync --group=dev`, `uv run pytest` bakes the template and checks the output, `uv run mypy hooks scripts test`, `uv run ruff check hooks scripts test`).
````

- [ ] **Step 2: Full own-repo verification**

Run: `uv run pytest`
Expected: 8 passed.

Run: `uv run mypy hooks scripts test`
Expected: `Success: no issues found`.

Run: `uv run ruff check hooks scripts test`
Expected: `All checks passed!`.

Run: `uv run python -m scripts.adr.generate_index`
Expected: `Generated docs/adr/INDEX.md (7 entries)`, and `git diff --exit-code docs/adr/INDEX.md` exits 0 (index already up to date).

- [ ] **Step 3: Full templated-project verification**

Like Task 7 Step 6 and Task 8 Step 5, `pnpm build`/`pnpm typedoc` can't
run against the tracked template directory itself (its `package.json`
version and directory name are still literal, unrendered Jinja) — bake
first, exactly as `generate-and-validate.yml` does:

```bash
rm -rf /tmp/plan-verify
uvx "cookiecutter>=2,<3" . --no-input --output-dir /tmp/plan-verify
cd /tmp/plan-verify/my-browser-plugin
pnpm install
pnpm lint && pnpm typecheck && pnpm test
pnpm build && pnpm build:firefox
pnpm exec playwright install --with-deps chromium
pnpm test:e2e
pnpm typedoc
```
Expected: every command exits 0. Nothing here touches the tracked
template directory, so no cleanup step is needed afterward.

- [ ] **Step 4: Commit the README**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

- [ ] **Step 5: Delete this plan file and commit**

Run: `rm docs/superpowers/plans/2026-09-10-browser-plugin-template.md`

Run `git status`, then use the `creative-commits` skill for a final commit
removing the plan — nothing that ships should reference a branch-scoped
planning document; the code carries the *what*, the seven ADRs carry the
*why*.

---

## Intentional Decisions

*(Populated during review — reviewers must not re-raise these)*

- **Task 2's step numbering skips from Step 1 to Step 3, and again jumps
  from Step 22 to Step 22a before Step 23.** ADR 001's "Regenerate the ADR
  index" step (originally Step 2) had to move to after `package.json` and
  `wxt.config.ts` exist (Steps 6–7) — the ADR index generator hard-errors
  on a scope entry that doesn't exist on disk yet. Renumbering all of
  Task 2's ~20 remaining steps to close the gap was judged not worth the
  risk of a manual renumbering error; the same pattern (an ADR-regenerate
  step relocated to just before its task's Commit step) was applied
  without a numbering gap in Tasks 4, 6, 7, 8, 9, and 10, where the step
  count was small enough to renumber cleanly instead.
- **ADR 002's `scope` covers only `build.yml`, not `.readthedocs.yaml`**,
  even though its Decision text also discusses `.readthedocs.yaml`'s
  `tools.nodejs`. `.readthedocs.yaml` isn't written until Task 8, four
  tasks later — scoping ADR 002 to it would mean the ADR index generator
  fails every regeneration from Task 4 through Task 7. The prose still
  documents the connection; only the machine-checked `scope` field is
  narrower than the decision's full reach.

## Self-Review Checklist

- [ ] Does the plan header include a `**Worktree:**` field naming the existing worktree and branch?
- [ ] Does every commit step remind the agent to run `git status` first?
- [ ] Does the plan include an Intentional Decisions section?
- [ ] Does the final task delete the plan file?
- [ ] Spec coverage: does every section of the design spec map to a task?
- [ ] Placeholder scan: no "TBD"/"TODO"/"implement later"/"similar to Task N" anywhere?
- [ ] Type/name consistency: do file paths, script names, and job names referenced across tasks match exactly where first defined?
