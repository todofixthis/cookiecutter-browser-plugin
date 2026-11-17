"""Bakes the template with default answers and checks the output is well-formed."""

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
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


def test_renovate_maintains_lock_file(baked_project: Path) -> None:
    """Renovate refreshes pnpm-lock.yaml and merges it once CI passes."""
    with (baked_project / "renovate.json").open(encoding="utf-8") as f_in:
        config = json.load(f_in)
    assert config["lockFileMaintenance"]["enabled"] is True
    assert config["lockFileMaintenance"]["automerge"] is True


def test_renovate_waits_for_releases_to_age(baked_project: Path) -> None:
    """Renovate raises an npm update only once the release is 3 days old."""
    with (baked_project / "renovate.json").open(encoding="utf-8") as f_in:
        config = json.load(f_in)
    assert "security:minimumReleaseAgeNpm" in config["extends"]


def test_pnpm_waits_for_releases_to_age(baked_project: Path) -> None:
    """pnpm resolves and installs only releases at least 3 days old."""
    text = (baked_project / "pnpm-workspace.yaml").read_text(encoding="utf-8")
    match = re.search(r"^minimumReleaseAge: (\d+)$", text, re.MULTILINE)
    assert match is not None
    # pnpm counts minutes
    assert int(match.group(1)) == 3 * 24 * 60
    assert re.search(r"^minimumReleaseAgeStrict: true$", text, re.MULTILINE)


def load_ci_jobs(project: Path) -> dict[str, dict[str, Any]]:
    """Parses the baked ``build.yml`` and returns its jobs by name."""
    workflow = yaml.safe_load(
        (project / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    )
    jobs: dict[str, dict[str, Any]] = workflow["jobs"]
    return jobs


def test_ci_job_names(baked_project: Path) -> None:
    """CI runs exactly the jobs the template documents."""
    assert set(load_ci_jobs(baked_project)) == {
        "build",
        "docs",
        "e2e",
        "gate",
        "lint",
        "test",
        "type-check",
    }


def test_ci_has_gate_needing_every_job(baked_project: Path) -> None:
    """The ``gate`` job aggregates every other job and fails on a non-success."""
    jobs = load_ci_jobs(baked_project)
    gate = jobs["gate"]
    assert set(gate["needs"]) == set(jobs) - {"gate"}
    assert gate["if"] == "always()"
    fail_conditions = [step.get("if", "") for step in gate["steps"]]
    assert any(
        all(result in condition for result in ("failure", "cancelled", "skipped"))
        for condition in fail_conditions
    )


def test_ci_is_one_workflow(baked_project: Path) -> None:
    """``build.yml`` is the only workflow, so ``gate`` can need every job."""
    workflows = baked_project / ".github" / "workflows"
    assert [path.name for path in workflows.iterdir()] == ["build.yml"]
