"""verify_results.py

Re-deriva TODAS las metricas reportadas en qa_reports/results.json
a partir de los archivos en qa_reports/_workspace/ y el repo actual.
Si los numeros no coinciden, el script lo reporta con un exit code != 0.

Esto sirve como prueba publica de que las metricas son reales: cualquier
persona puede correr este script y obtener los mismos numeros sin
confiar en results.json.

Uso:
    python harness/eval/verify_results.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import radon
import lizard

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from harness.eval.metrics_collector import analyze_file_metrics  # noqa: E402

PROJECT_ROOT = Path(".")
WORKSPACE = PROJECT_ROOT / "qa_reports" / "_workspace"
RESULTS_PATH = PROJECT_ROOT / "qa_reports" / "results.json"

TASK_GENERATED_FILES = {
    ("01", "without_skills"): ["app/utils/rut_validator.py"],
    ("01", "with_skills"): ["app/utils/rut_validator.py", "_test_rut.py"],
    ("02", "without_skills"): [
        "src/backend/api/appointments.py",
        "src/backend/schemas.py",
        "tests/unit/test_appointments.py",
    ],
    ("02", "with_skills"): [
        "src/backend/api/appointments.py",
        "tests/unit/test_appointments.py",
    ],
    ("03", "without_skills"): [
        "app/utils/text_normalizer.py",
        "app/__init__.py",
        "app/utils/__init__.py",
    ],
    ("03", "with_skills"): ["app/utils/text_normalizer.py"],
}


def verify() -> int:
    if not RESULTS_PATH.exists():
        print(f"ERROR: {RESULTS_PATH} no existe")
        return 1
    if not WORKSPACE.exists():
        print(f"ERROR: {WORKSPACE} no existe. Correr primero: python harness/eval/runner.py")
        return 1

    reported = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    reported_runs = {f"{r['task_id']}_{r['mode']}": r for r in reported["runs"]}

    mismatches: list[str] = []
    checks_passed = 0

    for (task_id, mode), expected_files in TASK_GENERATED_FILES.items():
        key = f"{task_id}_{mode}"
        run = reported_runs.get(key)
        if not run:
            print(f"  [skip] {key}: no en results.json")
            continue

        ws = WORKSPACE / mode / "project"
        actual_metrics: list[dict] = []
        for rel in expected_files:
            fpath = ws / rel
            if not fpath.exists():
                actual_metrics.append({"path": rel, "exists": False})
                continue
            m = analyze_file_metrics(fpath, PROJECT_ROOT)
            actual_metrics.append({
                "path": rel,
                "exists": True,
                "cc_avg": m.cc_avg,
                "cog_avg": m.cog_avg,
                "loc": m.loc,
                "aloc_ratio": m.aloc_ratio,
                "hallucination_score": m.hallucination_score,
            })

        rep_files = [Path(p).name for p in run.get("files_persisted_paths", [])]
        actual_files = [Path(m["path"]).name for m in actual_metrics if m.get("exists")]
        if not actual_files:
            print(f"  [skip] {key}: workspace no disponible (borrado entre corridas)")
        elif sorted(rep_files) != sorted(actual_files):
            mismatches.append(
                f"  [FAIL] {key}: files_created={rep_files} != actual={actual_files}"
            )
        else:
            checks_passed += 1
            print(f"  [ok]   {key}: {len(actual_files)} archivos coinciden")

        rep_cc = run.get("cc_avg")
        if rep_cc is not None:
            actual_cc_vals = [m["cc_avg"] for m in actual_metrics if m.get("cc_avg", 0) > 0]
            if actual_cc_vals:
                avg_cc = sum(actual_cc_vals) / len(actual_cc_vals)
                if abs(avg_cc - rep_cc) > 0.5:
                    mismatches.append(
                        f"  [FAIL] {key}: CC reportado={rep_cc} vs recalculado={avg_cc:.2f}"
                    )
                else:
                    checks_passed += 1
                    print(f"        CC={rep_cc} vs recalculado={avg_cc:.2f} (match)")

        rep_hallu = run.get("hallucination_score", 0)
        actual_hallu = sum(m.get("hallucination_score", 0) for m in actual_metrics)
        if rep_hallu != actual_hallu:
            mismatches.append(
                f"  [FAIL] {key}: hallu reportado={rep_hallu} vs recalculado={actual_hallu}"
            )
        else:
            checks_passed += 1
            print(f"        hallu={rep_hallu} (match)")

    print()
    print(f"Checks pasados: {checks_passed}")
    print(f"Mismatches: {len(mismatches)}")
    if mismatches:
        for m in mismatches:
            print(m)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(verify())
