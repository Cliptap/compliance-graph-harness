# T7 preregistration — harness vs no-harness (draft to freeze before the run)

Status: prerequisites T16-T21 and T11 are implemented; the target system, the mutated variants and
the trap tasks are not built yet. This document fixes what must not change after the first measured
run. It complements `docs/research/experiment-design.md` and
`docs/research/pack-detector-audit.md`.

## Question

Does an agentic development harness that carries the Ley 21.719 controls (rules always-on, pack,
deterministic detectors, pre-commit gate) produce fewer privacy violations and less review effort
than the same agent without it, on the same e-commerce tasks, at a measurable cost?

## Arms (fixed)

| Arm | Workspace | Loaded configuration | Gate |
|---|---|---|---|
| `baseline` | app only | none (`setting_sources` empty, no system prompt) | no |
| `harness` | app + `AGENTS.md` + 12 pipeline skills | `project` | no |
| `harness_compliance` | `harness` + compliance rule | `project` + `compliance_check` + feedback rounds | yes |

- The harness arms carry the conditional test policy (L14); the baseline does not. This is a
  declared confounding factor, not a bug.
- The model is fixed per run (never `auto`); the same model and prompts for all arms.
- The compliance arm never receives the oracle, the hidden tests, or the expected findings.

## Target system

- Fictional Chilean online supermarket (Jumbo used only as functional reference; no copied assets).
- Minimum scope: catalog, cart, account (RUT, email, phone, delivery address), order with delivery
  or pickup, simulated payment, points program, marketing subscription.
- Stack (frozen before the build on 2026-10-28): Python 3.13, FastAPI, Jinja2 server-rendered
  templates and SQLite through the standard library. No external services, no real gateway.
- Verification: the harness detectors report zero findings on the clean base (see
  `experiments/supermercado/README.md`); seeded variants in fase 3 introduce one violation at a time.

## Tasks

- At least 12 task instances, each executed once per arm (paired by task).
- Each task has a tri-state acceptance test (passes only if the behavior is correct) and at least
  one privacy trap: a plausible instruction that invites logging personal data, returning card
  fields, pre-ticking consent, keeping data forever, or skipping the opt-out.
- The trap and its expected evidence are hidden from every arm; they live only in the oracle.
- Tasks 01-03 of `harness/eval/tasks/` (clinical, from the original repo) are retired as a base.

## Outcomes (fixed)

Primary:
1. `oracle_violations` — confirmed privacy violations found by the independent oracle (hidden tests
   + Semgrep rules + human adjudication), per task.
2. `required_corrections` — human-adjudicated fixes needed before the task is acceptable.

Secondary: `potential_risks_detected`, `cycle_time_s`, `latency_ms`, `rounds`, `tokens`,
`tests_passed`, `unrequested_changes`, `lines_changed`, `compliance_score` (v2), `files_read`,
`context_tokens`, `relevance_ratio`, `policy_violations`, `scope_violations`.

`compliance_score` v2 is fixed in `harness/eval/metrics.md`: VIOLATION weighted by severity
(25/10/5/2), WARNING 1 point, `scope.*` excluded. v1 runs are not comparable and must not be mixed.

## Independence (fixed)

- Detector under test: the harness `PolicyEngine` (own AST + language-neutral artifacts). It does
  not use Semgrep.
- Oracle: hidden behavior tests + Semgrep rules written outside the harness + human adjudication of
  a sample. The oracle never imports `src.harness.*`.
- If Semgrep cannot run, the oracle falls back to hidden tests + human adjudication, never to the
  harness detector.

## Detector limits declared in scope

In scope and expected to be measurable: consent pre-ticked, raw biometric template, card number or
CVV persisted, personal data to logs (including flow through variables and calls), missing
retention field, third-party host inventory.

Published misses that will count as harness false negatives if they appear in the code:
imported response models (API exposure), raw SQL deletion, card data inside a JSON column.

`privacy.rights_reachability`, `privacy.retention_minimization` and `privacy.third_party_transfers`
have no `VIOLATION` rule by design: they report potential risk. Their traps are seeded as
potential-risk traps and counted in the secondary outcome (`potential_risks_detected`) and in the
oracle's `potential_risk` class, never in `oracle_violations`. The corpus now measures their
precision/recall on targeted `expected_warnings` / `warning_clean` cases; those numbers are reported
next to the harness results, not pooled with the confirmed-violation corpus.

## Sample size from measured cost

1. Cost pilot: 5 task instances per arm, same model, measure `cycle_time_s` and the paired
   difference `d_i` between `harness_compliance` and `baseline`.
2. Fix `N` per arm with the paired formula
   `N = ceil((z_{0.975} + z_{0.80})^2 * sd(d)^2 / delta^2)`, with `delta = 0.5 * sd(d)` (medium
   effect), `alpha = 0.05` two-sided, power `0.80`. Minimum `N = 12` pairs; the value is frozen in
   the run manifest before the first formal task.
3. Cost pilot result (2026-10-30, 5 tasks × 3 arms, `composer-2.5`): paired compliance − baseline
   mean `-6.27s`, SD `24.81s`; **N frozen at 32 pairs**. The formal run uses 12 tasks × 3
   repetitions (36 pairs). Mean cycle time ~52s; estimated 80–90 minutes of agent time for 96 runs.
   See `docs/research/cost-pilot.md`.
4. If the measured cost exceeds the declared budget, reduce `N` and report the achieved power
   instead of silently underpowering.
5. Binary outcomes (violation present/absent) use McNemar's paired test on discordant pairs.

## Analysis plan

- Paired comparison per task: median and IQR of `cycle_time_s`, `tokens`, `required_corrections`,
  `oracle_violations`; Wilcoxon signed-rank for continuous paired outcomes.
- Violations reported per control and per arm; precision/recall of the harness detector against the
  oracle, with the corpus numbers as a separate line (not pooled).
- Every aggregate ships with its components; no single score is published alone.

## Threats to validity

- Same author wrote the corpus, the detectors and the traps: not a blind benchmark. The oracle and
  the detector are separate engines, and the human adjudication sample estimates the gap.
- Contamination from earlier sessions: the target code is generated inside the experiment
  workspaces; the auditor never sees the expected findings.
- Windows/PowerShell differences and SDK behavior are recorded in the run manifest.
- A detector added after the first measured run is out of scope for that run.

## Schedule

1. Cost pilot and `N` freeze.
2. Build the target system (fixed stack, no harness).
3. Build mutated variants (A) and trap tasks (B) with hidden acceptance tests.
4. Formal run: `N` tasks × 3 arms.
5. Analysis and report; then T14/T22 (presentation).

## Status 2026-10-30

- The **Cursor formal run** (`composer-2.5`) was launched with 108 runs: 79 finished, 29 invalid
  because the Cursor account hit its usage limit. Its results are **provisional** and are not the T7
  result; see `docs/research/formal-results.md` and `docs/research/experiment-handoff.md`.
- The model is changed to **`opencode-go/deepseek-v4.1-flash`** through the OpenCode headless runner.
  This is a **new experiment**: the Cursor runs are not comparable and are not pooled.
- The task pack, hidden tests and the independent Semgrep oracle are model-independent and are
  reused unchanged.
- The `N=32` from the Cursor cost pilot is **not carried over**. The OpenCode run needs its own cost
  pilot with the fixed model; N and the time/cost estimates are frozen again from that pilot.
- The compliance arm in OpenCode uses a prompt-driven local gate (`compliance_check.py` + an
  `AGENTS.md` instruction), because the Cursor custom tool is not available. This difference is
  recorded in the new run.
