from pathlib import Path

import pytest

from harness import render

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


@pytest.fixture
def fake_repo(tmp_path):
    h = tmp_path / "harness"
    _write(h / "rules/common/01_ask.md", b"---\nname: ask\n---\r\nPreguntar\r\n")
    _write(h / "rules/stacks/python.md", b"python rules\n")
    _write(h / "contexts/dev.md", b"dev context\n")
    _write(h / "agents/planner.md", b"planner\n")
    _write(h / "hooks/scripts/session_start.js", b"// start\n")
    _write(h / "templates/AGENTS.md", "# Reglas\r\n## Estructura ({{RUNTIME_NAME}})\r\n".encode())
    return tmp_path


def test_render_projects_every_source_into_the_antigravity_layout(fake_repo):
    written = render.render(fake_repo, "antigravity")

    assert sorted(written) == [
        ".agents/agents/planner.md",
        ".agents/contexts/vibecoding/dev.md",
        ".agents/hooks/scripts/session_start.js",
        ".agents/rules/01_ask.md",
        ".agents/rules/stacks/python.md",
        "AGENTS.md",
    ]
    assert (fake_repo / ".agents/rules/01_ask.md").read_bytes() == b"---\nname: ask\n---\r\nPreguntar\r\n"
    assert (fake_repo / "AGENTS.md").read_bytes() == "# Reglas\r\n## Estructura (Antigravity)\r\n".encode()


def test_check_reports_drift_without_writing(fake_repo):
    render.render(fake_repo, "antigravity")
    edited = fake_repo / ".agents/rules/01_ask.md"
    edited.write_bytes(b"edited by hand\n")
    (fake_repo / ".agents/agents/planner.md").unlink()

    drift = render.render(fake_repo, "antigravity", check=True)

    assert drift == [".agents/agents/planner.md", ".agents/rules/01_ask.md"]
    assert edited.read_bytes() == b"edited by hand\n"
    assert not (fake_repo / ".agents/agents/planner.md").exists()


def test_check_is_clean_right_after_render(fake_repo):
    render.render(fake_repo, "antigravity")

    assert render.render(fake_repo, "antigravity", check=True) == []


def test_unresolved_placeholder_fails_the_render(fake_repo):
    _write(fake_repo / "harness/templates/AGENTS.md", b"# {{RUNTIME_NAME}} {{MISSING_VALUE}}\n")

    with pytest.raises(render.RenderError, match="MISSING_VALUE"):
        render.render(fake_repo, "antigravity")
    assert not (fake_repo / "AGENTS.md").exists()


def test_unmanaged_files_are_left_untouched(fake_repo):
    _write(fake_repo / ".agents/hooks/hooks.json", b'{"enabled": true}\n')
    _write(fake_repo / ".agents/agents/eval-libre.md", b"eval\n")

    render.render(fake_repo, "antigravity")

    assert (fake_repo / ".agents/hooks/hooks.json").read_bytes() == b'{"enabled": true}\n'
    assert (fake_repo / ".agents/agents/eval-libre.md").read_bytes() == b"eval\n"


def test_cli_check_exit_codes(fake_repo, capsys):
    assert render.main(["--root", str(fake_repo), "--check"]) == 1
    assert "AGENTS.md" in capsys.readouterr().out

    assert render.main(["--root", str(fake_repo)]) == 0
    assert render.main(["--root", str(fake_repo), "--check"]) == 0


def test_repository_projections_are_in_sync_with_harness_sources():
    drift = render.render(REPO_ROOT, "antigravity", check=True)

    assert drift == [], (
        "Archivos generados desincronizados; edita la fuente en harness/ y ejecuta "
        f"`python -m harness.render`: {drift}"
    )
