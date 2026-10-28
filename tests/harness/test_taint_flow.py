import pytest

from src.harness.contracts import TaskSpec
from src.harness.policy_engine import SensitiveLoggingPolicy

pytestmark = [pytest.mark.harness]

SPEC = TaskSpec(task_id="flow", goal="flow", allowed_paths=["*"], forbidden_paths=[])
VIA_VARIABLE = "def f(p):\n    msg = 'rut=' + p.rut\n    logger.info(msg)\n"


def violations(files: dict[str, str], track_flows: bool = True):
    found = SensitiveLoggingPolicy(track_flows=track_flows).evaluate(SPEC, files)
    return [f for f in found if f.status == "VIOLATION"]


def test_flow_finding_points_at_the_sink_and_names_the_origin():
    [f] = violations({"src/a.py": VIA_VARIABLE})
    assert (f.policy_id, f.severity, f.file, f.line) == ("privacy.cwe_532", "CRITICAL", "src/a.py", 3)
    assert f.evidence == "logger.info(msg)"
    assert "p.rut (src/a.py:2)" in f.message
    assert "msg" in f.message


def test_flow_crosses_files_through_an_imported_function():
    files = {
        "src/audit.py": "def audit(value):\n    logger.info('value=%s', value)\n",
        "src/service.py": "from audit import audit\n\ndef create(p):\n    audit(p.rut)\n",
    }
    [f] = violations(files)
    assert (f.file, f.line) == ("src/audit.py", 2)
    assert "p.rut (src/service.py:4)" in f.message
    assert "audit(value)" in f.message


def test_flow_through_a_return_value():
    code = "def describe(rec):\n    return 'dx ' + rec.diagnosis\n\ndef show(rec):\n    print(describe(rec))\n"
    [f] = violations({"src/r.py": code})
    assert (f.line, f.evidence) == (5, "print(describe(rec))")


def test_module_level_flow_is_detected():
    [f] = violations({"src/m.py": "x = patient.rut\nprint(x)\n"})
    assert f.line == 2


def test_a_direct_leak_is_reported_once():
    code = "def f(p):\n    logger.info(f'patient {p.rut} created')\n"
    assert len(violations({"src/a.py": code})) == 1


def test_recursive_calls_terminate():
    code = (
        "def f(x, n):\n    if n == 0:\n        return x\n    return f(x, n - 1)\n\n"
        "def g(p):\n    print(f(p.rut, 3))\n"
    )
    [f] = violations({"src/a.py": code})
    assert f.line == 7


def test_run_is_a_source_as_a_field_but_not_as_a_bare_variable():
    assert len(violations({"src/a.py": "def f(p):\n    v = p.run\n    print(v)\n"})) == 1
    assert violations({"src/a.py": "def f(rs):\n    run = rs[0]\n    v = run.get('score')\n    print(v)\n"}) == []


def test_without_flow_tracking_the_previous_local_behavior_holds():
    assert violations({"src/a.py": VIA_VARIABLE}, track_flows=False) == []
    direct = "def f(p):\n    logger.info(f'patient {p.rut} created')\n"
    assert len(violations({"src/a.py": direct}, track_flows=False)) == 1


def test_non_python_files_keep_the_line_scan():
    [f] = violations({"src/a.js": "const msg = user.rut;\nconsole.log(user.rut);\n"})
    assert f.line == 2
