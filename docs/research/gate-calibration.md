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
| Blind round 4 (sealed, post-fix) | 35 | **31/35** | 4 false negatives, 0 false positives |
| Blind round 5 (sealed) | 42 | **32/42** | 7 false negatives, 3 false positives |
| Blind round 6 (sealed, post-taint) | 42 | **37/42** | 4 false negatives, 1 false positive |
| Blind round 7 (sealed, post-taint) | 42 | **34/42** | 7 false positives, 1 false negative |
| Blind round 8 (sealed, post-taint) | 42 | **34/42** | 5 false negatives, 3 false positives |
| Blind round 9 (sealed, post-taint) | 42 | **31/42** | 4 false negatives, 7 false positives |
| Blind round 10 (sealed, post-taint) | 42 | **38/42** | 3 false negatives, 1 false positive |
| Blind round 11 (sealed, post-taint) | 42 | **32/42** | 6 false negatives, 4 false positives |
| Blind round 12 (sealed, post-taint) | 42 | **35/42** | 5 false negatives, 2 false positives |
| Blind round 13 (sealed, post-taint) | 42 | **28/42** | 10 false negatives, 4 false positives |
| Blind round 14 (sealed, post-taint) | 42 | **37/42** | 5 false negatives, 0 false positives |

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
| `v2.admin_exposure` | 0 | 0 | 3 | 2 | â€” | 0.00 |
| `v2.api_key` | 0 | 0 | 3 | 3 | â€” | 0.00 |
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

## Blind round 4 (sealed, post-fix)

A fourth fresh author wrote 35 cases (5 per control, at least 2 violations each) with Flask
blueprints, SQLAlchemy sessions, FastAPI dependency injection, GraphQL types and Celery tasks. The
file was sealed before the run (`cases_blind_round4.json.sha256`,
`6bec731128b9642bee6637faaccc48f2066cd6056e587d5d60e083605df7719a`) and run once.

Result: **31/35**. Aggregate: precision **1.000** [0.806, 1.000], recall **0.800** [0.584, 0.919],
accuracy 0.886 [0.740, 0.955].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 0 | 1 | 2 | 1.00 | 0.67 |
| `v2.api_key` | 2 | 0 | 1 | 2 | 1.00 | 0.67 |
| `v2.billing_retention` | 3 | 0 | 0 | 2 | 1.00 | 1.00 |
| `v2.credential_response` | 2 | 0 | 1 | 2 | 1.00 | 0.67 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 2 | 1.00 | 1.00 |
| `v2.log_pii` | 1 | 0 | 1 | 3 | 1.00 | 0.50 |
| `v2.reset_token` | 3 | 0 | 0 | 2 | 1.00 | 1.00 |

The four false negatives:

| Case | Cause |
|---|---|
| `r4_log_sms_phone` | `phone_number` is an identifier, not an exact synonym |
| `r4_admin_graphql_rut` | GraphQL type fields are not inspected |
| `r4_cred_graphql_api_secret` | same GraphQL type gap |
| `r4_key_graphql_log_secret` | a `secret` name in a log is not matched; `v2.log_pii` fires instead |

## Fixes after blind round 4

| Case | Fix |
|---|---|
| `r4_log_sms_phone` | fuzzy identifier matching, guarded by metadata suffixes (`_id`, `_ttl`, `_minutes`, `_fp`, `_hash`, ...) |
| GraphQL types | Strawberry `AnnAssign` fields are scanned like serializers |
| `r4_key_graphql_log_secret` | api-key log arguments with `secret`/`api_key` names are flagged; the log helpers are scoped to log sinks to avoid `Response`/`JsonResponse` false positives |

Regression state: curated 22/22, regression corpus **104/104** (69 previous + 35 round-4 cases), full
suite **427 passed**. The sealed round-4 set was not re-scored; 31/35 is the measurement **before**
these fixes. A round 5 is required for the post-fix number.

## Blind round 5 (sealed)

A fifth fresh author wrote 42 cases (6 per control) with indirect data flow: helper returns,
intermediate variables, f-strings and `%` formatting, and `try/except`. The file was sealed before the
run (`cases_blind_round5.json.sha256`,
`fdf4c861144bc12a1c1115b23cd785493d78d9984b88675495f6feb8ae207f9a`) and run once.

Result: **32/42**. Aggregate: precision **0.824** [0.590, 0.938], recall **0.667** [0.454, 0.828],
accuracy 0.762 [0.615, 0.865].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 0 | 0 | 3 | 3 | â€” | 0.00 |
| `v2.api_key` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.billing_retention` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.credential_response` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.customer_hard_delete` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.log_pii` | 2 | 2 | 1 | 1 | 0.50 | 0.67 |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |

The failures are interprocedural and prose, not new field names:

| Group | Cases | Cause |
|---|---|---|
| Helper return | `r5-log-01` | The f-string is built in a helper; the caller logs the variable |
| Admin prefix | `r5-adm-01/02/03` | The admin context is in `APIRouter(prefix='/admin')` or the path, not in the decorator/name; helpers return the value |
| Object dump | `r5-cred-01` | `dict(user.__dict__)` is not recognised by `_dump_names` |
| Intermediate token/key | `r5-rst-02`, `r5-key-03` | The token/key is put into an f-string or `%` variable and then passed to a redirect |
| Helper retention (FP) | `r5-del-06` | The cutoff comes from `_retention_cutoff()`; the helper is not resolved |
| Prose word (FP) | `r5-log-05/06` | "email" in a message ("invoice email", "with_email=%d") is matched as a value |

This is the interprocedural ceiling: pattern matching is precise on local flows and does not follow
helper returns, intermediate formatted variables or router prefixes. Prose matching also needs a
value context ("email=" with a string, not "invoice email").

## Fixes after blind round 5

Six of the ten failures were fixed and promoted to the regression corpus:

| Case | Fix |
|---|---|
| `r5-log-05/06` (FP) | prose synonyms need a value context; derived prefixes (`with_`, `has_`, `is_`) and aggregations (`sum`, `len`, `count`, `bool`, `any`, `all`) are not tainted |
| `r5-adm-01` | admin context includes the file path, not only the function/decorator/class |
| `r5-adm-03` | dict keys use the fuzzy field matcher with metadata guards |
| `r5-cred-01` | `dict(obj.__dict__)` is recognised as an attribute dump |
| `r5-del-06` | helper cutoffs and default arguments resolve to constants, but only when the cutoff feeds the delete |

Regression state: regression corpus **110/110** (104 + 6), full suite **436 passed**. The four
remaining failures are interprocedural: helper return (`r5-log-01`), helper phone (`r5-adm-02`),
formatted token/key variable (`r5-rst-02`, `r5-key-03`). The 32/42 is the pre-fix measurement; a
round 6 is required for the post-fix number.

## Interprocedural taint (after round 5)

The four remaining failures are fixed. The detector now builds a return-value summary for every
local helper, to a fixpoint, and a credential source model:

| Gap | Model |
|---|---|
| Helper return | `_function_summaries` runs each function's returns through the taint tracker and records the categories the return can carry; a call to that helper taints its target |
| Append-built payload | `payload.append(value)` and `extend`/`update` taint the container with the value's categories |
| Formatted intermediate | `env` already propagates through f-strings and `%`; the missing piece was the credential source |
| Credential source | a call taints its target when the target name, the callee name or a collection receiver (`secrets.get_active`) matches the credential synonyms |
| Truncation | a slice/index subscript (`api_key[-4:]`) counts as a mask, like `*` f-strings and `bool`/`len`/`count` calls |

Scope is intra-file: summaries are keyed by function name, parameters are not mapped, and imports
are not followed. That is deliberate: the measured failures were all same-file helpers and
source-returning calls, and a full interprocedural graph was not required to close them.

Result: **42/42** on the sealed round-5 set, with the four cases promoted to the regression corpus.
Regression state: curated 22/22, regression corpus **114/114**, full suite **443 passed**. The
32/42 remains the measurement before the taint work; a round 6 is required for the post-fix number.

## Blind round 6 (sealed, post-taint)

A sixth fresh author wrote 42 realistic modules (15–45 lines, class methods, 2–3 helper chains,
explicit-name cross-file imports). The file was sealed before the run
(`cases_blind_round6.json.sha256`, `e8b47c6ef4347fb1d1a84fb1ee5d1044b16ffd32b895695bcde41b57b9d6a40d`)
and run once.

Result: **37/42**. Aggregate: precision **0.944** [0.742, 0.990], recall **0.810** [0.600, 0.923],
accuracy 0.881 [0.750, 0.948].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.api_key` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.billing_retention` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.credential_response` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.customer_hard_delete` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.log_pii` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.reset_token` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |

The taint work holds on chains, classes and formatted intermediates: `log_pii` and `reset_token`
are perfect, and the helper-chain cases passed. The remaining failures are the documented limits
plus one false positive:

| Case | Cause |
|---|---|
| `r6-cred-04` (FP) | the callee name `_has_password` is read as a value identifier; the fuzzy matcher sees `password` in the function name |
| `r6-admin-02` | DRF view builds columns dynamically from `self.columns`; the list is never mapped to fields |
| `r6-del-03` | `session.delete(row)` on rows from `query(Customer)`; instance delete is not linked to the table |
| `r6-bill-01` | `_expired_orders(session, cutoff).delete(...)`; the table comes from a helper, and the 365-day cutoff is never resolved |
| `r6-key-03` | `key` flows through `_auth_header(key)` and `_audit_line(header)`; parameter-to-return mapping is not modeled |

## Fixes after blind round 6

The five failures were fixed and promoted to the regression corpus:

| Case | Fix |
|---|---|
| `r6-cred-04` (FP) | a call's `func` node is no longer read as a value identifier; `_has_password` stops matching `password` |
| `r6-admin-02` | literal field lists (`self.columns = [...]`) are mapped to categories and a dict comprehension keyed by the iteration variable is flagged |
| `r6-del-03` | names that hold a query result are tracked, so `session.delete(row)` resolves to the queried table |
| `r6-bill-01` | tables propagate through query helpers, so `_expired_orders(...).delete()` resolves to `orders`; an adequate helper cutoff feeding the deleted rows is still a gate |
| `r6-key-03` | parameter positions that reach a return value or a log sink are computed to a fixpoint; a call with a tainted argument at a logged position is flagged |

Regression state: sealed round-6 set **42/42**, curated 22/22, regression corpus **119/119** (114 + 5),
full suite **449 passed**. The 37/42 remains the pre-fix measurement; a round 7 is required for the
post-fix number.

## Blind round 7 (sealed, post-taint)

A seventh fresh author wrote 42 modules with keyword-argument flows, parameters that reach responses
and redirects, and explicit-name cross-file imports. The file was sealed before the run
(`cases_blind_round7.json.sha256`, `d1e568a53c033c816a55916ec7ce3046ca1ed8520fcd0ff57fc0acc5665682cd`)
and run once.

Result: **34/42**. Aggregate: precision **0.741** [0.553, 0.868], recall **0.952** [0.773, 0.992],
accuracy 0.810 [0.667, 0.900]. Recall is the best of any round; the cost was precision.

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 2 | 1 | 1 | 0.50 | 0.67 |
| `v2.api_key` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.billing_retention` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.credential_response` | 3 | 2 | 0 | 1 | 0.60 | 1.00 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.log_pii` | 3 | 2 | 0 | 1 | 0.60 | 1.00 |
| `v2.reset_token` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |

The false positives share one theme: a value that was masked, derived or unrelated got matched
through a format label, a callee argument or a fuzzy key.

| Case | Cause |
|---|---|
| `r7-log-04/06` (FP) | the format label `email=%s` / `address=%s` counted as a value even though the argument was masked |
| `r7-adm-04` (FP) | dict key `email` with a masked value passed as a parameter; the value name was not recognised as a mask |
| `r7-adm-06` (FP) | `_phone_suffix(phone=customer.phone)`; the masking call's argument leaked |
| `r7-cred-04` (FP) | `password_algorithm` and `password_changed_at` matched `password` by fuzzy substring |
| `r7-cred-05` (FP) | `User.objects.create(password=make_password(raw))`; a credential-shaped nested call tainted the returned user |
| `r7-bil-06` (FP) | the cutoff came from a constructor keyword (`Job(days=LEGAL_HOLD_DAYS)`) and was not resolved |
| `r7-adm-03` (FN) | `format_rut_and_email` is imported from another module; cross-module returns are not followed |

## Fixes after blind round 7

| Case | Fix |
|---|---|
| `r7-log-04/06` | prose synonyms no longer treat `%s`/`{}` placeholders as literal values |
| `r7-adm-04` | a value whose name carries a masking hint (`masked`, `email_masked`) is not exposed |
| `r7-adm-06` | masking calls are recognised by name suffix (`_suffix`, `_last4`, `_fp`, `_hash`) and their arguments are not read |
| `r7-cred-04` | metadata suffixes `_at`, `_algorithm`, `_status`, `_policy`, `_ref`, `_version` stop matching `password`/`secret` |
| `r7-cred-05` | credential sources follow only the call chain, not nested arguments |
| `r7-bil-06` | a constructor keyword resolved from a constant gates the retention window |
| keyword flows | parameter effects include parameter names, so keyword arguments propagate at call sites |
| receiver methods | `self`/`cls` are not treated as parameter positions |
| parameter sinks | a parameter that reaches a response or redirect inside a helper is flagged at the call site |
| `r7-adm-03` | imported producer names (`format_rut_and_email`) seed their categories from the name; maskers and senders are excluded |

Regression state: sealed round-7 set **42/42**, curated 22/22, regression corpus **127/127**
(119 + 8), full suite **463 passed**. The 34/42 remains the pre-fix measurement; a round 8 is
required for the post-fix number.

## Blind round 8 (sealed, post-taint)

An eighth fresh author wrote 42 modules that put the sink behind a function boundary: local helpers
build the response or redirect from a parameter, values cross calls by keyword, and classes carry
state across methods. The file was sealed before the run (`cases_blind_round8.json.sha256`,
`952b3b60c2e3fe055130da65b0c2314943647d063ad96eaed685b180a11843af`) and run once.

Result: **34/42**. Aggregate: precision **0.842** [0.624, 0.945], recall **0.762** [0.549, 0.894],
accuracy 0.810 [0.667, 0.900].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.api_key` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.billing_retention` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.credential_response` | 1 | 1 | 2 | 2 | 0.50 | 0.33 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.log_pii` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |

The helper-boundary emphasis worked: `log_pii`, `customer_hard_delete` and the keyword flows held.
The failures concentrated in class state and in masked arguments that still propagated.

| Case | Cause |
|---|---|
| `r8-admin-02`, `r8-cred-02`, `r8-reset-02`, `r8-apikey-02` (FN) | methods mutate `self._payload[...]` and `render` returns `JSONResponse(self._payload)`; instance state was not tracked |
| `r8-cred-03` (FN) | `PlainTextResponse` was not a response pattern; the imported name `read_private_key_pem` also failed the token check |
| `r8-log-06` (FP) | the label `session=%s` matched the credential synonym `session` |
| `r8-cred-04` (FP) | `api_key[-4:] if api_key else None` (an `IfExp`) was not recognised as a truncation |
| `r8-bill-04` (FP) | a keyword-only default (`*, days=ORDER_RETENTION_DAYS`) was not read |

## Fixes after blind round 8

| Case | Fix |
|---|---|
| class state | `self.<attr>` mutations are collected per class (`self._payload['email'] = ...`) and read back at the sink; the model is an order-insensitive union |
| `r8-cred-03` | `PlainTextResponse`, `HTMLResponse`, `HttpResponse` and `StreamingResponse` are response patterns; import-name matching also checks whole synonyms (`private_key`) |
| `r8-log-06` | `session` and `cookie` join the prose synonyms and need a literal value |
| `r8-cred-04` | an `IfExp` is masked when both branches are, and `None` counts as masked |
| `r8-bill-04` | keyword-only defaults feed the constant map |
| masked arguments | a masked argument (`Compare`, `bool`, truncation) never propagates through a parameter position, and arguments outside propagating positions are not walked |

Regression state: sealed round-8 set **42/42**, curated 22/22, regression corpus **135/135**
(127 + 8), full suite **469 passed**. The 34/42 remains the pre-fix measurement; a round 9 is
required for the post-fix number.

## Blind round 9 (sealed, post-taint)

A ninth fresh author wrote 42 modules around inheritance, decidable conditional assembly and
multi-object flows (service → DTO → serializer → presenter). The file was sealed before the run
(`cases_blind_round9.json.sha256`,
`8353f8edd5c1b122d2155af8599e74082ba21e66a3a10acba1b1c1e6cb3a2d31`) and run once.

Result: **31/42**. Aggregate: precision **0.708** [0.508, 0.851], recall **0.810** [0.600, 0.923],
accuracy 0.738 [0.589, 0.847].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.api_key` | 2 | 1 | 1 | 2 | 0.67 | 0.67 |
| `v2.billing_retention` | 2 | 1 | 1 | 2 | 0.67 | 0.67 |
| `v2.credential_response` | 3 | 2 | 0 | 1 | 0.60 | 1.00 |
| `v2.customer_hard_delete` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.log_pii` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.reset_token` | 2 | 1 | 1 | 2 | 0.67 | 0.67 |

Object-oriented structure exposed two classes of failure: dead branches behind constants were
walked anyway, and method-name collisions across a base class and its subclass lost taint.

| Case | Cause |
|---|---|
| `r9-log-05`, `r9-admin-05`, `r9-cred-05`, `r9-reset-05`, `r9-key-05` (FP) | the dead branch of a flag (`LOG_RAW = False`, `include_credentials = False`, `if not GENERIC:`) was still walked |
| `r9-cred-06` (FP) | the CamelCase constructor `SessionService()` matched the credential synonym `session` |
| `r9-bill-04` (FP) | `retention_days()` overridden in a subclass was not resolved for `timedelta(days=self.retention_days())` |
| `r9-del-01` (FN) | `delete(model)` where `model` is a helper parameter and the caller passes `Customer` |
| `r9-reset-01` (FN) | `create_reset_token` was not an import verb; the subclass `issue` lost its summary to the base `issue` |
| `r9-key-01` (FN) | the endpoint returns `serializer.to_dict()`; a helper-call return was not treated as a response payload |
| `r9-bill-03` (FN) | the delete lives in an imported repository (`delete_older_than`); no statement in the file |

## Fixes after blind round 9

| Case | Fix |
|---|---|
| dead branches | `visit_If` resolves module and class constant flags and walks only the taken branch |
| `r9-cred-06` | credential sources ignore CamelCase constructor names |
| `r9-bill-04` | methods that return an int constant feed the constant map (minimum across overrides) |
| `r9-del-01` | models passed to a helper whose parameter is used in `delete(param)` resolve to the table |
| `r9-reset-01` | `create` joins the import verbs; summaries are unioned across same-named methods so a subclass cannot erase the base taint |
| `r9-key-01` | a returned helper or serializer call with a summary is a response payload, in both families |
| key assignments | `body['api_key'] = value` taints the container from the key, unless the value is masked |
| precision | a keyword label (`api_key=...`) is not a value; only literal strings count for the key pattern |

Regression state: sealed round-9 set **41/42** (only `r9-bill-03` remains), curated 22/22, regression
corpus **145/145** (135 + 10), full suite **475 passed**. The 31/42 remains the pre-fix measurement;
a round 10 is required for the post-fix number.

## Blind round 10 (sealed, post-taint)

A tenth fresh author wrote 42 async, decorator-driven and nested-structure modules. The file was
sealed before the run (`cases_blind_round10.json.sha256`,
`dbea6ca615366141b463ba687b0d0c4856fcc9f12651f6a0faeab453e6f0dd8e`) and run once.

Result: **38/42**. Aggregate: precision **0.947** [0.754, 0.991], recall **0.857** [0.654, 0.950],
accuracy 0.905 [0.779, 0.962]. The best precision of any round so far.

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.api_key` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.billing_retention` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |
| `v2.credential_response` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.log_pii` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.reset_token` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |

Async, decorators and nested payloads held. The failures were projection and retention semantics.

| Case | Cause |
|---|---|
| `r10-log-02` (FN) | the decorator wrapper logs `body.get('address')`; a `.get('field')` projection was not a value |
| `r10-admin-04` (FP) | the list comprehension `{'rut_last4': r['rut'][-4:]}` tainted the list because the tracker's dict masking did not cover the comprehension |
| `r10-bill-01` (FN) | `repo.delete_older_than(365)` deletes in memory; no statement, no table in the call |
| `r10-bill-03` (FN) | the mixin's `retention_days = 730` (below policy) was treated as a retention gate |

## Fixes after blind round 10

| Case | Fix |
|---|---|
| `r10-log-02` | `.get('address')` and indexed projections count as field access |
| `r10-admin-04` | the tracker applies the same masked-value blocking as the sink walk, so truncated projections inside comprehensions stay clean |
| `r10-bill-01` | a `delete_*`/`purge_*` call with a cutoff below the policy is flagged when the call, function or path names the table |
| `r10-bill-03` | a retention field gates a delete only when its resolved value is at least the policy |

Regression state: sealed rounds 9 and 10 **42/42**, curated 22/22, regression corpus **150/150**
(145 + 5), full suite **481 passed**. The 38/42 remains the pre-fix measurement; a round 11 is
required for the post-fix number.

## Blind round 11 (sealed, post-taint)

An eleventh fresh author wrote 42 modules around exception paths, framework serializers and batch
exports. The file was sealed before the run (`cases_blind_round11.json.sha256`,
`149024d3b27f11e156e6c0a7fce77beb75f7cac9f009e6175600f6173fe62d95`) and run once.

Result: **32/42**. Aggregate: precision **0.789** [0.567, 0.915], recall **0.714** [0.500, 0.862],
accuracy 0.762 [0.615, 0.865].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 3 | 2 | 0 | 1 | 0.60 | 1.00 |
| `v2.api_key` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |
| `v2.billing_retention` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |
| `v2.credential_response` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.customer_hard_delete` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.log_pii` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |

DRF serializers were the weak spot: the field name alone was checked, so `source=`, `write_only`
and the credential controls were not handled.

| Case | Cause |
|---|---|
| `r11-log-04`, `r11-admin-04` (FP) | `email_masked` was not treated as a masked field name |
| `r11-admin-06` (FP) | the derived count `without_email` matched the contact synonym |
| `r11-cred-04` (FP) | a DRF `write_only=True` password field was still treated as exposed |
| `r11-custdel-02` (FN) | `self.customer_model.objects...delete()` with a dynamic model |
| `r11-bill-01`, `r11-bill-03` (FN) | prefixed retention constants (`ORDER_RETENTION_DAYS`, `ADMIN_ORDER_RETENTION_DAYS`) bypassed the field gate |
| `r11-reset-02` (FN) | a DRF serializer `token` field on a credential control |
| `r11-apikey-02` (FN) | a DRF serializer `secret` field on a credential control |
| `r11-apikey-03` (FN) | a Celery task returned a list containing `signing_secret` |

## Fixes after blind round 11

| Case | Fix |
|---|---|
| masked fields | `_masked` joins the metadata suffixes; `without_` joins the derived prefixes |
| `r11-cred-04` | serializer fields declared `write_only=True` are not exposures |
| serializer sources | a field whose `source` names a sensitive column is flagged |
| credential serializers | the credential family runs the same serializer scan on response sinks |
| `r11-custdel-02` | a `.delete()` on a dynamic `*_model.objects` chain resolves through the table token |
| `r11-bill-01/03` | retention-field matching accepts prefixed constant names and compares their values |
| `r11-apikey-03` | an endpoint or task returning a tainted name is a response |
| delete routes | decorator calls such as `@router.delete(...)` are not statements; argument-bearing `.delete(repo)` calls need an explicit table |

Regression state: sealed round-11 set **42/42**, curated 22/22, regression corpus **160/160**
(150 + 10), full suite **490 passed**. The 32/42 remains the pre-fix measurement; a round 12 is
required for the post-fix number.

## Blind round 12 (sealed, post-taint)

A twelfth fresh author wrote 42 modules around admin inlines, nested serializers and error
middleware. The file was sealed before the run (`cases_blind_round12.json.sha256`,
`880048fe2a379a5d6a30138f075bae7d7c420a98d7eabea07dcadd52d21dce26`) and run once.

Result: **35/42**. Aggregate: precision **0.889** [0.672, 0.969], recall **0.762** [0.549, 0.894],
accuracy 0.833 [0.694, 0.917].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 1 | 1 | 2 | 0.67 | 0.67 |
| `v2.api_key` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |
| `v2.billing_retention` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.credential_response` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.log_pii` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |

Admin inlines and middleware were solid. The failures were serializer inheritance, `response.data`
error payloads and a Django redirect class.

| Case | Cause |
|---|---|
| `r12-adm-02` (FP) | `email_domain` in `list_display` matched the email synonym |
| `r12-billret-06` (FP) | the class alias `required_days = TAX_RETENTION_DAYS` was not resolved |
| `r12-adm-03` (FN) | the nested serializer lived in a file without "admin" in path or class name |
| `r12-cred-05`, `r12-apikey-05` (FN) | `response.data = {...}` with a comprehension over `secret_fields` |
| `r12-restok-05` (FN) | `HttpResponseRedirect` was not a redirect pattern and `urlencode` blocked its argument |
| `r12-apikey-03` (FN) | `Meta.fields` inherited through an expression; only declared fields remained |

## Fixes after blind round 12

| Case | Fix |
|---|---|
| `r12-adm-02` | `_domain` joins the metadata suffixes |
| `r12-billret-06` | constant aliases (`required_days = TAX_RETENTION_DAYS`) resolve by fixpoint |
| `r12-adm-03` | admin serializer context also comes from an `Admin*` class in the file; declared serializer fields are scanned when `Meta.fields` is an expression |
| `r12-cred-05/05` | `response.data = ...` is a response payload in both families |
| `r12-restok-05` | `HttpResponseRedirect` is a redirect; `urlencode` passes its arguments through |
| `r12-apikey-03` | declared credential fields are scanned even when `Meta.fields` is inherited |

Regression state: sealed round-12 set **42/42**, curated 22/22, regression corpus **167/167**
(160 + 7), full suite **496 passed**. The 35/42 remains the pre-fix measurement; a round 13 is
required for the post-fix number.

## Blind round 13 (sealed, post-taint)

A thirteenth fresh author wrote 42 modules around management commands, signals, custom managers and
async middleware. The file was sealed before the run (`cases_blind_round13.json.sha256`,
`d1b3105c54aa9cb338b550060613384340e5a6d788c04b3d1d560894a0299abd`) and run once. Two controls
came with a 4/2 violation/clean split instead of 3/3; the labels are consistent, so the set was
kept as authored.

Result: **28/42**. Aggregate: precision **0.765** [0.527, 0.904], recall **0.565** [0.368, 0.744],
accuracy 0.667 [0.516, 0.790].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.api_key` | 2 | 3 | 1 | 0 | 0.40 | 0.67 |
| `v2.billing_retention` | 1 | 0 | 3 | 2 | 1.00 | 0.25 |
| `v2.credential_response` | 1 | 1 | 2 | 2 | 0.50 | 0.33 |
| `v2.customer_hard_delete` | 2 | 0 | 2 | 2 | 1.00 | 0.50 |
| `v2.log_pii` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |

The round exposed global state, serializer method chains and custom manager deletes.

| Case | Cause |
|---|---|
| `r13-key-04` (FP) | `self.stdout.write` with a masked suffix; `bool(client.api_key)` inside the argument |
| `r13-key-05` (FP) | an `IfExp` whose masked branch ended in `''` |
| `r13-cred-06`, `r13-key-06` (FP) | fields removed by `get_fields`/`to_representation` mixins were still scanned |
| `r13-admin-02` (FN) | a module-level dictionary filled in a signal |
| `r13-cred-02`, `r13-cred-03`, `r13-key-03`, `r13-reset-03` (FN) | `SerializerMethodField` chains and `.data` returns |
| `r13-del-01`, `r13-bill-06` (FN) | custom `hard_delete`/`purge_queryset` manager methods |
| `r13-del-03`, `r13-bill-03` (FN) | `adelete()` was not a delete call |
| `r13-bill-02` (FN) | `purge_batch` on an invoice queryset; the table lived in the class name |

## Fixes after blind round 13

| Case | Fix |
|---|---|
| serializer methods | a `get_*` method returning sensitive data marks the field; serializer constructors pass their payload through |
| serializer exclusions | fields removed by `get_fields`/`to_representation` (incl. `pop`) are not exposures; meta-less serializers use declared fields |
| global containers | module-level names filled inside functions taint the module env seeded into every scan |
| async deletes | `adelete`/`abulk_delete`/`hard_delete` are delete calls; class names join the table-token fallback |
| custom manager deletes | a delete/purge call with no cutoff is flagged when the retention constant in scope is below policy |
| precision | empty-string/boolean constants are masks; `_set` is metadata; `values()`/`items()` accessors carry taint; log heuristics skip nested masked calls |
| reset links | imported names containing `reset` and `link` are credential sources |

Regression state: sealed round-13 set **42/42**, curated 22/22, regression corpus **181/181**
(167 + 14), full suite **503 passed**. The 28/42 remains the pre-fix measurement; a round 14 is
required for the post-fix number.

## Blind round 14 (sealed, post-taint)

A fourteenth fresh author wrote 42 modules around Django forms, GraphQL/JWT and async dependencies.
The file was sealed before the run (`cases_blind_round14.json.sha256`,
`b3c60436f1d5735fa93cd824fdf07af19767bc8e6b624db21bb1bd72387b52b9`) and run once.

Result: **37/42**. Aggregate: precision **1.000** [0.816, 1.000], recall **0.773** [0.566, 0.899],
accuracy 0.881 [0.750, 0.948]. No false positives.

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.api_key` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.billing_retention` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.credential_response` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.customer_hard_delete` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.log_pii` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |

Forms, JWT and async dependencies held. The five false negatives were rendering, aliasing and
GraphQL under credential controls.

| Case | Cause |
|---|---|
| `r14-adm-01` | a `FormView` stores PII in `self.results` and renders it with `render_to_response` |
| `r14-del-05` | the custom purge call is below retention but a known cutoff suppressed the method rule |
| `r14-bill-05` | `repo = OrderRepository(...)`; the alias table was not resolved and `PURGE_AFTER_DAYS` was not a retention name |
| `r14-reset-03`, `r14-key-03` | GraphQL type fields under credential controls; the type scan ran only for sink exposure |

## Fixes after blind round 14

| Case | Fix |
|---|---|
| `r14-adm-01` | a class that renders a template and holds PII in instance attributes is a response |
| `r14-del-05` | the delete-method rule runs even when a local cutoff is known |
| `r14-bill-05` | `Repository`/`Manager`/`Service`/`QuerySet` class names and receiver aliases resolve to tables; `*_days` constants with retention/purge/keep semantics gate |
| `r14-reset-03`, `r14-key-03` | the credential family scans GraphQL type fields |
| precision | `purge(x)`/`hard_delete(x)` no longer treat their first argument as a model; only ORM `delete(x)` does |

Regression state: sealed round-14 set **42/42**, curated 22/22, regression corpus **186/186**
(181 + 5), full suite **508 passed**. The 37/42 remains the pre-fix measurement; a round 15 is
required for the post-fix number.

## Blind round 15 (sealed, post-taint)

A fifteenth fresh author wrote 42 modules around pydantic/dataclass output models, cache and session
round-trips and background tasks. The file was sealed before the run
(`cases_blind_round15.json.sha256`,
`bdffcacc56e88d5588b025ccbad87e8e759af1a6e8465ddb16f9a320e9f38b8b`) and run once.

Result: **35/42**. Aggregate: precision **1.000** [0.785, 1.000], recall **0.667** [0.454, 0.828],
accuracy 0.833 [0.694, 0.917]. No false positives.

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |
| `v2.api_key` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.billing_retention` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.credential_response` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.log_pii` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.reset_token` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |

Retention and background deletes held, and the async purge cases stayed precise. The seven false
negatives share one shape: the sensitive value is declared by a model class or parked in the cache,
so no single expression carries the field name.

| Case | Cause |
|---|---|
| `r15-log-01` | `model_dump()` of a pydantic model that declares `email` and `rut` |
| `r15-admin-01` | a FastAPI `response_model` with `email`/`phone`; the constructor return was not a payload |
| `r15-admin-03` | a background task stores PII in `cache.set`; another endpoint returns `cache.get` |
| `r15-cred-03`, `r15-key-03` | a dataclass `asdict` stored in the cache and read in a second endpoint |
| `r15-reset-01`, `r15-reset-03` | a pydantic/dataclass reset payload returned directly or via the cache |

## Fixes after blind round 15

| Case | Fix |
|---|---|
| `r15-log-01`, `r15-admin-01`, `r15-reset-01` | a pydantic `BaseModel`/`@dataclass` that declares a sensitive field seeds the class constructor summary; `model_dump`, `model_dump_json` and `dict` are value accessors, and `asdict`/`model_dump` are not sanitizers |
| `r15-admin-03`, `r15-cred-03`, `r15-reset-03`, `r15-key-03` | `cache.set`/`cache.get` and `request.session[...]`/`.get` propagate categories through the same key text inside the file |
| precision | `self.session = session` and a database session receiver (`self.session.execute(...)`) are not credentials; call receivers of infrastructure methods are not values. This also fixes the pre-existing round-2 false positive `cred_public_columns` |

Regression state: sealed round-15 set **42/42**, curated 22/22, regression corpus **194/194**
(186 + 8, including `cred_public_columns`), full suite **515 passed**. The 35/42 remains the
pre-fix measurement; a round 16 is required for the post-fix number.

## Blind round 16 (sealed, post-taint)

A sixteenth fresh author wrote 42 modules around indirect storage keys, cross-module producers and
model inheritance. The file was sealed before the run (`cases_blind_round16.json.sha256`,
`a0b17984ed45d9d5c4f28aa62478aa6792aad2358c4208ff2d329961ca7d35a8`) and run once.

Result: **28/42**. Aggregate: precision **0.733** [0.480, 0.891], recall **0.524** [0.324, 0.717],
accuracy 0.667 [0.516, 0.790].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 0 | 1 | 3 | 2 | 0.00 | 0.00 |
| `v2.api_key` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.billing_retention` | 1 | 1 | 2 | 2 | 0.50 | 0.33 |
| `v2.credential_response` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.customer_hard_delete` | 1 | 1 | 2 | 2 | 0.50 | 0.33 |
| `v2.log_pii` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |

The round targeted the limits left by round 15 and found them: a key written with one expression and
read with another, a subclass that inherits the sensitive field, and a wrapper model that annotates
another model.

| Case | Cause |
|---|---|
| `r16-admin-01` | `cache.set(f'admin:directory:{id}', ...)` vs `cache.get('admin:directory:' + str(id))` |
| `r16-admin-02` | `AdminUserCard(BaseUserCard)` inherits `email`; the subclass was not a model |
| `r16-admin-03` | `build_admin_export` is imported; the name does not state the payload |
| `r16-cred-02` | `ProfileEnvelope.account: AccountRecord`; the annotated wrapper was not scanned |
| `r16-del-02` | `record = session.get(ArchivedCustomer, id)` then `record.hard_delete(session)` |
| `r16-del-03` | `hard_delete_customer(...)` with no cutoff and no low retention constant |
| `r16-bill-02` | `CreditNote(Invoice)` declares `__tablename__ = 'credit_notes'` |
| `r16-bill-03` | the cutoff arrives as a keyword: `delete_orders_older_than(..., days=GRACE_DAYS)` |
| `r16-reset-02` | `ResetResult(NotifyMixin, ResetEnvelope)` inherits `token` |
| `r16-key-02` | `PartnerIntegrationView(IntegrationView)` inherits `api_secret`; list responses under the credential family |
| `r16-log-05` (FP) | `safe = contact.to_dict()` masks; `safe['email']` still matched by field name |
| `r16-admin-05` (FP) | a `model_dump` override masks with `'***' + value[-4:]`; the concatenation was not a mask |
| `r16-del-04` (FP) | eligibility is a boolean cached from `age >= RETENTION_DAYS` |
| `r16-bill-04` (FP) | the cutoff comes from a cached window: `timedelta(days=window['days'])` |

## Fixes after blind round 16

| Case | Fix |
|---|---|
| `r16-admin-01` | cache and session keys reduce to a literal namespace (`f'k:{id}'`, `'k:' + str(id)` and `'k:{}'.format(id)` all become `k:{}`); local key variables resolve |
| `r16-admin-02`, `r16-cred-02`, `r16-reset-02`, `r16-key-02` | model classes inherit fields through bases, a field annotated with another model carries its categories, and a `model_dump` that pops a field removes it |
| `r16-key-02` | list/set/generator returns are response payloads in the credential family too |
| `r16-bill-03` | keyword arguments feed the cutoff scan |
| `r16-log-05` | a subscript on a masked serializer result (`safe = contact.to_dict()`) is not matched by field name |
| `r16-admin-05` | a string concatenation containing a `***` literal is a mask |
| `r16-del-02` | `session.get(Model, id)` resolves the table, CamelCase model names resolve to table tokens, and an instance delete resolves the receiver before its arguments |
| `r16-del-03` | a hard-delete/purge call that names the table and has no cutoff is flagged unless a retention-aware check guards the function |
| `r16-del-04`, `r16-bill-04` | a guard driven by a cached eligibility flag or a cached retention window counts; `timedelta(days=window['days'])` resolves the stored constant |
| `r16-bill-02` | `__tablename__` is inherited by subclasses declared in the file |

Regression state: sealed round-16 set **41/42** (`r16-admin-03` remains), curated 22/22, regression
corpus **207/207** (194 + 13), full suite **524 passed**. The 28/42 remains the pre-fix measurement;
a round 17 is required for the post-fix number.

## Blind round 17 (sealed, post-taint)

A seventeenth fresh author wrote 42 modules around field exclusion and non-JSON response paths. The
file was sealed before the run (`cases_blind_round17.json.sha256`,
`247c6deebbe5ce7dd56fb54b1f984aa56199f95b67c83526d8d640adf63898ba`) and run once.

Result: **34/42**. Aggregate: precision **0.842** [0.624, 0.945], recall **0.762** [0.549, 0.894],
accuracy 0.810 [0.667, 0.900].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.api_key` | 2 | 1 | 1 | 2 | 0.67 | 0.67 |
| `v2.billing_retention` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.credential_response` | 2 | 1 | 1 | 2 | 0.67 | 0.67 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.log_pii` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.reset_token` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |

Exclusion is where the round found the model thin: the detector did not know that
`model_dump(exclude=...)` or `Field(exclude=True)` removes a field, and it did not treat a returned
`model_dump()` as a payload at all.

| Case | Cause |
|---|---|
| `r17-log-05` (FP) | `event.model_dump(exclude={'email', 'phone'})` logged; the receiver stayed tainted |
| `r17-cred-05` (FP) | `exclude={'password_hash', 'api_secret'}`; the excluded literals were read as values |
| `r17-cred-06` (FP) | a dict comprehension filtered by `hidden_fields` still carried the payload |
| `r17-key-04` (FP) | `api_key = ApiKey.objects.get(...)`: a record named like the secret |
| `r17-adm-03` (FN) | a CSV written with `writerow` and returned as `HttpResponse` |
| `r17-cred-01` (FN) | a returned `model_dump(exclude={'email'})` that still carries credentials |
| `r17-bill-03` (FN) | `DELETE FROM billing_invoice`: a prefixed table name |
| `r17-rst-02` (FN) | the token in `response.headers['Location']` |
| `r17-key-03` (FN) | `ORJSONResponse` was not a response pattern |

## Fixes after blind round 17

| Case | Fix |
|---|---|
| `r17-log-05`, `r17-cred-05`, `r17-cred-01` | a dump call subtracts the `exclude` categories from its receiver; a model whose sensitive fields are all `Field(exclude=True)` is a safe projection; a returned `model_dump()`/`to_dict()` is a response payload |
| `r17-cred-06` | a dict comprehension filtered against a known field list strips those fields |
| `r17-key-04` | a name assigned from a model lookup (`*.objects.get(...)`, `session.get(Model)`) is not a credential source and is not matched by its own name |
| `r17-adm-03` | a `writerow` row with PII is a response in an admin response scan |
| `r17-bill-03` | a SQL table name is split into tokens, so `billing_invoice` matches the `invoices` policy |
| `r17-rst-02` | an assignment to `response.headers['Location'/'Link']` is a redirect sink |
| `r17-key-03` | `ORJSONResponse`, `UJSONResponse` and `FileResponse` are response patterns |
| summaries | local helpers are seeded before the fixpoint, so a passthrough-named helper (`strip`) does not leak its arguments |

Regression state: sealed round-17 set **42/42**, curated 22/22, regression corpus **215/215**
(207 + 8), full suite **533 passed**. The 34/42 remains the pre-fix measurement; a round 18 is
required for the post-fix number.

## Blind round 18 (sealed, post-taint)

An eighteenth fresh author wrote 42 modules around template rendering, runtime exclusion sets and
streaming. The file was sealed before the run (`cases_blind_round18.json.sha256`,
`889717b6909c8110359fe699cb20abef22b5a630194ee2dc6d0e66bdfd98451a`) and run once.

Result: **31/42**. Aggregate: precision **0.917** [0.646, 0.985], recall **0.524** [0.324, 0.717],
accuracy 0.738 [0.589, 0.847].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |
| `v2.api_key` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |
| `v2.billing_retention` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.credential_response` | 0 | 0 | 3 | 3 | - | 0.00 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.log_pii` | 2 | 0 | 1 | 3 | 1.00 | 0.67 |
| `v2.reset_token` | 1 | 0 | 2 | 3 | 1.00 | 0.33 |

The round found the response model's blind spot: a template context, a streamed row and a returned
dict variable were not payloads. The credential control scored zero.

| Case | Cause |
|---|---|
| `r18-log-05` (FN) | `audit.warning(...)` is a named logger; only `logger.`/`log.` were sinks |
| `r18-admin-01`, `r18-cred-01`, `r18-reset-01`, `r18-key-01` (FN) | the PII or credential is in a `render`/`render_template` context |
| `r18-admin-05`, `r18-cred-05`, `r18-key-05` (FN) | rows built by iterating `EXPORT_COLUMNS` with `getattr` and streamed |
| `r18-cred-03` (FN) | a returned dict variable that received a credential key |
| `r18-reset-05` (FN) | the token in a `yield` inside a `StreamingResponse` generator |
| `r18-bill-04` (FP) | the cutoff comes through `purgeable()` → `self.cutoff()`; the transitive helper was not resolved |

## Fixes after blind round 18

| Case | Fix |
|---|---|
| `r18-log-05` | any call ending in a log level (`.info`, `.warning`, `.error`, ...) is a log sink, not only `logger.` |
| `r18-admin-01`, `r18-cred-01`, `r18-reset-01`, `r18-key-01` | `render`, `render_template`, `render_to_string` and `TemplateResponse` contexts are response payloads |
| `r18-admin-05`, `r18-cred-05`, `r18-key-05` | a row built by iterating a literal column tuple (`EXPORT_COLUMNS`) inherits its categories |
| `r18-reset-05` | a `yield` inside a function that feeds a `StreamingResponse` is a response; a dependency generator is not |
| `r18-cred-03` | a returned variable that carries categories is a response payload in the sink family |
| `r18-cred-03` (precision) | `decode`/`encode` are value accessors, so `pem.decode()` keeps the credential |
| precision | dict keys and subscript targets use exact synonyms only (`last_password_change`, `token_source` are not values) |
| `r18-bill-04` | retention-aware helpers are transitive, so `purgeable()` → `cutoff()` gates the delete |

Regression state: sealed round-18 set **42/42**, curated 22/22, regression corpus **226/226**
(215 + 11), full suite **541 passed**. The 31/42 remains the pre-fix measurement; a round 19 is
required for the post-fix number.

## Blind round 19 (sealed, post-taint)

A nineteenth fresh author wrote 42 modules around model properties, `response_model` exclusion and
signed or templated payloads. The file was sealed before the run
(`cases_blind_round19.json.sha256`,
`9aab8d64f16182513ed6e2e765fdf2ccaad95f56bfa5d6d90b346ed8b0211484`) and run once.

Result: **30/42**. Aggregate: precision **0.680** [0.484, 0.828], recall **0.810** [0.600, 0.923],
accuracy 0.714 [0.564, 0.828].

| Control | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---|---|
| `v2.admin_exposure` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |
| `v2.api_key` | 2 | 3 | 1 | 0 | 0.40 | 0.67 |
| `v2.billing_retention` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.credential_response` | 2 | 2 | 1 | 1 | 0.50 | 0.67 |
| `v2.customer_hard_delete` | 3 | 0 | 0 | 3 | 1.00 | 1.00 |
| `v2.log_pii` | 1 | 1 | 2 | 2 | 0.50 | 0.33 |
| `v2.reset_token` | 3 | 1 | 0 | 2 | 0.75 | 1.00 |

The round was a precision round: recall 0.810, but eight false positives, all from fields that
never leave the process. `response_model_exclude` and the declared `response_model` were not read.

| Case | Cause |
|---|---|
| `r19-log-01` (FN) | a `@property` returning contact data, logged as an attribute |
| `r19-log-05` (FN) | a `format_map` receipt body logged |
| `r19-cred-05`, `r19-key-05` (FN) | `Template.substitute` bodies with `signing_key`/`api_key` |
| `r19-log-06` (FP) | `email_fingerprint` was not metadata; the object's taint leaked |
| `r19-adm-04`, `r19-cred-02`, `r19-res-04`, `r19-key-04` (FP) | `response_model_exclude` was ignored |
| `r19-cred-04`, `r19-key-02`, `r19-key-06` (FP) | a payload key outside the declared `response_model` (or a metadata field) |

## Fixes after blind round 19

| Case | Fix |
|---|---|
| `r19-log-01` | a property or method name accessed as an attribute carries its return summary |
| `r19-log-05`, `r19-cred-05`, `r19-key-05` | `format_map` and `substitute` pass their arguments through |
| `r19-log-06`, `r19-key-06` | `_fingerprint` joins the metadata suffixes; a projected field only carries the base's taint when its category is in the control's set |
| `r19-adm-04`, `r19-cred-02`, `r19-res-04`, `r19-key-04` | `response_model_exclude`/`include` subtract or intersect the categories |
| `r19-cred-04`, `r19-key-02` | only keys declared by the `response_model` are exposed; the model resolves inherited and annotated fields |
| `r19-cred-05`, `r19-key-05` | `signing_key` joins the `CREDENTIAL` synonyms |
| precision | `_returns_secret_attribute` uses the field category, so `api_key_expires_at` is not a secret |

Regression state: sealed round-19 set **42/42**, curated 22/22, regression corpus **238/238**
(226 + 12), full suite **548 passed**. The 30/42 remains the pre-fix measurement; a round 20 is
required for the post-fix number.

## Interpretation

- The curated 22/22 says the detector handles the cases it was built around; it does not estimate
  performance.
- The author-held-out round found one false negative that the curated set missed. The blind round
  found ten failures (8 FN, 2 FP), including common idioms: ORM deletes, class-based admin views,
  `log.info`, `private_key`, a boolean credential projection and manual f-string masking.
- The calibration now has four sealed rounds. Round 1 pre-fix: precision 0.867 [0.621, 0.963],
  recall 0.619 [0.409, 0.792]. Round 2 post-round-1: 0.944 [0.742, 0.990] / 0.810 [0.600, 0.923].
  Round 3 post-run-fix: 1.000 [0.676, 1.000] / 0.364 [0.197, 0.570]. Round 4 post-framework:
  1.000 [0.806, 1.000] / 0.800 [0.584, 0.919]. The samples are small; report the intervals.
- The round-2 gaps were fixed and regression-tested. Round 3 moved the frontier to framework
  coverage: Django `JsonResponse`, DRF serializer fields, Django admin, ORM manager deletes, CLI
  stdout and header dicts. The detector was precise but web-request-centric; recall collapsed on
  those idioms. The 14 gaps were fixed after the measurement and are now regression cases; 25/38
  remains the pre-fix number until round 4.
- The false positives matter: a boolean projection, a manual f-string mask and the English word
  "run" were fixed; round 3 produced no false positives.
- Round 4's four gaps were fixed and are now regression cases (104/104). The 31/35 number remains
  the pre-fix measurement; only a round 5 can estimate the post-fix recall.
- Round 5 is the first interprocedural-dominated round: helper returns, intermediate f-strings and
  `%` variables, router prefixes and helper cutoffs. Local matching stays precise; compositions are
  not followed. The prose matches ("invoice email", "with_email=%d") add false positives. This is a
  design fork: extend interprocedural taint or document the ceiling.
- The cheap round-5 fixes (prose value context, admin path, dict keys, `dict(__dict__)`, helper
  cutoffs) close six failures; the remaining four were closed by local helper summaries, an
  append model and a credential source model. The sealed set now passes 42/42, but that is a
  regression number: round 5 is burned.
- The taint model is intra-file and name-based. It follows helper returns, f-strings, `%` and
  container appends inside one module; it does not follow imports, parameter-to-return mappings or
  object field sensitivity. Those limits were the hypothesis for round 6 and the round confirmed
  them.
- Round 6 confirms that surface: helper chains, classes and formatted intermediates hold
  (precision 0.944, recall 0.810), while dynamic columns, ORM instance deletes, table resolution
  through helpers and parameter-to-return flows fail. One false positive came from reading a callee
  name (`_has_password`) as a value identifier.
- The round-6 fixes close all five: callee nodes are not values, literal field lists resolve, query
  results carry their table into instance deletes, tables propagate through helpers, and
  parameter-position effects model returns and logs. The sealed set is 42/42 as regression; the
  37/42 remains the pre-fix measurement.
- Round 7 moved recall to 0.952 at the cost of precision (0.741): keyword flows work, but format
  labels, masked names and nested credential-shaped arguments produced seven false positives. The
  fixes narrow those matches and the sealed set passes 42/42 as regression, including the imported
  producer name.
- The precision lesson is consistent: the detector must distinguish *where a value is* from *a label
  that names it*. Placeholders, masked identifiers, metadata suffixes and callee arguments are not
  values.
- The cross-module fix is name-based, not dataflow: an imported producer whose name states its
  payload (`format_rut_and_email`) is trusted, while maskers and senders are excluded. A function
  that hides its payload behind a neutral name is still a false negative.
- Round 8 moved the frontier to object state: helpers that build the response internally and
  keyword flows pass, but class methods that accumulate a payload in `self._payload` require an
  instance-attribute model. The union model closes the measured cases; it is not flow-sensitive
  (an attribute assigned in a branch is treated as always tainted).
- The precision theme repeats: a format label (`session=%s`), a truncation expression and a masked
  boolean argument are labels or derived values, not exposures. Positional propagation must skip
  masked arguments.
- Round 9 added object-oriented structure. The detector now resolves constant flags before walking
  branches, unions summaries across same-named methods, follows models passed to delete helpers and
  treats a returned serializer call as a response payload. The measured set is 41/42; the remaining
  false negative is a delete that only exists in an imported repository.
- Dead-branch precision is the new lesson: a flag that is `False` at module or class level makes the
  other branch unreachable, and walking it produces false positives that look like real leaks.
- Round 10 pushed precision to 0.947 with async code, decorators and nested structures. The three
  false negatives were semantic: a `.get('field')` projection, an in-memory delete method and a
  retention field below the policy. A retention field is only a gate when its value meets the
  policy; a field named `retention_days = 730` is not a license to delete at 730 days.
- The delete-method rule is deliberately narrow: it requires a deleting verb, a cutoff below the
  policy and a table token in the call, function or path. It is the first rule that infers a hard
  delete without the statement in the file, and it stays name- and value-based, not semantic.
- Round 11 moved to framework serializers and error paths. The failures were source aliases,
  write-only fields, prefixed retention constants and a task returning a list with a secret. The
  serializer scan now reads `source` and `write_only` and runs for credential controls, not only
  admin responses.
- A retention constant is a gate only through its value: `ORDER_RETENTION_DAYS = 365` must not
  suppress a finding just because the name contains the retention field.
- Round 12 confirmed serializer inheritance as the main gap: `Meta.fields` built as an expression,
  nested serializers in files without "admin" in the path, and declared fields behind an inherited
  `Meta` all needed explicit handling. Error payloads assigned to `response.data` are responses too.
- Round 13 moved the frontier to managed state: a module-level dictionary filled in a signal, a
  serializer method that returns another serializer's data, and custom manager deletes. The
  detector now seeds a module environment, follows serializer method returns, and treats
  `adelete`/`hard_delete`/`purge_*` as deletes with the table resolved from the class or path.
- The 4/2 split in two controls is a reminder that the blind protocol fixes the per-control case
  count, not the label balance; the metrics stay per control.
- Round 14 reached precision 1.000 with forms, JWT and async dependencies. The five false negatives
  were rendering (`FormView` + `render_to_response`), repository aliases and GraphQL types under
  credential controls. The delete-method rule now runs even when a local cutoff exists, because the
  actual delete may be behind a helper.
- A class name ending in `Repository`/`Manager`/`Service`/`QuerySet` is a useful table hint, but the
  reverse must stay narrow: `purge(x)` and `hard_delete(x)` do not take a model argument; only ORM
  `delete(model)` does.
- Round 15 moved the frontier to declared output shapes and stored values. A pydantic/dataclass
  class states which fields an instance carries, so the constructor is a source; `model_dump`,
  `asdict` and `dict` pass the fields through. A cache or session write followed by a read in another
  function is linked by the key text, which is name-based like the rest of the model.
- The same round exposed a precision bug from round 2: a SQLAlchemy session attribute named
  `session` was read as a credential, and `self.session.execute(...)` tainted the row it returned.
  A call receiver is infrastructure, not a value; the name heuristic now skips it.
- Round 16 moved to indirect storage and declared shapes. The key is reduced to its literal
  namespace, so `f'k:{id}'` and `'k:' + str(id)` link; a model class inherits the fields of its
  bases and of a field's annotation; a `model_dump` that pops a field removes it. The retention
  family resolves a cached window and treats an early return driven by a retention-aware check as a
  gate.
- The round also produced four false positives, all in the "value vs label" family: a masked
  serializer result read by field name, a `***` concatenation, a boolean eligibility flag and a
  cached window. Precision is still the first casualty when the model grows.
- Round 17 moved to declared exclusion. `model_dump(exclude=...)`, `Field(exclude=True)` and a
  filtered comprehension are the same idea: the payload is a projection, not the object. The round
  also showed that a returned `model_dump()` was never a payload at all, which is why a partial
  exclusion could hide a credential.
- Two name collisions shaped the round: a record named `api_key` is not the secret, and a local
  method named `strip` is not `str.strip`. The model now distinguishes a model lookup from a
  credential source, and seeds local helpers before the summary fixpoint.
- Round 18 moved to rendered and streamed output. A template context, a row built from a column
  tuple and a `yield` inside a `StreamingResponse` generator are all response payloads; the model
  now treats them as such, and a FastAPI dependency generator is explicitly not a stream.
- The credential control scored zero in round 18 because every credential case left through a
  template or a stream. That is a useful reminder: the control was not wrong about the data, it was
  blind to the channel.
- Round 19 was a precision round: recall 0.810 but eight false positives, all fields that never
  leave the process. A `response_model` is a contract: the payload is projected onto its fields and
  `response_model_exclude` removes the rest. The detector now reads that contract, including
  inherited and annotated fields.
- The remaining false positives came from metadata names: `email_fingerprint` and
  `api_key_expires_at` look sensitive by substring but are derived. The metadata-suffix guard and a
  category-aware projection keep them out.

## Limitations

- The blind author is a fresh model with a clean context, not a human adjudicator. The labels were
  not independently reviewed, and the author is still an LLM, not a domain expert.
- Minimal snippets, 7 of 37 controls, and only the v2 families. Legacy policies (`privacy.cwe_532`,
  `privacy.api_exposure`) are outside this calibration.
- Round 3 is deliberately Django/DRF-heavy; other frameworks and ORMs are less covered.
- Round 3's post-fix result is regression-only: a fresh blind round is required to estimate it.
- Round 4's post-fix result is also regression-only; the detector now has coverage for Flask,
  SQLAlchemy, GraphQL and Celery idioms, but no fresh measurement yet.
- Round 5 is not in the regression corpus: its failures are interprocedural and require a design
  change, not a pattern fix. Six of its cases were fixed and promoted; the four interprocedural ones
  remain outside the corpus.
- The interprocedural taint is intra-file and name-based: imports, parameter-to-return mappings and
  per-field object models are not followed. A cross-file helper returning a credential is still a
  false negative candidate.
- Round 6 is burned like the previous sets. Its 37/42 is the measurement **before** the fixes; the
  five failing cases were fixed and promoted, so the sealed set now passes 42/42 as regression.
- Round 7 is burned. Its 34/42 is the measurement **before** the fixes; the eight failing cases
  were fixed and promoted.
- Round 8 is burned. Its 34/42 is the measurement **before** the fixes; the eight failing cases
  were fixed and promoted.
- The class-state model is file-local and order-insensitive: it unions `self.<attr>` assignments
  across methods and does not model branches, so it can over-approximate a conditional payload.
- Round 9 is burned. Its 31/42 is the measurement **before** the fixes; ten of the eleven failing
  cases were fixed and promoted. `r9-bill-03` was fixed later by the round-10 delete-method rule.
- Round 10 is burned. Its 38/42 is the measurement **before** the fixes; the four failing cases
  were fixed and promoted.
- Round 11 is burned. Its 32/42 is the measurement **before** the fixes; the ten failing cases
  were fixed and promoted.
- Round 12 is burned. Its 35/42 is the measurement **before** the fixes; the seven failing cases
  were fixed and promoted.
- Round 13 is burned. Its 28/42 is the measurement **before** the fixes; the fourteen failing
  cases were fixed and promoted.
- Round 14 is burned. Its 37/42 is the measurement **before** the fixes; the five failing cases
  were fixed and promoted.
- Round 15 is burned. Its 35/42 is the measurement **before** the fixes; the seven failing cases
  were fixed and promoted, together with the pre-existing round-2 false positive.
- Round 16 is burned. Its 28/42 is the measurement **before** the fixes; thirteen of the fourteen
  failing cases were fixed and promoted. `r16-admin-03` remains: the imported producer
  (`build_admin_export`) does not state its payload, so a name-based cross-module model cannot
  decide it.
- Round 17 is burned. Its 34/42 is the measurement **before** the fixes; the nine failing cases were
  fixed and promoted.
- Round 18 is burned. Its 31/42 is the measurement **before** the fixes; all eleven failing cases
  were fixed and promoted.
- The exclusion model is syntactic: it reads `exclude={...}` literals, `Field(exclude=True)` and a
  comprehension filtered against a literal field list. A dynamic exclusion computed at runtime, or a
  serializer that removes a field through a helper, is still a false positive candidate.
- Round 19 is burned. Its 30/42 is the measurement **before** the fixes; all twelve failing cases
  were fixed and promoted.
- The response-model contract is read from the decorator: the model must be declared in the same
  file. An imported `response_model` is not resolved, so its projection is unknown.
- The streaming model is structural: a `yield` counts only when the function feeds a
  `StreamingResponse`/`StreamingHttpResponse` in the same file, and a column tuple counts only when
  a row is built from it. A stream assembled in another module is still a false negative candidate.
- The cache and session model is textual: a store and a read link only when both reduce to the same
  literal namespace. A key assembled by unrelated expressions, or stored in one module and read in
  another, is still a false negative candidate.
- Parameter effects cover positional and keyword arguments and log, response and redirect sinks.
  Cross-module handling is name-based: imports whose names state their payload are trusted, the rest
  are not followed.
- The sealed blind sets are burned: after the first run, fixes cannot be measured against them. A new
  blind set is required for the next number.

## Next

1. Author a fresh blind round 20 for the post-fix number, with real code from the target app and
   public repositories, not only snippets.
2. Probe imported response models, streams assembled across modules and nested template includes.
3. Extend the calibration beyond the 7 v2 controls and the legacy policies.

## Artifacts

- `harness/eval/catalog_corpus.json`, `harness/eval/catalog_corpus_heldout.json`.
- `harness/eval/blind/README.md`, `author_pack.md`, `check_blind_set.py`,
  `cases_blind_round1.json` through `cases_blind_round19.json` with their `.sha256` seals.
- `qa_reports/catalog-corpus/metrics.json`, `heldout_metrics.json`, `blind_round1_metrics.json`
  through `blind_round19_metrics.json`.
- `src/harness/catalog.py` (`is_sanitizer`), `src/harness/policy_families.py`,
  `tests/harness/test_catalog.py`, `test_catalog_corpus.py`, `test_framework_coverage.py`.
