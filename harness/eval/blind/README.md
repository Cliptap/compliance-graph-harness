# Blind held-out round 1 - protocol

Goal: measure the catalog gate's precision and recall on cases authored **without access to the
detector**. This is the measurement the curated and post-fix corpora cannot provide.

## Roles

- **Author**: writes the cases and labels from `author_pack.md` only. Must not read `src/harness/`,
  `harness/eval/catalog_corpus*.json`, `qa_reports/catalog-corpus/`, or `tests/harness/test_catalog*`.
- **Adjudicator** (optional but recommended): a third person who reviews only the ambiguous cases,
  without seeing the arm or detector output, and records the final label.
- **Runner**: validates, seals, runs once, and reports. Does not edit cases after the seal.

## Sequence

1. Author writes `cases_blind_round1.json` from `author_pack.md`.
2. Runner validates with `check_blind_set.py` (structure, coverage, balance, valid Python).
3. Runner seals the file: `python harness/eval/blind/check_blind_set.py --seal`.
4. If an adjudicator is available, ambiguous cases are resolved **before** the run; the file is
   re-sealed after any change.
5. Run once:
   `python harness/eval/catalog_corpus.py --corpus harness/eval/blind/cases_blind_round1.json --out qa_reports/catalog-corpus/blind_round1_metrics.json`
6. No edits to the sealed file after the first run. Failures become regression cases; the next
   measurement uses a new blind set.

## Blindness rules

- The author works from the control intent, not from the implementation.
- The author does not see the curated corpus, the held-out round-1 corpus, the gate output, or the
  detector source.
- The adjudicator sees only the case code and the control definition.
- The runner does not tell the author which cases failed.

## What counts as a result

- Per control: TP, FP, FN, TN, precision and recall with 95% Wilson intervals (the runner computes
  them). With 5 cases per control, a perfect score still has a wide lower bound; report intervals.
- Failures are adjudicated: a false positive/negative is a detector finding only if the label is
  confirmed. A wrong label is an authoring defect, recorded as such.

## Status

- Round 1: sealed, run once, 26/36 pre-fix. See `docs/research/gate-calibration.md`.
- Round 2: sealed, run once, 37/42 post-round-1, focused on service/repository/async shapes.
- Round 3: sealed, run once, 25/38 post-run-fix, focused on CLI, workers, serializers and ORM
  models. The remaining gaps are framework coverage, not edge cases.
- Round 4: sealed, run once, 31/35 post-framework, focused on Flask, SQLAlchemy, FastAPI
  dependencies, GraphQL and Celery. The four gaps were fixed and are now regression cases.
- Round 5: sealed, run once, 32/42, focused on indirect data flow. Six failures were fixed and
  promoted to the regression corpus (prose value context, admin path, dict keys, `dict(__dict__)`,
  helper cutoffs); the four interprocedural cases were later closed by helper summaries, append
  taint and credential sources (42/42 regression). A round 6 is required for a post-fix number.
- Round 6: sealed, run once, 37/42, realistic modules with class methods and 2–3 helper chains.
  `log_pii` and `reset_token` are perfect; the four false negatives are dynamic columns, ORM
  instance deletes, table resolution through helpers and parameter passthrough. One false positive
  comes from a callee name read as a value. Fixes pending.
