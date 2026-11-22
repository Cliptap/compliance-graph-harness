"""Runner guard: a dead provider must fail fast instead of masquerading as a timeout."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "experiments" / "tasks"
if str(TASKS) not in sys.path:
    sys.path.insert(0, str(TASKS))

from opencode_run import (  # noqa: E402
    _fatal_provider_line, _run_watched, format_gate_feedback, run_opencode,
)
from opencode_arms import auth_accounts, definition_of_done, prepare_sandbox  # noqa: E402


def _child(body: str) -> list[str]:
    return [sys.executable, "-u", "-c", body]


def test_fatal_provider_line_matches_quota_errors():
    line = ('timestamp=2026-11-20T02:46:32.952Z level=ERROR message="stream error" '
            'error.error="AI_APICallError: OpenCode Go usage limit reached (monthly)"')
    assert _fatal_provider_line(line) == line
    assert _fatal_provider_line('level=INFO message="read 12 files"') is None


def test_watched_run_aborts_on_fatal_provider_error():
    body = ("import sys,time\n"
            "sys.stderr.write('level=ERROR error.error=\"AI_APICallError: usage limit reached\"\\n')\n"
            "sys.stderr.flush()\n"
            "time.sleep(60)\n")
    started = time.perf_counter()
    result = _run_watched(_child(body), ROOT, os.environ.copy(), timeout=30)
    elapsed = time.perf_counter() - started
    assert result["timed_out"] is False
    assert "usage limit reached" in (result["fatal"] or "")
    assert elapsed < 20, f"the fatal line was not detected early enough: {elapsed:.1f}s"


def test_watched_run_reports_timeout_without_fatal_line():
    result = _run_watched(_child("import time\ntime.sleep(60)\n"), ROOT, os.environ.copy(),
                          timeout=1)
    assert result["timed_out"] is True
    assert result["fatal"] is None


def test_watched_run_keeps_normal_output():
    body = ('import json\nprint(json.dumps({"type": "step_finish", "part": {"reason": "stop"}}))\n')
    result = _run_watched(_child(body), ROOT, os.environ.copy(), timeout=30)
    assert result["timed_out"] is False
    assert result["fatal"] is None
    assert result["exit_code"] == 0
    assert '"step_finish"' in result["stdout"]


def test_auth_accounts_prefers_env_key(tmp_path):
    auth_file = tmp_path / "auth.json"
    auth_file.write_text('{"opencode-go": {"type": "api", "key": "stale"}, '
                         '"anthropic": {"type": "api", "key": "keep"}}', encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text('OPENCODEGO_API_KEY="fresh-key"\n', encoding="utf-8")
    accounts = auth_accounts(auth_file, env_file)
    assert accounts["opencode-go"]["key"] == "fresh-key"
    assert accounts["anthropic"]["key"] == "keep"


def test_definition_of_done_only_mentions_the_gate_when_present():
    assert "compliance_check.py" in definition_of_done(True)
    assert "compliance_check.py" not in definition_of_done(False)


def test_gate_feedback_resolves_catalog_control_titles():
    from types import SimpleNamespace

    finding = SimpleNamespace(
        status="VIOLATION", severity="BLOCKING", policy_id="privacy.cwe_532",
        file="app/leak.py", line=7, message="raw PII in log", evidence="rut",
        remediation_advice="mask the identifier",
    )
    text = format_gate_feedback([finding])
    assert "privacy.cwe_532" in text
    assert "control CORE-CHECK-002:" in text
    assert "control CL-DATAPROT-001:" in text


def test_gate_loop_issues_one_remediation_round(monkeypatch):
    calls = []

    def fake_invoke(workspace, prompt, model, timeout, env, session_id=None):
        calls.append(prompt)
        return {"events": [], "error": None, "exit_code": 0, "timed_out": False,
                "elapsed": 0.1, "session_id": "ses_test", "stderr": "", "stdout": "",
                "status": "finished"}

    state = {"first": True}

    def gate_check():
        if state["first"]:
            state["first"] = False
            return ("blocking violation: raw RUT in app/leak.py", 1)
        return ("", 0)

    monkeypatch.setattr("opencode_run._invoke", fake_invoke)
    result = run_opencode(ROOT, "do the task", "model", 10, {}, gate_enabled=True,
                          gate_check=gate_check, max_rounds=3, enforce=True)
    assert len(calls) == 2, "the gate feedback did not trigger a follow-up invoke"
    assert calls[1] == "blocking violation: raw RUT in app/leak.py"
    assert result["gate_rounds"] == 1
    assert result["gate_unresolved"] == 0
    assert result["status"] == "finished"


def test_gate_loop_does_not_run_when_disabled(monkeypatch):
    calls = []

    def fake_invoke(workspace, prompt, model, timeout, env, session_id=None):
        calls.append(prompt)
        return {"events": [], "error": None, "exit_code": 0, "timed_out": False,
                "elapsed": 0.1, "session_id": "ses_test", "stderr": "", "stdout": "",
                "status": "finished"}

    monkeypatch.setattr("opencode_run._invoke", fake_invoke)
    result = run_opencode(ROOT, "do the task", "model", 10, {}, gate_enabled=False,
                          gate_check=lambda: ("violation", 1), enforce=False)
    assert len(calls) == 1
    assert result["gate_rounds"] == 0


def test_prepare_sandbox_writes_env_credentials(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("OPENCODEGO_API_KEY=fresh-key\n", encoding="utf-8")
    monkeypatch.setattr("opencode_arms.auth_accounts",
                        lambda auth_file: auth_accounts(auth_file, env_file))
    sandbox = tmp_path / "sandbox"
    prepare_sandbox(sandbox, "opencode-go/deepseek-v4.1-flash", tmp_path / "missing.json")
    auth = json.loads((sandbox / "data" / "opencode" / "auth.json").read_text(encoding="utf-8"))
    assert auth["opencode-go"] == {"type": "api", "key": "fresh-key"}
