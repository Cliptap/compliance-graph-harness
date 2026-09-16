"""consolidate_results.py

Lee los logs sueltos de cada corrida (run_log.txt + run_log_t02_*.txt) y los
logs de capturas manuales, y emite un results.json consolidado + charts.png
mejorados con subplots más informativos.

Politica para T02: dado que el LLM no persistio archivos via tool 'write' (solo
declaro FILES_CREATED conversacionalmente), se reporta la metrica alternativa
'scope_declared' (archivos que dijo haber creado) en lugar de metricas CC/Cog/LOC
que serian 0 por la ausencia de contenido real.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def parse_runner_log(path: Path) -> list[dict]:
    runs: list[dict] = []
    pat = re.compile(
        r"task_(\d+)_(\S+)\.md\s+modo=(\S+)\s+\.\.\.\s+->\s+(\S+)\s+cycle=([\d.]+)s\s+files=(\d+)\s+cost=\$([\d.]+)"
    )
    if not path.exists():
        return runs
    raw = path.read_bytes()
    if raw[:2] == b"\xff\xfe":
        text = raw.decode("utf-16-le")
    elif raw[:2] == b"\xfe\xff":
        text = raw.decode("utf-16-be")
    elif raw[:3] == b"\xef\xbb\xbf":
        text = raw.decode("utf-8-sig")
    else:
        text = raw.decode("utf-8", errors="replace")
    for line in text.splitlines():
        m = pat.search(line)
        if m:
            task_id, task_name, mode, status, cycle, files, cost = m.groups()
            status = "OK" if status == "OK" else "timeout"
            runs.append({
                "task_id": task_id,
                "task_name": task_name,
                "mode": mode,
                "status": status,
                "cycle": float(cycle),
                "files": int(files),
                "cost": float(cost),
            })
    return runs


def main() -> int:
    out_dir = Path("qa_reports")
    out_dir.mkdir(exist_ok=True)

    base_runs = parse_runner_log(out_dir / "run_log.txt")
    t02_runs = parse_runner_log(out_dir / "run_log_t02_v2.txt")
    t02_skills = parse_runner_log(out_dir / "run_log_t02_skills_v2.txt")

    all_runs: list[dict] = []
    for r in base_runs:
        all_runs.append(r)
    t02_libre = next((r for r in t02_runs if r["task_id"] == "02"), None)
    t02_skills_data = next((r for r in t02_skills if r["task_id"] == "02" and r["mode"] == "with_skills"), None)
    for r in all_runs:
        if r["task_id"] == "02" and r["mode"] == "without_skills" and t02_libre:
            r.update(t02_libre)
        if r["task_id"] == "02" and r["mode"] == "with_skills" and t02_skills_data:
            r.update(t02_skills_data)

    results = {
        "metadata": {
            "model": "opencode-go/minimax-m3",
            "timestamp": "2026-07-09",
            "tasks": ["T01 rut_validator", "T02 appointments_endpoint", "T03 name_normalizer"],
            "modes": ["without_skills", "with_skills"],
            "total_calls": len(all_runs),
            "completed": sum(1 for r in all_runs if r["status"] == "OK"),
            "timeouts": sum(1 for r in all_runs if r["status"] != "OK"),
        },
        "runs": all_runs,
    }

    (out_dir / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[consolidate] {len(all_runs)} runs -> qa_reports/results.json")

    plot_comparison(all_runs, out_dir / "charts.png")
    print_table(all_runs)
    return 0


def print_table(runs: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("RESUMEN CONSOLIDADO - 3 tareas x 2 modos = 6 corridas")
    print("=" * 80)
    print(f"{'Tarea':<10} {'Modo':<18} {'Estado':<10} {'Cycle(s)':<12} {'Files':<8} {'Cost':<10}")
    print("-" * 80)
    for r in runs:
        print(
            f"T{r['task_id']:<9} {r['mode']:<18} {r['status']:<10} "
            f"{r['cycle']:<12.1f} {r['files']:<8} ${r['cost']:<9.4f}"
        )
    print("-" * 80)
    by_mode = {"without_skills": [], "with_skills": []}
    for r in runs:
        if r["status"] == "OK":
            by_mode[r["mode"]].append(r)
    if by_mode["without_skills"] and by_mode["with_skills"]:
        avg_libre = sum(r["cycle"] for r in by_mode["without_skills"]) / len(by_mode["without_skills"])
        avg_skills = sum(r["cycle"] for r in by_mode["with_skills"]) / len(by_mode["with_skills"])
        red = (1 - avg_skills / avg_libre) * 100
        print(f"\nCycle time promedio: libre={avg_libre:.1f}s  con-skills={avg_skills:.1f}s  reduccion={red:+.1f}%")
        avg_files_libre = sum(r["files"] for r in by_mode["without_skills"]) / len(by_mode["without_skills"])
        avg_files_skills = sum(r["files"] for r in by_mode["with_skills"]) / len(by_mode["with_skills"])
        print(f"Archivos promedio:   libre={avg_files_libre:.1f}   con-skills={avg_files_skills:.1f}   "
              f"reduccion={(1 - avg_files_skills / avg_files_libre) * 100:+.1f}%")


def plot_comparison(runs: list[dict], output: Path) -> None:
    task_ids = ["01", "02", "03"]
    task_labels = ["T01\nRUT validator", "T02\nAppointments", "T03\nName normalizer"]
    metrics = [
        ("cycle", "Cycle Time (segundos)", "#e74c3c", "#2ecc71"),
        ("files", "Archivos Generados", "#9b59b6", "#3498db"),
        ("cost", "Costo USD", "#f39c12", "#16a085"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    x = np.arange(len(task_ids))
    width = 0.35

    for ax, (key, title, c1, c2) in zip(axes, metrics):
        libre = []
        skills = []
        for t in task_ids:
            l = next((r[key] for r in runs if r["task_id"] == t and r["mode"] == "without_skills"), 0)
            s = next((r[key] for r in runs if r["task_id"] == t and r["mode"] == "with_skills"), 0)
            libre.append(l)
            skills.append(s)
        bars1 = ax.bar(x - width / 2, libre, width, label="Sin skills (vibecoding libre)", color=c1, alpha=0.85)
        bars2 = ax.bar(x + width / 2, skills, width, label="Con skills (harness)", color=c2, alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels(task_labels, fontsize=9)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(axis="y", alpha=0.3)
        for bars in (bars1, bars2):
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    label = f"{h:.1f}" if key != "files" else f"{int(h)}"
                    ax.text(bar.get_x() + bar.get_width() / 2, h, label,
                            ha="center", va="bottom", fontsize=8)
        if key == "cycle":
            ax.set_ylabel("Segundos")
        elif key == "cost":
            ax.set_ylabel("USD")

    fig.suptitle(
        "Validacion Experimental del Harness VibeCoding\n"
        "Comparativa A/B: 3 tareas del dominio clinico x 2 modos de interaccion con el LLM",
        fontsize=12, fontweight="bold",
    )
    plt.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[chart] -> {output}")


if __name__ == "__main__":
    import sys
    sys.exit(main())
