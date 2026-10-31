# T7 experiment handoff — 2026-10-30

## What is done

- **Task pack**: `experiments/tasks/` — 12 development tasks with a plausible privacy trap,
  hidden acceptance tests (`hidden/`), independent Semgrep oracle (`oracle/rules.yml`), `build.py`,
  `evaluate.py`. Commit `fe50c6e`.
- **Cost pilot (Cursor, `composer-2.5`)**: 5 tasks × 3 arms; N frozen at **32 pairs**;
  `docs/research/cost-pilot.md`. Commit `d347ca3`.
- **Formal Cursor run**: 108 runs launched (3 reps × 3 arms × 12 tasks). **79 finished, 29 invalid**
  because the Cursor account ran out of usage (`You're out of usage. Switch to Auto...`).
  - Reports: `qa_reports/formal/`; aggregates `aggregate_rep*_*.json`; analysis `analysis.json`.
  - **Provisional only** (`docs/research/formal-results.md`):
    baseline n=31, mean 61.5 s, hidden 29/31, oracle 2;
    harness n=24, 46.0 s, hidden 23/24, oracle 0;
    compliance n=24, 44.3 s, hidden 19/24, oracle 2;
    paired compliance−baseline n=24, mean −23.16 s, SD 44.46, sign test p=0.54, McNemar p=0.375.
  - Not comparable with any other model; do not mix.
- **OpenCode Go verified**: `opencode 1.17.18`; model `opencode-go/deepseek-v4.1-flash`
  available; headless `opencode run "<prompt>" --model ... --format json --auto --pure --dir <ws>`
  edited a file and returned tokens/cost in a 12 s smoke test.
- Runner/monitoring/analysis: `arms.py`, `run_arm.py`, `cost_pilot.py`, `formal_run.py`,
  `formal_all.py`, `formal_status.py`, `formal_analysis.py`, `formal_report.py`.

## Next steps (ordered)

1. **Adapt the runner to OpenCode** (`experiments/tasks/opencode_run.py`, `opencode_arms.py`):
   - Set a temporary `XDG_CONFIG_HOME` with a minimal `opencode.json` so the global persona/rules do
     not contaminate the baseline; keep the real data dir for auth (or copy `auth.json` to a temp
     data dir and remove it afterwards).
   - Run with the fixed model `opencode-go/deepseek-v4.1-flash`, `--format json`, `--auto`, `--pure`,
     `--dir <workspace>`; parse events for cycle time, tokens, cost and steps.
   - Baseline: no harness files. Harness: workspace `AGENTS.md` with the harness rules plus skills.
     Compliance: harness + a local `compliance_check.py` CLI (gate) and an `AGENTS.md` instruction to
     run it after changes; this replaces the Cursor custom tool.
2. Reuse `manifest.json`, hidden tests and Semgrep oracle unchanged.
3. Run a **new cost pilot** (5 tasks × 3 arms) with deepseek; refreeze N/time from that pilot.
4. Run the formal experiment (12 tasks × 3 reps × 3 arms) and analyse with
   `formal_analysis.py` / `formal_report.py`.
5. Keep the Cursor run archived as an aborted/provisional run; never pool models.

## Key files

- `experiments/tasks/manifest.json` — tasks, prompts, expected rules/controls.
- `experiments/tasks/hidden/` — oracle tests; not copied to the agent workspace.
- `experiments/tasks/oracle/rules.yml` — Semgrep rules; independent of `src.harness.*`.
- `experiments/tasks/{arms,run_arm,cost_pilot,formal_*}.py` — Cursor runner and analysis.
- `docs/research/preregistration.md` — model/N/status.
- `docs/research/cost-pilot.md` — Cursor pilot.
- `docs/research/formal-results.md` — provisional Cursor formal results.
- `qa_reports/formal/` — 108 per-run reports, aggregates, analysis.

## Caveats

- Cursor usage is exhausted; rep3 harness/compliance and 5 rep3 baseline cells are invalid.
- `formal_run.py --resume` now retries reports whose status is not `finished`.
- The OpenCode compliance gate is prompt-driven (local CLI), not a custom tool; record the difference
  in the new preregistration/results.
- `experiments/supermercado/tests/test_app.py` skips the photo test when photo assets are not copied
  into a workspace (the workspaces exclude them).
- Concurrent Cursor edits remain uncommitted in `docs/presentation/guion.md`,
  `presentacion.html` and `odd/tasks/harness-consolidation.md`.

## Prompt for the next session

"Continúa el experimento T7 con OpenCode Go y el modelo fijo `deepseek-v4.1-flash`. Leé
`docs/research/experiment-handoff.md` y `docs/research/preregistration.md`. Adaptá el runner y la
compuerta de cumplimiento a OpenCode, corré el nuevo piloto de costo, congelá N, corré el formal y
analizá. No mezcles los resultados de Cursor (quedaron provisionales por falta de uso)."
