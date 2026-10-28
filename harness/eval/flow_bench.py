"""Flow bench: three detectors of personal data in log sinks, scored on the same corpus cases.

- ``local``: ``SensitiveLoggingPolicy`` without data flow (the detector before call-level taint).
- ``lineage``: ``DataLineageEngine``, the file-level lineage graph, as the control. Each case is
  scanned next to a fixture model that declares sensitive fields, as a repository would.
- ``call_level``: ``SensitiveLoggingPolicy`` with call-level taint (the default).

Scored cases: corpus ids starting with ``log-`` or ``flow-``. A case is positive when its
expected set holds ``privacy.cwe_532``. Run: ``python -m harness.eval.flow_bench``.
"""
from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

from harness.eval.corpus import SPEC, load_cases
from src.harness.data_lineage import DataLineageEngine
from src.harness.db import init_harness_db
from src.harness.policy_engine import SensitiveLoggingPolicy

POLICY = "privacy.cwe_532"
PREFIXES = ("log-", "flow-")
FIXTURE_MODEL = (
    "class Patient(Base):\n"
    "    __tablename__ = 'patients'\n"
    "    rut = Column(String)\n"
    "    diagnosis = Column(String)\n"
    "    clinical_notes = Column(String)\n"
)


def log_cases(cases: list[dict] | None = None) -> list[dict]:
    return [c for c in (cases if cases is not None else load_cases()) if c["id"].startswith(PREFIXES)]


def _policy_detect(case: dict, track_flows: bool) -> bool:
    findings = SensitiveLoggingPolicy(track_flows=track_flows).evaluate(SPEC, {case["path"]: case["code"]})
    return any(f.policy_id == POLICY and f.status == "VIOLATION" for f in findings)


def local_detect(case: dict) -> bool:
    return _policy_detect(case, track_flows=False)


def call_level_detect(case: dict) -> bool:
    return _policy_detect(case, track_flows=True)


def lineage_detect(case: dict) -> bool:
    tmp = Path(tempfile.mkdtemp(prefix="flow-bench-"))
    try:
        app = tmp / "app"
        app.mkdir()
        (app / "models.py").write_text(FIXTURE_MODEL, encoding="utf-8")
        (app / "case.py").write_text(case["code"], encoding="utf-8")
        db = tmp / "harness.db"
        init_harness_db(db)
        engine = DataLineageEngine(db_path=db)
        engine.scan_and_build_lineage(root_dir=tmp, scan_dirs=[app])
        return any("app/case.py" in v["sink"] for v in engine.detect_violations())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


DETECTORS: dict[str, Callable[[dict], bool]] = {
    "local": local_detect,
    "lineage": lineage_detect,
    "call_level": call_level_detect,
}


def run(cases: list[dict] | None = None) -> dict[str, dict]:
    """Per detector: tp/fp/fn, precision and recall (None when undefined) and the missed or wrong ids."""
    scored = log_cases(cases)
    results: dict[str, dict] = {}
    for name, detect in DETECTORS.items():
        s: dict = {"tp": 0, "fp": 0, "fn": 0, "missed": [], "false_positives": []}
        for case in scored:
            expected, got = POLICY in case["expected"], detect(case)
            if expected and got:
                s["tp"] += 1
            elif got:
                s["fp"] += 1
                s["false_positives"].append(case["id"])
            elif expected:
                s["fn"] += 1
                s["missed"].append(case["id"])
        s["precision"] = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else None
        s["recall"] = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else None
        results[name] = s
    return results


if __name__ == "__main__":
    scored = log_cases()
    positives = sum(POLICY in c["expected"] for c in scored)
    print(f"{len(scored)} cases ({positives} seeded, {len(scored) - positives} clean)")
    for name, s in run().items():
        print(f"{name}: precision={s['precision']} recall={s['recall']} tp={s['tp']} fp={s['fp']} fn={s['fn']}")
        print(f"  missed={s['missed']}")
        print(f"  false_positives={s['false_positives']}")
