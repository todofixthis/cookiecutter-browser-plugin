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
