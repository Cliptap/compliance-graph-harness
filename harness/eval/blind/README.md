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
  `log_pii` and `reset_token` are perfect; the four false negatives were dynamic columns, ORM
  instance deletes, table resolution through helpers and parameter passthrough, plus one false
  positive from a callee name. The five cases were fixed and promoted (42/42 regression). A round 7
  is required for a post-fix number.
- Round 7: sealed, run once, 34/42, keyword-argument flows and parameters reaching responses.
  Recall 0.952 and precision 0.741: seven false positives from format labels, masked names, suffix
  helpers, credential metadata and a nested credential-shaped argument, plus one cross-module false
  negative. The seven false positives were fixed and promoted (41/42 regression); round 8 is
  required for a post-fix number.
- Round 7 closed: the imported producer name was added as a name-based cross-module rule; the sealed
  set now passes 42/42 as regression (127/127 corpus).
- Round 8: sealed, run once, 34/42, sinks inside helpers and keyword flows. The boundary cases held;
  the failures were class-state payloads, a `PlainTextResponse`, a `session=%s` label, an `IfExp`
  truncation and a keyword-only retention default. The eight cases were fixed and promoted
  (42/42 regression). A round 9 is required for a post-fix number.
- Round 9: sealed, run once, 31/42, inheritance, constant-flag branches and multi-object flows.
  Seven false positives came from walking dead branches; four false negatives came from method
  collisions, `delete(model)` parameters, `create_*` imports and a serializer call returned from
  the endpoint. Ten of the eleven were fixed and promoted (41/42 regression); the remaining FN is a
  delete inside an imported repository. Round 10 is required for a post-fix number.
- Round 10: sealed, run once, 38/42, async code, decorators and nested structures. The failures
  were a `.get('field')` projection, a truncated projection inside a comprehension, an in-memory
  `delete_older_than(365)` and a `retention_days = 730` mixin treated as a gate. All four were fixed
  and promoted; rounds 9 and 10 now pass 42/42 as regression. Round 11 is required for a post-fix
  number.
- Round 11: sealed, run once, 32/42, exception paths, framework serializers and batch exports. DRF
  `source=`/`write_only`, credential serializers, prefixed retention constants and a task returning
  a list with a secret were the gaps. All ten failing cases were fixed and promoted (42/42
  regression). Round 12 is required for a post-fix number.
- Round 12: sealed, run once, 35/42, admin inlines, nested serializers and error middleware. The
  failures were `email_domain`, a class constant alias, a nested serializer outside an admin path,
  `response.data` error payloads, `HttpResponseRedirect` and inherited `Meta.fields`. All seven were
  fixed and promoted (42/42 regression). Round 13 is required for a post-fix number.
- Round 13: sealed, run once, 28/42, management commands, signals, custom managers and async
  middleware. Global dictionaries, serializer method chains, `adelete`, custom manager deletes and
  exclusion mixins were the gaps. All fourteen failing cases were fixed and promoted (42/42
  regression). Round 14 is required for a post-fix number.
- Round 14: sealed, run once, 37/42, Django forms, GraphQL/JWT and async dependencies. The failures
  were a `FormView` rendering instance PII, a custom purge below retention with a known cutoff, a
  repository alias and GraphQL types under credential controls. All five were fixed and promoted
  (42/42 regression). Round 15 is required for a post-fix number.
- Round 15: sealed, run once, 35/42, pydantic/dataclass output models, cache and session round-trips
  and background tasks. The failures were `model_dump`/`asdict` payloads, a `response_model`, and
  values stored with `cache.set` and returned by another endpoint. All seven were fixed and promoted
  (42/42 regression), together with the round-2 false positive `cred_public_columns`. Round 16 is
  required for a post-fix number.
