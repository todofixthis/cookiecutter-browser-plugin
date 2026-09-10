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
