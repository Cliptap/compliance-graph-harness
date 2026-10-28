import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.harness.normative_pack import load_pack
from src.harness.precommit import (
    POLICY_CONTROLS, collect_staged, evaluate, format_report, install_hook, main,
)

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / ".harness" / "packs" / "cl-ley-21719.json"

LEAK = "import logging\nlogger = logging.getLogger(__name__)\n\ndef f(p):\n    logger.info(f'patient {p.rut} created')\n"
CLEAN = "import logging\nlogger = logging.getLogger(__name__)\n\ndef f(p):\n    logger.info('patient created')\n"
API_LEAK = "@router.get('/p/{pid}')\ndef get_p(pid):\n    p = load(pid)\n    return {'id': p.id, 'rut': p.rut}\n"


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), "-c", "core.autocrlf=false", *args],
                         capture_output=True, text=True, check=True)
    return out.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    return tmp_path


def stage(repo: Path, rel: str, content: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    git(repo, "add", rel)


def test_collect_staged_reads_the_index_not_the_working_tree(repo):
    stage(repo, "src/a.py", CLEAN)
    (repo / "src/a.py").write_text(LEAK, encoding="utf-8", newline="\n")
    assert collect_staged(repo) == {"src/a.py": CLEAN}


def test_collect_staged_skips_deleted_files_and_other_languages(repo):
    stage(repo, "src/a.py", CLEAN)
    stage(repo, "notes.md", "rut\n")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "rm", "-q", "src/a.py")
    stage(repo, "src/b.js", "console.log('ok')\n")
    assert collect_staged(repo) == {"src/b.js": "console.log('ok')\n"}


def test_leak_in_logs_blocks_with_control_and_article():
    result = evaluate({"src/a.py": LEAK}, PACK)
    assert result.blocked
    assert [f.policy_id for f in result.findings] == ["privacy.cwe_532"]
    report = format_report(result, PACK)
    assert "src/a.py:5" in report and "CORE-CHECK-002" in report
    assert "Art. 14° bis" in report and "no es asesoría legal" in report


def test_leak_through_a_call_across_staged_files_blocks_with_control():
    files = {
        "src/audit.py": "def audit(value):\n    logger.info('value=%s', value)\n",
        "src/service.py": "from audit import audit\n\ndef create(p):\n    audit(p.rut)\n",
    }
    result = evaluate(files, PACK)
    assert result.blocked
    assert [(f.policy_id, f.file, f.line) for f in result.findings] == [("privacy.cwe_532", "src/audit.py", 2)]
    report = format_report(result, PACK)
    assert "src/audit.py:2" in report and "CORE-CHECK-002" in report and "src/service.py:4" in report


def test_api_exposure_blocks():
    result = evaluate({"src/api.py": API_LEAK}, PACK)
    assert result.blocked
    assert {f.policy_id for f in result.findings} == {"privacy.api_exposure"}


def test_clean_change_passes_with_empty_report():
    result = evaluate({"src/a.py": CLEAN}, PACK)
    assert not result.blocked and result.findings == []
    assert format_report(result, PACK) == ""


def test_scope_and_domain_policies_do_not_run_in_the_gate():
    deletion = "def purge(db, rec):\n    db.delete(rec)\n"
    assert evaluate({"src/x.py": deletion}, PACK).findings == []


def test_test_and_fixture_paths_are_excluded():
    assert not evaluate({"tests/test_x.py": LEAK, "harness/eval/corpus/c.py": LEAK}, PACK).blocked


def test_every_gate_policy_maps_to_existing_pack_controls():
    ids = {c["id"] for c in load_pack(PACK)["controls"]}
    assert set(POLICY_CONTROLS) == {"privacy.cwe_532", "privacy.api_exposure", "privacy.payment_data_storage"}
    assert all(set(v) <= ids for v in POLICY_CONTROLS.values())


def test_main_exit_codes_follow_the_staged_content(repo, capsys):
    stage(repo, "src/a.py", CLEAN)
    assert main(["--root", str(repo), "--pack", str(PACK)]) == 0
    stage(repo, "src/a.py", LEAK)
    assert main(["--root", str(repo), "--pack", str(PACK)]) == 1
    assert "CORE-CHECK-002" in capsys.readouterr().err


def test_install_hook_blocks_a_real_commit(repo):
    install_hook(repo)
    hook = repo / ".git" / "hooks" / "pre-commit"
    assert hook.exists() and "src.harness.precommit" in hook.read_text(encoding="utf-8")
    stage(repo, "src/a.py", LEAK)
    proc = subprocess.run(["git", "-C", str(repo), "commit", "-m", "leak"], capture_output=True, text=True,
                          env={**os.environ, "PYTHONPATH": str(ROOT), "HARNESS_PYTHON": sys.executable})
    assert proc.returncode != 0
    assert "CORE-CHECK-002" in proc.stderr + proc.stdout
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", "HEAD"], capture_output=True)
    assert head.returncode != 0, "the blocked commit must not exist"


def test_install_hook_does_not_overwrite_a_foreign_hook(repo):
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        install_hook(repo)
    assert "mine" in hook.read_text(encoding="utf-8")
    install_hook(repo, force=True)
    assert "src.harness.precommit" in hook.read_text(encoding="utf-8")
