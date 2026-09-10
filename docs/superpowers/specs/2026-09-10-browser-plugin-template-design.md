# Design: cookiecutter-browser-plugin

## Purpose

A [cookiecutter](https://cookiecutter.readthedocs.io/) template for new browser
extension projects, mirroring `todofixthis/cookiecutter-py`'s principles and
capabilities (packaging, commit hooks, unit tests, CI, docs, ADR workflow,
agent tooling, release process) but for the WebExtension ecosystem. Firefox is
the primary target; Chromium is also supported. Playwright e2e scaffolding
has no Python-template equivalent.

## Architecture

Wherever a row below says "same as", "unchanged", or "carries over
verbatim", the implementing agent must read the corresponding file in
`todofixthis/cookiecutter-py` directly and port it — this spec does not
reproduce that content.

Same two-part split as cookiecutter-py:

- This repo's own dev tooling stays Python (`uv`, `pytest`, `mypy`, `ruff`,
  `autohooks`) — cookiecutter itself is a Python tool, with no need to run
  this repo's own test/lint/ADR-index tooling in JS. The ADR index generator
  (`scripts/adr/generate_index.py`, `.autohooks/adr_index.py`) carries over
  verbatim.
- `cookiecutter.json` / `hooks/pre_prompt.py` / `hooks/post_gen_project.py` —
  same prompt-and-hook shape as cookiecutter-py. Prompts: `author_email`,
  `author_name`, `project_name`, `github_project_name` (derived, same
  slugify pattern as cookiecutter-py), `github_username`, `package_name`
  (derived; used for `package.json`'s `name` and as the base of the Firefox
  extension ID), `project_short_description`, `gecko_extension_id` (derived:
  `{{ cookiecutter.package_name }}@{{ cookiecutter.github_username }}`, for
  `browser_specific_settings.gecko.id`), `node_version`, `this_year`
  (computed), `version`. `pre_prompt.py` fills in `this_year` only; unlike
  Python's `python_version`, `node_version` is a **static** `cookiecutter.json`
  default that the template maintainer updates periodically, not computed
  from the interpreter running cookiecutter — cookiecutter itself never needs
  Node installed, and there's no guarantee a Node is even present on the
  machine baking the template. `package.json` has no registry-publish
  concern (`private: true` — extensions ship as store artefacts, not npm
  packages), so there's no `pypi_project_name`-style derived registry name.
  `post_gen_project.py` restores the same two symlinks (`CLAUDE.md` →
  `AGENTS.md`, `.claude/skills` → `.agents/skills`).
- `{{ cookiecutter.github_project_name }}/` — the templated extension project,
  detailed below.
- `test/test_bake.py` — bakes with default answers, asserts no unrendered
  Jinja, valid `package.json`, expected `src/` layout, both symlinks survive.
- `.github/workflows/generate-and-validate.yml` — bakes a real project and
  runs *that project's own* lint/type-check/unit-test/build(-both-targets)/
  e2e/docs-build, same escalation cookiecutter-py uses to catch bugs static
  checks on the template files can't.

## Generated project tooling

| Concern | Choice | Rationale |
|---|---|---|
| Package manager | `pnpm`, version pinned via `package.json`'s `packageManager` field (Corepack) — the single source of truth CI (`pnpm/action-setup`, reading that field) and Renovate both key off | fast, modern; closest to `uv`'s role |
| Extension framework | **WXT** (Vite-based) | generates correct MV3 manifests for both Firefox and Chromium from one source tree — Firefox needs `background.scripts`, Chromium needs `background.service_worker`; WXT resolves this per build target instead of hand-maintaining two manifests |
| Language | TypeScript, `tsc --strict` | closest equivalent to `mypy --strict` |
| Lint/format | `eslint` (`typescript-eslint` type-checked config) + `prettier` | standard JS pairing, equivalent to `ruff`/`black` |
| Commit hooks | `husky` + `lint-staged` | standard JS pre-commit equivalent to `autohooks` |
| Unit tests | `vitest` | equivalent to `pytest` |
| e2e tests | **Playwright**, Chromium only | loads the *built* extension via `launchPersistentContext` + `--load-extension`, exercises the popup and background service worker. Firefox is excluded — Playwright cannot load unpacked WebExtensions in Firefox (a Playwright limitation, not WXT's); Firefox behaviour is covered by unit tests plus manual/`web-ext run` smoke-testing. Documented as an ADR, not silently scoped out. |
| Docs | **TypeDoc**, still hosted on **ReadTheDocs** via its `build.commands` custom-build support — the commands must explicitly copy TypeDoc's output into `$READTHEDOCS_OUTPUT/html/`, RTD's required location for a custom build | keeps the actual hosting capability like-for-like instead of switching to GitHub Pages |
| CI support width | single pinned Node LTS, **no version matrix** | Node is build tooling only here — the shipped artefact runs inside the browser, not on Node, so there's no equivalent to "support the 3 most recent Python releases" |
| Dependency updates | Renovate (`config:recommended` + `helpers:pinGitHubActionDigests`) | unchanged from cookiecutter-py |
| Licence | MIT | unchanged |
| Agent tooling | `AGENTS.md`/`CLAUDE.md` symlink pair, `.agents/skills` (symlinked to `.claude/skills`) | unchanged |

### Layout

```
{{ cookiecutter.github_project_name }}/
├── entrypoints/            # WXT convention: background.ts, popup/
├── test/unit/              # vitest
├── test/e2e/                # Playwright, Chromium-only
├── docs/                   # TypeDoc source + .readthedocs.yaml build.commands
├── .agents/skills/release/SKILL.md
├── .agents/skills/rotate-node-version/SKILL.md   # complete skill set — cookiecutter-py's generated
│                                                   # projects carry only these two equivalents (release,
│                                                   # rotate-python-versions); no third skill to port
├── wxt.config.ts
├── package.json / tsconfig.json / eslint config / prettier config
├── .github/workflows/build.yml
└── AGENTS.md, CLAUDE.md (symlink), renovate.json, LICENCE.txt, .gitignore
```

The placeholder extension is deliberately minimal, matching
`test_placeholder.py`'s role in cookiecutter-py: vanilla TypeScript + HTML,
no UI framework (no React/Vue/Svelte, and no matching eslint framework
plugin) — a popup that renders a greeting, a background entrypoint that logs
a startup message, one Vitest unit test, one Playwright e2e test asserting
the built extension loads in Chromium and the popup renders.

### CI (`build.yml`)

Jobs: `lint` (eslint+prettier check), `type-check` (`tsc --noEmit`), `test`
(vitest), `build` (matrix over `firefox`/`chrome` targets via `wxt build -b
<target>`), `e2e` (Playwright against the Chromium build), `docs` (TypeDoc
build via the same command ReadTheDocs runs). Same job-per-concern shape as
cookiecutter-py's `build.yml`, widened by one axis (build target) instead of
narrowed by the Python-version axis.

### Release skill

Adapted, not reused verbatim — extensions don't publish to a package
registry the way PyPI packages do:

1. Bump version (`package.json` + manifest via WXT), same research/draft/gate
   phases as the Python release skill (release notes, breaking-change gate,
   migration guide).
2. Build both targets and run `wxt zip` for each, producing a distributable
   `.zip` per target (`*-chrome.zip`, `*-firefox.zip`) — not a signed
   `.xpi`; a genuine AMO-signed `.xpi` only exists after Mozilla's manual
   signing step (3, below). GPG-sign both `.zip` files and create the GitHub
   release with them — same shape as the PyPI skill's build/sign/release
   steps.
3. **Store upload (AMO, Chrome Web Store) stays a manual, developer-run
   step** — it needs per-developer store API credentials, same spirit as the
   PyPI skill handing `UV_PUBLISH_TOKEN` back to the developer rather than
   assuming it's available to the agent. The developer submits the Firefox
   `.zip` to AMO by hand; the signed `.xpi` AMO returns can optionally be
   attached to the GitHub release afterwards.

### `rotate-node-version` skill

Equivalent to `rotate-python-versions`, simpler: one pinned version to bump
(`package.json` `engines.node`, CI's `node-version`, docs), not three.

## ADRs to write during implementation

One per non-obvious tooling choice above, matching cookiecutter-py's ADR
density: WXT as the extension framework; `pnpm`; single pinned Node version
instead of a matrix; Playwright scoped to Chromium only; TypeDoc-on-RTD via
custom build commands; `husky`+`lint-staged`; Renovate; validate-by-baking.

## Testing (this repo's own)

Same two-tier validation as cookiecutter-py: `test/test_bake.py` (fast,
structural, Python/pytest) and `generate-and-validate.yml` (slow, bakes a
real project and runs its own lint/type-check/test/build/e2e/docs-build).
`generate-and-validate.yml` needs Node installed via `actions/setup-node`
before it can `pnpm install` into the baked output.

## Out of scope

- Safari support (not requested).
- Automated AMO/Chrome Web Store submission (needs per-developer
  credentials; scoped to manual, same as the Python template's PyPI step).
- Firefox e2e automation (Playwright limitation; documented gap).
