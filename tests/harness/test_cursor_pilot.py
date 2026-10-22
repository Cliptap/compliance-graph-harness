import asyncio
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from harness.eval import cursor_runner
from harness.eval.pilot_arms import ARMS, prepare_workspace
from harness.eval.pilot_metrics import (
    changed_files,
    collect_event_stats,
    compliance_score,
    context_relevance,
    evaluate_policies,
    parse_pytest_summary,
)
from src.harness.contracts import Finding

pytestmark = [pytest.mark.harness, pytest.mark.governance]

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE = {
    "task_id": "T02",
    "goal": "GET /appointments",
    "allowed_paths": ["src/backend/api/appointments.py"],
    "forbidden_paths": ["src/database/*"],
}


def _git(ws: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ws, capture_output=True, text=True, check=True
    ).stdout


def test_baseline_workspace_contains_app_and_no_harness(tmp_path):
    ws = prepare_workspace(REPO_ROOT, "baseline", tmp_path / "baseline")

    assert (ws / "src/backend/api/appointments.py").is_file()
    assert (ws / "tests/demo/conftest.py").is_file()
    for leaked in ("AGENTS.md", ".cursor", ".agents", ".harness", "harness", "src/harness"):
        assert not (ws / leaked).exists(), leaked
    assert _git(ws, "status", "--porcelain") == ""
    assert _git(ws, "rev-parse", "HEAD").strip()


def test_harness_workspace_projects_rules_and_pipeline_skills(tmp_path):
    ws = prepare_workspace(REPO_ROOT, "harness", tmp_path / "harness")

    rule = (ws / ".cursor/rules/vibecoding-harness.mdc").read_text(encoding="utf-8")
    assert "alwaysApply: true" in rule
    assert "Preguntar, Nunca Asumir" in rule
    assert (ws / ".cursor/skills/01-prd/SKILL.md").is_file()
    assert (ws / ".cursor/skills/12-documentation/SKILL.md").is_file()
    assert not (ws / ".cursor/rules/compliance-gate.mdc").exists()
    assert not (ws / "src/harness").exists()
    assert _git(ws, "status", "--porcelain") == ""


def test_compliance_workspace_adds_gate_rule_but_not_engine(tmp_path):
    ws = prepare_workspace(REPO_ROOT, "harness_compliance", tmp_path / "hc")

    gate = (ws / ".cursor/rules/compliance-gate.mdc").read_text(encoding="utf-8")
    assert "compliance_check" in gate
    assert (ws / ".cursor/rules/vibecoding-harness.mdc").is_file()
    assert not (ws / "src/harness").exists()
    assert ARMS["harness_compliance"].compliance_tool is True
    assert ARMS["baseline"].setting_sources is None
    for skill in ("compliance-dev", "compliance-audit", "compliance-patch"):
        assert (ws / ".cursor/skills" / skill / "SKILL.md").is_file()
    assert (ws / ".harness/packs/cl-ley-21719.json").is_file()
    assert not (ws / ".harness/compliance_rules.json").exists()


def test_compliance_skills_and_pack_only_in_compliance_arm(tmp_path):
    ws = prepare_workspace(REPO_ROOT, "harness", tmp_path / "h")
    assert not (ws / ".cursor/skills/compliance-dev").exists()
    assert not (ws / ".harness").exists()


def test_compliance_skills_reference_existing_pack_and_outcome_vocabulary():
    for skill in ("compliance-dev", "compliance-audit", "compliance-patch"):
        text = (REPO_ROOT / ".agents/skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\nname: " + skill)
        assert ".harness/packs/cl-ley-21719.json" in text
    audit = (REPO_ROOT / ".agents/skills/compliance-audit/SKILL.md").read_text(encoding="utf-8")
    for outcome in ("confirmed_violation", "potential_risk", "not_applicable", "insufficient_evidence"):
        assert outcome in audit


def test_collect_event_stats_counts_each_tool_call_once_and_files_read():
    messages = [
        SimpleNamespace(type="tool_call", call_id="c1", name="read", status="running",
                        args={"path": "src/backend/schemas.py"}),
        SimpleNamespace(type="tool_call", call_id="c1", name="read", status="completed",
                        args={"path": "src/backend/schemas.py"}),
        SimpleNamespace(type="tool_call", call_id="c2", name="edit", status="completed",
                        args={"path": "src/backend/api/appointments.py"}),
        SimpleNamespace(type="usage", usage=SimpleNamespace(total_tokens=10)),
        SimpleNamespace(type="usage", usage=SimpleNamespace(total_tokens=5)),
    ]

    stats = collect_event_stats(messages)

    assert stats.tool_calls == 2
    assert stats.tool_calls_by_name == {"read": 1, "edit": 1}
    assert stats.files_read == ["src/backend/schemas.py"]
    assert stats.turns == 2


def test_changed_files_reports_modified_and_new_files(tmp_path):
    ws = tmp_path / "repo"
    ws.mkdir()
    (ws / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(ws, "init", "-q")
    _git(ws, "add", "-A")
    _git(ws, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
    (ws / "a.py").write_text("x = 2\ny = 3\n", encoding="utf-8")
    (ws / "b.py").write_text("z = 1\n", encoding="utf-8")

    changes = changed_files(ws)

    assert changes == {"a.py": (2, 1), "b.py": (1, 0)}


def test_changed_files_reports_renames_as_delete_plus_add_and_keeps_privacy_findings(tmp_path):
    ws = prepare_workspace(REPO_ROOT, "baseline", tmp_path / "ws")
    old = ws / "src/backend/schemas.py"
    content = old.read_text(encoding="utf-8")
    old.unlink()
    (ws / "src/backend/schemas_v2.py").write_text(
        content + "\nlogging.info('rut %s', patient.rut)\n", encoding="utf-8"
    )

    changes = changed_files(ws)
    findings = evaluate_policies(ws, changes, SCOPE)

    assert set(changes) == {"src/backend/schemas.py", "src/backend/schemas_v2.py"}
    assert changes["src/backend/schemas.py"][0] == 0
    assert "privacy.cwe_532" in {f.policy_id for f in findings}


def test_changed_files_ignores_line_ending_only_rewrites(tmp_path):
    ws = prepare_workspace(REPO_ROOT, "baseline", tmp_path / "ws")
    target = ws / "src/backend/schemas.py"
    text = target.read_bytes().decode("utf-8").replace("\r\n", "\n")

    target.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    assert changed_files(ws) == {}

    target.write_bytes((text + "a = 1\nb = 2\nc = 3\n").encode("utf-8"))
    assert changed_files(ws) == {"src/backend/schemas.py": (3, 0)}


def test_changed_files_handles_non_ascii_paths(tmp_path):
    ws = prepare_workspace(REPO_ROOT, "baseline", tmp_path / "ws")
    (ws / "src/backend/api/citas_año.py").write_text("x = 1\n", encoding="utf-8")

    assert changed_files(ws) == {"src/backend/api/citas_año.py": (1, 0)}


def test_evaluate_policies_flags_scope_and_cwe_532(tmp_path):
    (tmp_path / "src/database").mkdir(parents=True)
    (tmp_path / "src/database/models.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src/backend/api").mkdir(parents=True)
    (tmp_path / "src/backend/api/appointments.py").write_text(
        "logger.info(f'paciente {patient.rut}')\n", encoding="utf-8"
    )

    findings = evaluate_policies(
        tmp_path, ["src/database/models.py", "src/backend/api/appointments.py"], SCOPE
    )
    policy_ids = {f.policy_id for f in findings}

    assert "scope.forbidden_path" in policy_ids
    assert "privacy.cwe_532" in policy_ids


def test_compliance_score_weights_severity_and_ignores_scope():
    privacy = Finding(policy_id="privacy.cwe_532", severity="CRITICAL", file="a.py", message="m")
    scope = Finding(policy_id="scope.forbidden_path", severity="CRITICAL", file="b.py", message="m")

    assert compliance_score([]) == 100.0
    assert compliance_score([privacy]) == 75.0
    assert compliance_score([scope]) == 100.0
    assert compliance_score([privacy] * 5) == 0.0


def test_context_relevance_ratio():
    assert context_relevance(["a", "b", "c"], ["a", "b", "z"]) == pytest.approx(2 / 3)
    assert context_relevance([], ["a"]) is None


def test_parse_pytest_summary():
    assert parse_pytest_summary("== 3 passed, 1 failed, 2 errors in 0.5s ==") == {
        "passed": 3, "failed": 1, "errors": 2,
    }
    assert parse_pytest_summary("21 passed in 0.39s") == {"passed": 21, "failed": 0, "errors": 0}


def test_dry_run_prepares_all_arms_without_calling_sdk(tmp_path, monkeypatch):
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    out = tmp_path / "out"

    exit_code = cursor_runner.main([
        "--dry-run",
        "--workspace-root", str(tmp_path / "ws"),
        "--out-dir", str(out),
    ])

    assert exit_code == 0
    report = json.loads(next(out.glob("pilot_*.json")).read_text(encoding="utf-8"))
    assert report["metadata"]["dry_run"] is True
    assert [r["arm"] for r in report["runs"]] == ["baseline", "harness", "harness_compliance"]
    assert all(r["status"] == "prepared" for r in report["runs"])
    assert all(Path(r["workspace"]).is_dir() for r in report["runs"])


class FakeRun:
    """Imita `AsyncRun`: `messages()` es iterable asíncrono; `wait` y `cancel` son corrutinas."""

    def __init__(self, run_id: str, hang: bool = False):
        self.id = run_id
        self.status = "running" if hang else "finished"
        self.hang = hang
        self.cancelled = False

    async def _stream(self):
        yield SimpleNamespace(type="usage", usage=SimpleNamespace(total_tokens=1))
        if self.hang:
            await asyncio.sleep(3600)

    def messages(self):
        return self._stream()

    async def wait(self):
        status = "cancelled" if self.cancelled else "finished"
        return SimpleNamespace(status=status, duration_ms=100,
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5))

    async def cancel(self):
        self.cancelled = True
        self.status = "cancelled"


class FakeAgent:
    """Simula el agente: cada envío aplica la edición correspondiente al workspace."""

    def __init__(self, edits, hang: bool = False):
        self.edits = list(edits)
        self.sent = []
        self.hang = hang

    async def send(self, message):
        self.sent.append(message)
        edit = self.edits.pop(0) if self.edits else None
        if edit:
            edit()
        return FakeRun(f"run-{len(self.sent)}", hang=self.hang)


def _drive(agent, plan, settings=None):
    rounds, messages = [], []
    asyncio.run(cursor_runner._drive_rounds(agent, plan, settings or SETTINGS, rounds, messages))
    return rounds


def _plan(tmp_path, arm):
    ws = prepare_workspace(REPO_ROOT, arm, tmp_path / arm)
    task = REPO_ROOT / cursor_runner.DEFAULT_TASK
    return cursor_runner.RunPlan(ARMS[arm], ws, "tarea", cursor_runner.load_scope(task))


def _append(path: Path, text: str):
    return lambda: path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


SETTINGS = cursor_runner.LiveSettings("composer-2.5", "key", max_rounds=3, timeout_s=60)
LEAK = "\n\ndef _audit(patient):\n    logger.info(f'paciente {patient.rut}')\n"


def test_no_changes_triggers_the_standard_clarification_reply(tmp_path):
    plan = _plan(tmp_path, "baseline")
    target = plan.workspace / "src/backend/api/appointments.py"
    agent = FakeAgent([None, _append(target, "\n# filtros\n")])

    rounds = _drive(agent, plan)

    assert [r["kind"] for r in rounds] == ["task", "clarification"]
    assert agent.sent[1] == cursor_runner.CLARIFICATION_REPLY


def test_compliance_arm_feeds_violations_back_until_clean(tmp_path):
    plan = _plan(tmp_path, "harness_compliance")
    target = plan.workspace / "src/backend/api/appointments.py"
    original = target.read_text(encoding="utf-8")
    agent = FakeAgent([_append(target, LEAK), lambda: target.write_text(original + "\n# ok\n",
                                                                         encoding="utf-8")])

    rounds = _drive(agent, plan)

    assert [r["kind"] for r in rounds] == ["task", "compliance_feedback"]
    assert "privacy.cwe_532" in agent.sent[1]


def test_baseline_arm_gets_no_compliance_feedback(tmp_path):
    plan = _plan(tmp_path, "baseline")
    target = plan.workspace / "src/backend/api/appointments.py"
    agent = FakeAgent([_append(target, LEAK)])

    rounds = _drive(agent, plan)

    assert [r["kind"] for r in rounds] == ["task"]


def test_send_timeout_cancels_the_run_and_stops_rounds(tmp_path):
    plan = _plan(tmp_path, "baseline")
    agent = FakeAgent([None], hang=True)

    rounds = _drive(agent, plan, cursor_runner.LiveSettings("composer-2.5", "key", 3, timeout_s=1))

    assert [r["status"] for r in rounds] == ["cancelled"]
    assert rounds[0]["timed_out"] is True


def test_compliance_tool_reports_findings_for_changed_files(tmp_path):
    plan = _plan(tmp_path, "harness_compliance")
    _append(plan.workspace / "src/backend/api/appointments.py", LEAK)()

    tool = cursor_runner.compliance_tool(plan.workspace, plan.scope)
    output = tool.execute({}, None)

    assert "privacy.cwe_532" in output


def test_summarize_run_reports_metric_groups(tmp_path):
    plan = _plan(tmp_path, "baseline")
    _append(plan.workspace / "src/backend/api/appointments.py", LEAK)()
    (plan.workspace / "src/database/extra.py").write_text("x = 1\n", encoding="utf-8")
    rounds = [{"kind": "task", "status": "finished", "duration_ms": 100, "wall_s": 1.0,
               "usage": {"input_tokens": 10, "output_tokens": 5}},
              {"kind": "clarification", "status": "finished", "duration_ms": 50, "wall_s": 0.5,
               "usage": {"input_tokens": 3, "output_tokens": 2}}]
    messages = [SimpleNamespace(type="tool_call", call_id="c1", name="read", status="completed",
                                args={"path": str(plan.workspace / "src/database/models.py")})]

    summary = cursor_runner.summarize_run(
        plan, {"status": "finished", "rounds": rounds, "messages": messages, "cycle_time_s": 2.0}
    )

    assert summary["efficiency"]["tokens"] == {"input_tokens": 13, "output_tokens": 7}
    assert summary["efficiency"]["latency_ms"] == 150
    assert summary["efficiency"]["usage_reported"] is True
    assert summary["quality"]["files_changed"] == 2
    assert summary["quality"]["tests"]["passed"] == 21
    assert summary["governance"]["privacy_findings"] >= 1
    assert summary["governance"]["scope_violations"] == 1
    assert summary["governance"]["compliance_score"] < 100
    assert summary["context"]["files_read"] == ["src/database/models.py"]
    assert summary["context"]["relevance_ratio"] == 1.0
    assert summary["review"]["required_corrections"] == 1


@pytest.mark.parametrize("argv", [
    ["--dry-run", "--model", "AUTO"],
    ["--dry-run", "--arms", "baseline,bogus"],
    ["--dry-run", "--reps", "0"],
])
def test_invalid_options_are_rejected_before_preparing(tmp_path, argv):
    with pytest.raises(SystemExit) as exc:
        cursor_runner.main([*argv, "--workspace-root", str(tmp_path / "ws"),
                            "--out-dir", str(tmp_path / "out")])

    assert exc.value.code == 2
    assert not (tmp_path / "ws").exists()


def test_gate_rounds_are_not_counted_as_required_corrections(tmp_path):
    plan = _plan(tmp_path, "harness_compliance")
    rounds = [{"kind": kind, "status": "finished", "duration_ms": 1, "wall_s": 0.1, "usage": None}
              for kind in ("task", "compliance_feedback", "clarification")]

    summary = cursor_runner.summarize_run(plan, {"status": "finished", "rounds": rounds,
                                                 "messages": [], "cycle_time_s": 1.0})

    assert summary["review"]["required_corrections"] == 1
    assert summary["governance"]["gate_rounds"] == 1


def test_compliance_tool_ignores_paths_outside_workspace(tmp_path):
    plan = _plan(tmp_path, "harness_compliance")
    outside = tmp_path / "secret.py"
    outside.write_text("logging.info('rut %s', rut)\n", encoding="utf-8")

    output = cursor_runner.compliance_tool(plan.workspace, plan.scope).execute(
        {"files": [str(outside)]}, None
    )

    assert "privacy.cwe_532" not in output


def test_api_key_is_read_from_env_file_when_variable_is_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("# comentario\nOTHER=1\nCURSOR_API_KEY = \"key-from-file\"\n", encoding="utf-8")

    assert cursor_runner.load_api_key(env_file) == "key-from-file"
    assert cursor_runner.load_api_key(tmp_path / "missing.env") == ""


def test_environment_variable_wins_over_env_file(tmp_path, monkeypatch):
    monkeypatch.setenv("CURSOR_API_KEY", "key-from-env")
    env_file = tmp_path / ".env"
    env_file.write_text("CURSOR_API_KEY=key-from-file\n", encoding="utf-8")

    assert cursor_runner.load_api_key(env_file) == "key-from-env"


def test_api_key_is_not_in_settings_repr():
    assert "secret-key" not in repr(cursor_runner.LiveSettings("m", "secret-key", 1, 1))


def test_live_run_without_api_key_fails_before_preparing(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)

    exit_code = cursor_runner.main(["--workspace-root", str(tmp_path / "ws"),
                                    "--out-dir", str(tmp_path / "out"),
                                    "--env-file", str(tmp_path / "missing.env")])

    assert exit_code == 1
    assert "CURSOR_API_KEY" in capsys.readouterr().err
    assert not (tmp_path / "ws").exists()
