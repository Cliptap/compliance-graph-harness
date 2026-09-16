"""plot_results.py

Genera qa_reports/charts.png con 3 subplots explicativos a partir del
results.json consolidado. Los graficos son claros y autocontenidos:
cada uno incluye titulo, leyenda, valores sobre las barras y unidades.

Subplots:
  1. Cycle time por tarea (con error bars si hay varianza)
  2. Archivos generados por tarea
  3. LOC del archivo principal por tarea
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load_runs(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["runs"]


def plot(runs: list[dict], output: Path) -> None:
    task_ids = ["01", "02", "03"]
    task_labels = [
        "T01\nRUT validator\n(modulo 11)",
        "T02\nAppointments\nendpoint",
        "T03\nName normalizer\n(Unicode NFC)",
    ]
    libre_cycle = []
    skills_cycle = []
    libre_files = []
    skills_files = []
    libre_loc = []
    skills_loc = []

    for t in task_ids:
        r_l = next((r for r in runs if r["task_id"] == t and r["mode"] == "without_skills"), None)
        r_s = next((r for r in runs if r["task_id"] == t and r["mode"] == "with_skills"), None)
        libre_cycle.append(r_l["cycle_time_seconds"] if r_l else 0)
        skills_cycle.append(r_s["cycle_time_seconds"] if r_s else 0)
        libre_files.append(r_l["files_persisted"] if r_l else 0)
        skills_files.append(r_s["files_persisted"] if r_s else 0)
        libre_loc.append(r_l["loc"] if (r_l and r_l["loc"] is not None) else 0)
        skills_loc.append(r_s["loc"] if (r_s and r_s["loc"] is not None) else 0)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    x = np.arange(len(task_ids))
    width = 0.35

    ax = axes[0]
    bars1 = ax.bar(x - width / 2, libre_cycle, width, label="Sin skills (libre)",
                   color="#e74c3c", alpha=0.85)
    bars2 = ax.bar(x + width / 2, skills_cycle, width, label="Con skills (harness)",
                   color="#2ecc71", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(task_labels, fontsize=9)
    ax.set_ylabel("Segundos", fontsize=10)
    ax.set_title("Cycle Time por tarea\n(menor = mejor)", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    for bars in (bars1, bars2):
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h, f"{h:.0f}s",
                        ha="center", va="bottom", fontsize=9)
    libre_avg = sum(c for c in libre_cycle if c > 0) / max(1, sum(1 for c in libre_cycle if c > 0))
    skills_avg = sum(c for c in skills_cycle if c > 0) / max(1, sum(1 for c in skills_cycle if c > 0))
    if libre_avg > 0 and skills_avg > 0:
        red = (1 - skills_avg / libre_avg) * 100
        ax.text(0.02, 0.95, f"Promedio exitoso:\nlibre {libre_avg:.0f}s vs skills {skills_avg:.0f}s\n↓ {red:+.0f}% con harness",
                transform=ax.transAxes, fontsize=8, va="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f0", alpha=0.8))

    ax = axes[1]
    bars1 = ax.bar(x - width / 2, libre_files, width, label="Sin skills (libre)",
                   color="#e74c3c", alpha=0.85)
    bars2 = ax.bar(x + width / 2, skills_files, width, label="Con skills (harness)",
                   color="#2ecc71", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(task_labels, fontsize=9)
    ax.set_ylabel("Cantidad de archivos .py", fontsize=10)
    ax.set_title("Archivos generados\n(menor = menos goldplating)", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    for bars in (bars1, bars2):
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}",
                        ha="center", va="bottom", fontsize=9)
    ax.text(0.02, 0.95, "T03: con skills eliminó 2\n__init__.py redundantes",
            transform=ax.transAxes, fontsize=8, va="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f0", alpha=0.8))

    ax = axes[2]
    bars1 = ax.bar(x - width / 2, libre_loc, width, label="Sin skills (libre)",
                   color="#e74c3c", alpha=0.85)
    bars2 = ax.bar(x + width / 2, skills_loc, width, label="Con skills (harness)",
                   color="#2ecc71", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(task_labels, fontsize=9)
    ax.set_ylabel("Líneas de código (LOC)", fontsize=10)
    ax.set_title("LOC del archivo principal\n(indicador de implementacion)", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    for bars in (bars1, bars2):
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}",
                        ha="center", va="bottom", fontsize=9)
    ax.text(0.02, 0.95, "T02 sin datos:\nLLM no persistio codigo\nen ninguna de las 2 corridas",
            transform=ax.transAxes, fontsize=8, va="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff4e1", alpha=0.9))

    fig.suptitle(
        "Validacion Experimental del Harness VibeCoding\n"
        "3 tareas del dominio clinico x 2 modos (libre vs con skills)  -  N=6 corridas, modelo opencode-go/minimax-m3",
        fontsize=12, fontweight="bold",
    )
    plt.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=130, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    in_path = Path("qa_reports/results.json")
    if not in_path.exists():
        print(f"ERROR: {in_path} no existe")
        return 1
    runs = load_runs(in_path)
    plot(runs, Path("qa_reports/charts.png"))
    print("[plot] -> qa_reports/charts.png")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
