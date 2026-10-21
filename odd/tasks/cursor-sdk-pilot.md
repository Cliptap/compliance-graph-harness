# Feature: cursor-sdk-pilot
Objective: pilot runner on the Cursor SDK (Pro plan) that runs 1 task in 3 arms and records metrics. Branch: `feat/cursor-sdk-pilot`.
Delivery: ask-on-risk. Test runner: `python -m pytest tests/harness/test_cursor_pilot.py` (focused), `python -m pytest tests/` (suite).

## Specs

- **S1 — Cursor runtime.** The experiment runs on the user's Cursor Pro plan: "hay alguna forma de adaptar el experimento para usar los tokens del actual plan Pro de cursor que tengo?". Use the Python `cursor-sdk` (local runtime) with a fixed model id (never `auto`).
- **S2 — Three arms.** Accepted proposal: "un runner con el SDK en vibecoding que corre 1 tarea en los 3 brazos". Arms: `baseline` (clinical app only, no harness files, no system prompt, no ambient settings), `harness` (app + harness rules and pipeline skills projected into `.cursor/`), `harness_compliance` (`harness` + compliance engine exposed as a custom tool + gate loop). The compliance engine never lives inside any arm workspace.
- **S3 — One task.** Pilot task: `harness/eval/tasks/task_02_appointments_endpoint.md`, with an explicit scope sidecar (allowed/forbidden/relevant paths).
- **S4 — Metrics.** "registra las métricas". Capture, per run, the subset of the user's metric list that is measurable without new ground truth: cycle time, latency (SDK `duration_ms`), iterations (rounds and tool calls), tokens; tests passed; lines modified; unrequested changes and scope violations; policy violations; privacy findings (Ley N° 21.719 / CWE-532); compliance score; files retrieved; context relevance ratio. Metrics not yet measurable are reported as `null` with a reason.
- **S5 — Budget calibration.** "para validar que los tokens llegan y calcular cuántas corridas permite tu plan". The output must show whether token usage was reported and the tokens per run.
- **S6 — Dry run (assumption).** A `--dry-run` mode prepares and validates the arm workspaces without calling the SDK, so the pipeline can be checked without an API key.

## Tasks

| ID | Specs | Route | Status | Evidence |
|---|---|---|---|---|
| T1 | S2, S3 | inline | done | RED: `ImportError cursor_runner`; GREEN: workspace tests pass |
| T2 | S4 | inline | done | GREEN: metrics/policy/score/relevance tests pass |
| T3 | S1, S5, S6 | inline | done | GREEN: 16/16 focused, 67/67 suite; dry run 3 arms; `tests/demo` 21/21 inside isolated baseline workspace |
| T4 | S1, S5 | inline | blocked: needs `CURSOR_API_KEY` | |

Route evidence: one dependent chain of small units; no Writer trigger (no parallel independent units, no context backstop).

## Log

- **L1 (2026-10-21, user):** "si" — accepting: "¿Arranco con ese piloto? Sería un runner con el SDK en vibecoding que corre 1 tarea en los 3 brazos y registra las métricas, para validar que los tokens llegan y calcular cuántas corridas permite tu plan."
- **L2 (2026-10-21, analysis):** The previous runner's baseline (`harness/eval/runner.py:71-77`) instructs the model to over-engineer ("Sé prolijo, agregá lo que consideres necesario…"), biasing results toward the harness; the pilot baseline uses no system prompt. `AGENTS.md` Rule 1 ("PREGUNTÁ") can stall headless runs; all arms receive the same standard clarification reply, counted as a required correction. Baseline suite: `tests/demo` 21 passed.
- **L3 (2026-10-21):** Engram mirror pending: the Engram server runs from the Gentle-AI workspace and rejects project `compliance-graph-harness` as unknown.
- **L4 (2026-10-21):** T1-T3 implemented. SDK API checked against installed `cursor-sdk` 1.0.40 (`Agent.create`, `LocalAgentOptions.setting_sources/custom_tools`, `SDKToolUseMessage.call_id/name/status/args`). Read-tool names are unverified (`READ_TOOLS` in `pilot_metrics.py`); the first live run must confirm them from `tool_calls_by_name`. Risk: item 5 (new eval dependency `cursor-sdk`). Next: T4 live pilot once the user sets `CURSOR_API_KEY`.
