# Gate calibration - v2 controls (2026-11-21)

## Question

How precise and how complete is the catalog gate on labeled cases, and does the result generalize
beyond the corpus that was written alongside the detector?

## Corpora

- **Curated, in-sample**: `harness/eval/catalog_corpus.json`, 22 cases over 7 v2 controls
  (`admin_exposure`, `api_key`, `billing_retention`, `credential_response`, `customer_hard_delete`,
  `log_pii`, `reset_token`). It was written with the detector and is a smoke test, not calibration.
- **Author-held-out (not blind)**: `harness/eval/catalog_corpus_heldout.json`, 16 cases over the
  same 7 controls, written by the same author from each control's intent with patterns the curated
  set does not use: attribute access instead of dict access, f-strings, FastAPI decorators, psycopg
  `%s` placeholders, named SQL parameters, soft delete, and a boolean API-key flag. Labels were
  assigned before running.

Each case names one control and one label. The runner measures only the named control; other
controls firing on the same code are recorded but do not count.

## Results

| Corpus | Cases | Result | Note |
|---|---|---|---|
| Curated (in-sample) | 22 | 22/22 | Not evidence of generalization |
| Author-held-out round 1 (pre-fix) | 16 | 15/16 | One false negative: `credential_password_hash` |
| Author-held-out round 1 (post-fix) | 16 | 16/16 | Regression on the same set, no longer held-out |
| Blind round 1 (sealed) | 36 | **26/36** | 8 false negatives, 2 false positives |
| Blind round 2 (sealed, post-fix) | 42 | **37/42** | 4 false negatives, 1 false positive |
| Blind round 3 (sealed, post-fix) | 38 | **25/38** | 14 false negatives, 0 false positives |

Author-held-out post-fix per-control counts and 95% Wilson intervals:

| Control | TP | FP | FN | TN | Precision [95% CI] | Recall [95% CI] |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 1 | 0 | 0 | 2 | 1.00 [0.21, 1.00] | 1.00 [0.21, 1.00] |
| `v2.api_key` | 1 | 0 | 0 | 1 | 1.00 [0.21, 1.00] | 1.00 [0.21, 1.00] |
| `v2.billing_retention` | 1 | 0 | 0 | 1 | 1.00 [0.21, 1.00] | 1.00 [0.21, 1.00] |
| `v2.credential_response` | 1 | 0 | 0 | 1 | 1.00 [0.21, 1.00] | 1.00 [0.21, 1.00] |
| `v2.customer_hard_delete` | 1 | 0 | 0 | 1 | 1.00 [0.21, 1.00] | 1.00 [0.21, 1.00] |
| `v2.log_pii` | 2 | 0 | 0 | 1 | 1.00 [0.34, 1.00] | 1.00 [0.34, 1.00] |
| `v2.reset_token` | 1 | 0 | 0 | 1 | 1.00 [0.21, 1.00] | 1.00 [0.21, 1.00] |

The interval is the point of the table: with one to three cases per control, a perfect score is
compatible with a true recall as low as 0.21.

## The false negative and its fix

The held-out case `credential_password_hash` returns
`{"password_hash": customer.password_hash}` from an account route. The gate returned no finding.

Root cause: `Catalog.is_sanitizer` matched sanitizer markers as substrings of the whole payload. The
marker `hash` appears inside the field name `password_hash`, so the payload was treated as already
sanitized. `{"password": customer.password}` fired because `password` contains no marker.

Fix: a sanitizer marker now counts only when it is applied as a call (optionally with a dotted
prefix), so `mask_rut(...)`, `_fingerprint(...)`, `hash_secret(...)` and `bcrypt.hashpw(...)` still
sanitize, while a field named `password_hash` does not. Covered by
`tests/harness/test_catalog.py::test_is_sanitizer_requires_a_call` and by the held-out regression test.

The curated corpus stayed at 22/22 after the fix, which confirms the change did not break the
existing sanitizer cases.

## Blind round 1 (sealed)

A fresh subagent with no access to the detector, the existing corpora or the gate output authored 36
cases from `harness/eval/blind/author_pack.md`: 5-6 per control, 3 violation and 2-3 clean each. The
file was sealed before the run (`cases_blind_round1.json.sha256`,
`80449e24e73397a3be957ba235001ec9fda4212879ae07c2465f2d66aae69a7d`) and run exactly once. The
protocol is in `harness/eval/blind/README.md`.

Result: **26/36**. Aggregate over the 36 cases: precision **0.867** [0.621, 0.963], recall **0.619**
[0.409, 0.792], accuracy 0.722.

| Control | TP | FP | FN | TN | Precision [95% CI] | Recall [95% CI] |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 1 | 1 | 1 | 0.67 [0.21, 0.94] | 0.67 [0.21, 0.94] |
| `v2.api_key` | 2 | 0 | 1 | 2 | 1.00 [0.34, 1.00] | 0.67 [0.21, 0.94] |
| `v2.billing_retention` | 1 | 0 | 2 | 2 | 1.00 [0.21, 1.00] | 0.33 [0.06, 0.79] |
| `v2.credential_response` | 2 | 1 | 1 | 1 | 0.67 [0.21, 0.94] | 0.67 [0.21, 0.94] |
| `v2.customer_hard_delete` | 1 | 0 | 2 | 2 | 1.00 [0.21, 1.00] | 0.33 [0.06, 0.79] |
| `v2.log_pii` | 2 | 0 | 1 | 3 | 1.00 [0.34, 1.00] | 0.67 [0.21, 0.94] |
| `v2.reset_token` | 3 | 0 | 0 | 2 | 1.00 [0.44, 1.00] | 1.00 [0.44, 1.00] |

Failure taxonomy (10 cases):

| Kind | Cases | Root cause |
|---|---|---|
| FN | `log_pii_02` | Sink name `log.info` is not in `LOG_PATTERNS` (only `logger.`, `logging.`, `print`, `console.*`) |
| FN | `admin_exposure_02` | Admin context checks the function name and decorators; an `Admin...` class name is ignored |
| FP | `admin_exposure_04` | Manual f-string masking (`***`) inside the payload is not recognised as a sanitizer |
| FN | `credential_response_03` | `private_key` is missing from the `CREDENTIAL` synonyms |
| FP | `credential_response_04` | A boolean projection (`bool(user.password_hash)`) is treated as exposing the credential |
| FN | `customer_hard_delete_02` | ORM `repo.delete(customer)` is not matched; only SQL `DELETE FROM` is |
| FN | `customer_hard_delete_03` | SQLAlchemy `delete(Customer).where(...)` is not matched |
| FN | `billing_retention_02` | SQLAlchemy `delete(Order)` is not matched |
| FN | `billing_retention_03` | `session.query(...).delete()` is not matched, and the retention constant is not resolved |
| FN | `api_key_03` | An `Authorization` header written to a log is not treated as a secret |

The 26/36 is the defensible calibration number for this detector and corpus. It is far from the
curated 22/22 precisely because the blind author used idiomatic shapes (ORM deletes, class-based
admin views, `log.info`, boolean projections) that the curated cases avoided.

## Fixes after blind round 1

All ten failures were fixed and promoted to the regression corpus:

| Case | Kind | Fix |
|---|---|---|
| `admin_exposure_04` | FP | A per-field f-string mask (`***`) counts as masked |
| `credential_response_04` | FP | `bool`/`len`/`any`/`all`, comparisons and `not` projections are derived flags, not exposures |
| `log_pii_02` | FN | `log.*` is a log sink; the match does not catch `catalog.` |
| `admin_exposure_02` | FN | Admin context includes the enclosing class name |
| `credential_response_03` | FN | `private_key` added to the `CREDENTIAL` synonyms |
| `customer_hard_delete_02` | FN | ORM `repo.delete(obj)` is matched; the argument maps to table candidates |
| `customer_hard_delete_03` | FN | SQLAlchemy `delete(Model).where(...)` is matched |
| `billing_retention_02` | FN | SQLAlchemy `delete(Model)` is matched |
| `billing_retention_03` | FN | `query(Model)...delete()` is matched and integer constants resolve the cutoff |
| `api_key_03` | FN | An `Authorization` header in a log is a secret for api-key controls |

The retention family was rewritten from a line-and-word scan to an AST pass: it recognises SQL
`DELETE FROM`, SQLAlchemy `delete(Model)`, `query(Model)...delete()` and ORM `repo.delete(obj)`,
maps model names to table candidates, and resolves numeric cutoffs including class constants
(`RETENTION_DAYS = 900`). The old shortcut that treated the word "retention" anywhere in the file as
retention-aware is gone; only a numeric cutoff at or above the policy value, or an explicit
`retention_days` field, makes a delete clean.

Regression state after the fixes: curated 22/22, author-held-out plus the ten blind cases 26/26,
full suite 408 passed. The sealed blind file was not edited and is not re-scored; the 26/36 above
remains the pre-fix measurement.

## Blind round 2 (sealed, post-fix)

A second fresh author, again with no access to the detector or the previous results, wrote 42 cases
(6 per control, 3 violation and 3 clean each) with emphasis on service classes, repository objects,
dependency injection and async handlers. The file was sealed before the run
(`cases_blind_round2.json.sha256`,
`26e7c288ba4bfb17d363423e7e76e9f746c43a92527dc4cac6f235ce8f40947f`) and run once.

Result: **37/42**. Aggregate: precision **0.944** [0.742, 0.990], recall **0.810** [0.600, 0.923],
accuracy 0.881.

| Control | TP | FP | FN | TN | Precision [95% CI] | Recall [95% CI] |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 3 | 0 | 0 | 3 | 1.00 [0.44, 1.00] | 1.00 [0.44, 1.00] |
| `v2.api_key` | 2 | 0 | 1 | 3 | 1.00 [0.34, 1.00] | 0.67 [0.21, 0.94] |
| `v2.billing_retention` | 2 | 1 | 1 | 2 | 0.67 [0.21, 0.94] | 0.67 [0.21, 0.94] |
| `v2.credential_response` | 2 | 0 | 1 | 3 | 1.00 [0.34, 1.00] | 0.67 [0.21, 0.94] |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 [0.44, 1.00] | 1.00 [0.44, 1.00] |
| `v2.log_pii` | 3 | 0 | 0 | 3 | 1.00 [0.44, 1.00] | 1.00 [0.44, 1.00] |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 [0.34, 1.00] | 0.67 [0.21, 0.94] |

The five failures are new idioms, not regressions of the round-1 cases:

| Kind | Case | Root cause |
|---|---|---|
| FN | `cred_vars_dump` | `return data` where `data = vars(user)`; the response scanner inspects dict/list/tuple/call returns, not a Name |
| FN | `billing_prune_180` | Default argument `retention_days=180`; the symbolic-retention fallback treats it as aware because the name contains `retention_days` |
| FP | `billing_delete_2190` | SQL `interval '2190 days'`; only AST `timedelta` cutoffs are parsed, so a safe interval is flagged |
| FN | `reset_token_log` | The token is logged but the reset-token control requires `token:` or `token=`; `v2.log_pii` fires instead, so the change is still blocked, by another control |
| FN | `apikey_plaintext_reveal` | Generic key `value` with `record.plaintext_secret`; no key or `sk_` pattern matches |

This is the post-fix calibration: recall improved from 0.619 to 0.810 and precision from 0.867 to
0.944, but the detector still misses object dumps, default-argument retention, SQL intervals and
credential attributes under generic keys. The reset-token log is a cross-control gap, not an open
gate: the change is blocked by `v2.log_pii`.

## Fixes after blind round 2

All five round-2 failures were fixed and promoted to the regression corpus:

| Case | Kind | Fix |
|---|---|---|
| `cred_vars_dump` | FN | `_dump_names` tracks `vars(obj)` and `obj.__dict__`; returning such a name is a dump finding |
| `billing_prune_180` | FN | Function default arguments feed the constant map, so `timedelta(days=retention_days)` resolves to 180 |
| `billing_delete_2190` | FP | SQL `interval 'N days'` and `make_interval(days => N)` are parsed as cutoffs |
| `reset_token_log` | FN | A log call whose arguments contain `token` fires the reset-token control |
| `apikey_plaintext_reveal` | FN | A response value that is a `secret` or `api_key` attribute fires the api-key control |

Regression state: curated 22/22, author-held-out plus the blind cases 31/31, full suite 408 passed.
The sealed round-2 set was not re-scored; 37/42 is the measurement **before** these five fixes. A
round 3 is required for the next number.

### The run false positive

Before round 3, the pre-commit hook flagged `print("formal run finished")` because `run` is a RUT
synonym. The fix requires a RUT-shaped value (`\d{1,2}.?\d{3}.?\d{3}-?[\dkK]`) for `run` in free
text, in both the legacy policy and the v2 family; a field named `run` still maps to RUT. Tests cover
prose (clean) and `run=12.345.678-5` (flagged).

## Blind round 3 (sealed, post-fix)

A third fresh author wrote 38 cases (5-6 per control, at least 3 violations each) using CLI and
management commands, background workers, serializers/DTOs, middleware and ORM models. The file was
sealed before the run (`cases_blind_round3.json.sha256`,
`47ab8920c7e90fed54bea5ff37ad174b42132f663817f65b305831e3152fb381`) and run once.

Result: **25/38**. Aggregate: precision **1.000** [0.676, 1.000], recall **0.364** [0.197, 0.570],
accuracy 0.632 [0.473, 0.766].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 0 | 0 | 3 | 2 | — | 0.00 |
| `v2.api_key` | 0 | 0 | 3 | 3 | — | 0.00 |
| `v2.billing_retention` | 1 | 0 | 2 | 2 | 1.00 | 0.33 |
| `v2.credential_response` | 1 | 0 | 2 | 2 | 1.00 | 0.33 |
| `v2.customer_hard_delete` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |
| `v2.log_pii` | 3 | 0 | 0 | 2 | 1.00 | 1.00 |
| `v2.reset_token` | 2 | 0 | 2 | 2 | 1.00 | 0.50 |

The 14 false negatives are framework coverage, not edge cases:

| Group | Cases | Cause |
|---|---|---|
| Django `JsonResponse` | `ae_view_addr`, `cr_view_reset_pw`, `rt_view_body`, `ak_rotate_raw` | `JsonResponse` is not in `RESPONSE_PATTERNS` |
| DRF serializer fields | `ae_ser_admin`, `cr_ser_secret` | `Meta.fields` lists are not inspected as response schemas |
| Django admin | `ae_modeladmin` | `list_display` and `search_fields` are not inspected |
| Django ORM deletes | `ch_cli_purge`, `ch_orm_manager`, `br_cli_365`, `br_worker_730` | `Model.objects.filter(...).delete()` is not mapped to a table |
| CLI stdout | `rt_cli_token`, `ak_cli_decrypt` | `self.stdout.write` is not a log sink |
| Header dict | `ak_worker_log` | `X-Api-Key` is not matched; `v2.log_pii` fires instead |

There were no false positives: the precision fixes of rounds 1 and 2 held. The detector is precise on
what it recognises and web-request-centric; it is not yet a general Django/DRF/ORM/CLI auditor.

## Fixes after blind round 3

The 14 framework false negatives were fixed and promoted to the regression corpus:

| Group | Fix |
|---|---|
| Django `JsonResponse` | added to `RESPONSE_PATTERNS` |
| DRF serializers | `Meta.fields` scanned; method fields masked with a sanitizer are skipped; derived suffixes (`_configured`, `_suffix`, `_last4`, `_preview`) ignored |
| Django admin | `list_display`, `search_fields` and `list_filter` scanned for personal fields |
| Django ORM | `Model.objects.filter(...).delete()` and `Manager.delete()` map to table candidates |
| CLI stdout | `stdout.write` and `stderr.write` are log sinks; token arguments are detected |
| Header dict | `X-Api-Key`/`Authorization` bindings passed to a log are flagged for api-key controls |
| Credential names | `temporary_password`, `temp_password`, `api_secret` and `client_secret` added to `CREDENTIAL` |

Regression state: curated 22/22, regression corpus **69/69** (31 previous + 38 round-3 cases), full
suite **423 passed**. The sealed round-3 set was not re-scored; 25/38 is the measurement **before**
these fixes. A round 4 is required for the post-fix number.

## Interpretation

- The curated 22/22 says the detector handles the cases it was built around; it does not estimate
  performance.
- The author-held-out round found one false negative that the curated set missed. The blind round
  found ten failures (8 FN, 2 FP), including common idioms: ORM deletes, class-based admin views,
  `log.info`, `private_key`, a boolean credential projection and manual f-string masking.
- The calibration now has three sealed rounds. Round 1 pre-fix: precision 0.867 [0.621, 0.963],
  recall 0.619 [0.409, 0.792]. Round 2 post-round-1: 0.944 [0.742, 0.990] / 0.810 [0.600, 0.923].
  Round 3 post-run-fix: 1.000 [0.676, 1.000] / 0.364 [0.197, 0.570]. The samples are small; report
  the intervals.
- The round-2 gaps were fixed and regression-tested. Round 3 moved the frontier to framework
  coverage: Django `JsonResponse`, DRF serializer fields, Django admin, ORM manager deletes, CLI
  stdout and header dicts. The detector was precise but web-request-centric; recall collapsed on
  those idioms. The 14 gaps were fixed after the measurement and are now regression cases; 25/38
  remains the pre-fix number until round 4.
- The false positives matter: a boolean projection, a manual f-string mask and the English word
  "run" were fixed; round 3 produced no false positives.

## Limitations

- The blind author is a fresh model with a clean context, not a human adjudicator. The labels were
  not independently reviewed, and the author is still an LLM, not a domain expert.
- Minimal snippets, 7 of 37 controls, and only the v2 families. Legacy policies (`privacy.cwe_532`,
  `privacy.api_exposure`) are outside this calibration.
- Round 3 is deliberately Django/DRF-heavy; other frameworks and ORMs are less covered.
- Round 3's post-fix result is regression-only: a fresh blind round is required to estimate it.
- The sealed blind sets are burned: after the first run, fixes cannot be measured against them. A new
  blind set is required for the next number.

## Next

1. Author a fresh blind round 4 after the framework coverage, with a human adjudicator if possible.
2. Include real code from the target app and public repositories, not only snippets.
3. Extend the calibration beyond the 7 v2 controls and the legacy policies.

## Artifacts

- `harness/eval/catalog_corpus.json`, `harness/eval/catalog_corpus_heldout.json`.
- `harness/eval/blind/README.md`, `author_pack.md`, `check_blind_set.py`,
  `cases_blind_round1.json`, `cases_blind_round2.json` and `cases_blind_round3.json` with their
  `.sha256` seals.
- `qa_reports/catalog-corpus/metrics.json`, `heldout_metrics.json`, `blind_round1_metrics.json`,
  `blind_round2_metrics.json`, `blind_round3_metrics.json`.
- `src/harness/catalog.py` (`is_sanitizer`), `tests/harness/test_catalog.py`,
  `tests/harness/test_catalog_corpus.py`.
