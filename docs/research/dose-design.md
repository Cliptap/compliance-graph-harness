# Dose design â€” which harness component reduces violations?

Status: **run complete** (2026-11-02); see dose-conclusions.md for the result. This experiment isolates the contribution of the
rules, the skills, the gate's instruction/CLI and the gate's external enforcement. It complements
the 3-arm formal result (`formal-conclusions-opencode.md`) and the v2 detector
(`catalog.full.json`).

Implementation: `experiments/tasks/opencode_arms.py` defines the five arms with `skills`, `gate`
and `enforce` flags; `opencode_run.py` skips the external feedback loop when `enforce` is false;
`cost_pilot.py`, `formal_run.py`, `formal_all.py` accept the dose arms; `formal_analysis.py` adds
per-arm contrasts against baseline and `formal_report.py` renders them. The aliases `harness` and
`harness_compliance` keep the 3-arm reports reproducible.

## Question

The 3-arm run showed that `harness_compliance` reduced confirmed violations (6 â†’ 1 in the
held-out pack) while `harness` did not. That arm bundles rules, 12 pipeline skills, compliance
skills, the gate CLI and external feedback rounds. Which component carries the effect?

## Arms

| Arm | Workspace files | `.agents/skills` | Gate CLI + instruction | External feedback rounds |
|---|---|---|---|---|
| `baseline` | none | none | no | no |
| `rules` | `AGENTS.md` | none | no | no |
| `rules_skills` | `AGENTS.md` | 12 pipeline skills | no | no |
| `rules_skills_gate` | `AGENTS.md` | 12 + 3 compliance skills + pack | yes | no |
| `rules_skills_gate_enforced` | same as above | same | yes | up to 3 |

`rules_skills` is the current `harness` arm; `rules_skills_gate_enforced` is the current
`harness_compliance` arm. The two new arms are `rules` and `rules_skills_gate` (advisory gate).

## What each contrast isolates

- `rules âˆ’ baseline`: the always-on written rules alone.
- `rules_skills âˆ’ rules`: the 12 pipeline skills, with the same rules.
- `rules_skills_gate âˆ’ rules_skills`: compliance skills + gate instruction/CLI, without the
  runner forcing a correction round.
- `rules_skills_gate_enforced âˆ’ rules_skills_gate`: the external feedback rounds (enforcement).
- `rules_skills_gate_enforced âˆ’ baseline`: the full arm, for continuity with the 3-arm result.

## Outcomes

Primary: `confirmed_violation` per task-rep (hidden test fail + independent Semgrep finding).
Secondary: hidden pass, gate calls, external gate rounds, `gate_unresolved`, tokens, cycle time, and
`behavioral_failure` split into `task_completion` (404/missing endpoint), `test_artifact` (an
over-strict hidden assertion) and `privacy_behavioral` (hidden fail without Semgrep that is neither).
The detector-vs-oracle table is reported per arm. Completion is not charged to the gate: the gate is
a privacy control, not the functional acceptance test.

## Analysis

- Per-arm counts and rates; pairwise McNemar against `baseline` and against the previous arm in
  the dose; exact p-values and risk differences with confidence intervals.
- Mixed-effects logistic regression with task as a random intercept and arm as a fixed effect, as
  a secondary analysis (the number of events, not the number of runs, limits power).
- Report the incremental effect of each component; do not collapse the dose into a single win.

## Sample size and runtime

The held-out pack (T31, T33, T34, T35) produced 6 confirmed violations in 20 baseline pairs, with
compliance at 1. For 5 arms Ã— 4 tasks Ã— 5 reps = 100 runs, the baseline arm has 20 pairs; the
dose contrasts use paired subsets. A dose with 5 arms and 5 reps is about 5 hours of agent time.
If the advisory gate reproduces the enforced gate, the enforcement arm can be dropped from a
confirmatory run to save time.

## Threats to validity

- The arms are incrementally larger; tokens and context grow, so a slower arm is not a pure
  detector effect.
- The compliance skills and the gate instruction are bundled; a separate "gate CLI without the
  compliance skills" arm would isolate them further if needed.
- The traps are stochastic: T31 fired in 2/5 baseline reps in the formal and did not fire in a
  one-rep pilot. Use 5 reps and report per-task rates, not a single run.
- The model is fixed (`opencode-go/deepseek-v4.1-flash`); do not pool with Cursor.

## Implementation notes

- `experiments/tasks/opencode_arms.py`: add `skills` and `enforce` flags to `OpenCodeArm`;
  `baseline` (no files), `rules` (files only), `rules_skills`, `rules_skills_gate`,
  `rules_skills_gate_enforced`.
- `experiments/tasks/opencode_run.py`: pass `enforce` to `run_opencode`; when false, do not run
  the external feedback loop, but keep the gate CLI and the `AGENTS.md` instruction.
- `experiments/tasks/formal_analysis.py` / `formal_report.py`: add the arms to `ARMS`, report the
  pairwise dose contrasts and split behavioral failures into task completion, test artifact and
  privacy behavioral.
- The gate instruction includes a definition-of-done for the next run: implement the route described
  in `TASK.md` and run `python -m pytest tests -q`. The current run did not include this checklist;
  its T31 404s are reported as task completion, not privacy.
- Pre-register the fixed arms, tasks, reps and the primary outcome before the first run.

