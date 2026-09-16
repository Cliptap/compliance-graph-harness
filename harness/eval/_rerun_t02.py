import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
from harness.eval.runner import run_single
sys.stdout.reconfigure(encoding='utf-8')
for mode in ("without_skills", "with_skills"):
    print(f"=== T02 {mode} ===")
    r = run_single(Path("harness/eval/tasks/task_02_appointments_endpoint.md"), Path("."), mode, "opencode-go/minimax-m3", 540)
    err = r.error or "OK"
    cost = r.llm_cost_usd
    print(f"  status: {err}  files: {len(r.files_created)}  cycle: {r.cycle_time_seconds:.0f}s  cost: ${cost:.4f}")
    for m in r.file_metrics:
        print(f"  - {m['path'][-50:]} cc={m['cc_avg']} loc={m['loc']} hallu={m['hallucination_score']}")
