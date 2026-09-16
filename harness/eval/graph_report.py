"""graph_report.py

Lee qa_reports/results.json y genera qa_reports/charts.png con 4 subplots:
  1. CC promedio por tarea (con vs sin skills)
  2. ALOC ratio por tarea
  3. Alucinaciones detectadas (imports inexistentes)
  4. Cycle time + thrashing
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def aggregate(runs: list[dict]) -> dict:
    by_task_mode: dict[tuple[str, str], dict] = {}
    for r in runs:
        if r.get("error"):
            continue
        key = (r["task_id"], r["mode"])
        cc_vals = [m.get("cc_avg", 0) for m in r.get("file_metrics", []) if m.get("cc_avg", 0) > 0]
        cog_vals = [m.get("cog_avg", 0) for m in r.get("file_metrics", []) if m.get("cog_avg", 0) > 0]
        aloc_vals = [m.get("aloc_ratio", 0) for m in r.get("file_metrics", [])]
        hallu_vals = [m.get("hallucination_score", 0) for m in r.get("file_metrics", [])]
        loc_vals = [m.get("loc", 0) for m in r.get("file_metrics", [])]
        by_task_mode[key] = {
            "task_id": r["task_id"],
            "task_name": r["task_name"],
            "mode": r["mode"],
            "cc_avg": float(np.mean(cc_vals)) if cc_vals else 0.0,
            "cog_avg": float(np.mean(cog_vals)) if cog_vals else 0.0,
            "aloc_avg": float(np.mean(aloc_vals)) if aloc_vals else 0.0,
            "hallu_total": int(sum(hallu_vals)),
            "loc_total": int(sum(loc_vals)),
            "cycle_time": r["cycle_time_seconds"],
            "thrashing": r["thrashing_index"],
            "file_count": len(r.get("file_metrics", [])),
        }
    return by_task_mode


def plot(by_task_mode: dict, output_path: Path) -> None:
    task_ids = sorted({k[0] for k in by_task_mode.keys()})
    metrics_to_plot = ["cc_avg", "cog_avg", "aloc_avg", "hallu_total", "cycle_time", "loc_total"]

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()
    titles = [
        "Complejidad Ciclomática (CC) promedio",
        "Complejidad Cognitiva promedio",
        "ALOC Ratio (goldplating)",
        "Alucinaciones detectadas (imports fantasma)",
        "Cycle Time (segundos)",
        "Líneas de código (LOC)",
    ]

    width = 0.35
    x = np.arange(len(task_ids))

    for ax, metric, title in zip(axes, metrics_to_plot, titles):
        libre = [by_task_mode.get((t, "without_skills"), {}).get(metric, 0) for t in task_ids]
        skills = [by_task_mode.get((t, "with_skills"), {}).get(metric, 0) for t in task_ids]
        ax.bar(x - width / 2, libre, width, label="Sin skills (libre)", color="#e74c3c", alpha=0.85)
        ax.bar(x + width / 2, skills, width, label="Con skills (AGENTS.md)", color="#2ecc71", alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels([f"T{t}" for t in task_ids])
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        for i, (l, s) in enumerate(zip(libre, skills)):
            if l > 0:
                ax.text(i - width / 2, l, f"{l:.1f}", ha="center", va="bottom", fontsize=7)
            if s > 0:
                ax.text(i + width / 2, s, f"{s:.1f}", ha="center", va="bottom", fontsize=7)

    fig.suptitle("Validación Experimental del Harness de Vibecoding\n"
                 "Impacto de las skills del AGENTS.md sobre la calidad del código generado por LLM",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[graph] -> {output_path}")


def print_table(by_task_mode: dict) -> None:
    task_ids = sorted({k[0] for k in by_task_mode.keys()})
    metrics = ["cc_avg", "cog_avg", "aloc_avg", "hallu_total", "cycle_time", "loc_total"]
    headers = ["Tarea", "Modo", "CC", "Cog", "ALOC", "Hallu", "Cycle(s)", "LOC"]
    print("\n" + " | ".join(f"{h:>10}" for h in headers))
    print("-" * (13 * len(headers)))
    for t in task_ids:
        for mode in ("without_skills", "with_skills"):
            d = by_task_mode.get((t, mode))
            if not d:
                row = [f"T{t}", mode, "-", "-", "-", "-", "-", "-"]
            else:
                row = [
                    f"T{t}", mode,
                    f"{d['cc_avg']:.2f}", f"{d['cog_avg']:.2f}",
                    f"{d['aloc_avg']:.3f}", str(d["hallu_total"]),
                    f"{d['cycle_time']:.1f}", str(d["loc_total"]),
                ]
            print(" | ".join(f"{c:>10}" for c in row))
        print("-" * (13 * len(headers)))


def main() -> int:
    in_path = Path("qa_reports/results.json")
    out_png = Path("qa_reports/charts.png")
    if not in_path.exists():
        print(f"ERROR: {in_path} no existe. Corré primero: python harness/eval/runner.py")
        return 1
    payload = json.loads(in_path.read_text(encoding="utf-8"))
    by_task_mode = aggregate(payload["runs"])
    print_table(by_task_mode)
    plot(by_task_mode, out_png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
